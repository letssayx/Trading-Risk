import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from jinja2 import Environment, FileSystemLoader
try:
    from weasyprint import HTML, CSS
except ImportError:
    HTML = None
    CSS = None
    import logging
    logging.error("Weasyprint is not installed. Please run: pip install weasyprint. PDF generation will fail.")

from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import date, timedelta
import tempfile
import json
import asyncio

from backend.ingest.nse_models import (
    DailyDerivativesAnalysis, FAOParticipantOI, SymbolMaster, BhavcopyFO
)

class MorningReportGenerator:
    """Generates the institutional multi-page PDF report."""

    def __init__(self, db: Session, target_date: date):
        self.db = db
        self.target_date = target_date
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_dir = os.path.join(self.base_dir, 'templates')
        self.reports_dir = os.path.join(self.base_dir, '../../../../reports')

        os.makedirs(self.template_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        self.chart_paths = []

    def _cleanup_charts(self):
        for path in self.chart_paths:
            if os.path.exists(path):
                os.remove(path)

    async def get_ai_inference(self, quant_summary: str) -> str:
        try:
            prompt = f"""Act as an institutional derivatives quant. Review the following quantitative market read and provide a 2 paragraph high conviction executive summary. Focus heavily on FII Positioning, Volatility, and Index Action.\n\nQuantitative Read:\n{quant_summary}"""
            import httpx
            import os

            openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
            if not openrouter_api_key:
                return "AI Inference skipped: OPENROUTER_API_KEY not found."

            headers = {
                "Authorization": f"Bearer {openrouter_api_key}",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "TurtleTerminal",
            }

            payload = {
                "model": "deepseek/deepseek-r1",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }

            async with httpx.AsyncClient() as client:
                response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60.0)

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"AI API Error: {response.text}"
        except Exception as e:
            return f"Failed to generate AI inference: {str(e)}"

    def _get_quant_summary(self, records: list) -> str:
        actual_trade_date = records[0].trade_date if records else self.target_date
        # Fetch FII Data
        fii_data = self.db.query(FAOParticipantOI).filter(
            FAOParticipantOI.trade_date == actual_trade_date,
            FAOParticipantOI.client_type == 'FII'
        ).first()

        summary = ""
        if fii_data:
            idx_long = fii_data.future_index_long or 0
            idx_short = fii_data.future_index_short or 0
            idx_ratio = (idx_long / idx_short) if idx_short > 0 else 0
            summary += f"FII Index Fut Ratio: {idx_ratio:.2f} (Longs: {idx_long}, Shorts: {idx_short}).\n"

            call_net = (fii_data.option_index_call_long or 0) - (fii_data.option_index_call_short or 0)
            put_net = (fii_data.option_index_put_long or 0) - (fii_data.option_index_put_short or 0)
            summary += f"FII Index Options Net: Calls {call_net}, Puts {put_net}.\n"

        nifty_rec = next((r for r in records if r.symbol == 'NIFTY'), None)
        if nifty_rec:
            summary += f"NIFTY: PCR {nifty_rec.pcr_oi:.2f}, IV {nifty_rec.atm_iv_near*100:.1f}%, Basis {nifty_rec.basis_1_bps} bps.\n"

        bank_rec = next((r for r in records if r.symbol == 'BANKNIFTY'), None)
        if bank_rec:
            summary += f"BANKNIFTY: PCR {bank_rec.pcr_oi:.2f}, IV {bank_rec.atm_iv_near*100:.1f}%, Basis {bank_rec.basis_1_bps} bps.\n"

        return summary

    def _get_5_day_history(self, symbols: list) -> pd.DataFrame:
        dt_start = self.target_date - timedelta(days=20)

        records = self.db.query(
            DailyDerivativesAnalysis.symbol,
            DailyDerivativesAnalysis.trade_date,
            DailyDerivativesAnalysis.close_price,
            DailyDerivativesAnalysis.futures_total_oi,
            DailyDerivativesAnalysis.chg_oi_options,
            DailyDerivativesAnalysis.chg_oi_futures
        ).filter(
            DailyDerivativesAnalysis.symbol.in_(symbols),
            DailyDerivativesAnalysis.trade_date >= dt_start,
            DailyDerivativesAnalysis.trade_date <= self.target_date
        ).order_by(
            DailyDerivativesAnalysis.symbol,
            DailyDerivativesAnalysis.trade_date.desc()
        ).all()

        # Convert ORM result objects to dictionary/tuple for pandas safely
        res = [tuple(r) for r in records]
        df = pd.DataFrame(res, columns=['symbol', 'trade_date', 'close_price', 'futures_total_oi', 'chg_oi_options', 'chg_oi_futures'])

        # Keep top 5 dates per symbol
        df = df.sort_values(['symbol', 'trade_date'], ascending=[True, False])
        df = df.groupby('symbol').head(5).reset_index(drop=True)
        # Sort chronologically for charting
        df = df.sort_values(['symbol', 'trade_date'], ascending=[True, True])
        return df

    def _generate_bar_chart(self, title, df_hist, symbol, y_col, color):
        sym_df = df_hist[df_hist['symbol'] == symbol].copy()
        if sym_df.empty: return None

        plt.figure(figsize=(4, 2.5))
        dates = sym_df['trade_date'].astype(str).str[5:] # MM-DD
        vals = sym_df[y_col]

        # Use an array of colors to dynamically color positive/negative values
        colors = ['#38a169' if v >= 0 else '#e53e3e' for v in vals]

        plt.bar(dates, vals, color=colors)
        plt.title(f"{symbol} - {title}", fontsize=9)
        plt.xticks(rotation=45, fontsize=7)
        plt.yticks(fontsize=7)

        # Turn off scientific notation
        plt.ticklabel_format(style='plain', axis='y')

        plt.tight_layout()

        fd, path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        plt.savefig(path, dpi=100)
        plt.close()
        self.chart_paths.append(path)
        return path

    async def generate_report(self) -> str:
        # 1. Fetch main data
        records = self.db.query(DailyDerivativesAnalysis).filter(
            DailyDerivativesAnalysis.trade_date == self.target_date
        ).all()

        actual_trade_date = self.target_date
        date_fallback_note = ""

        if not records:
            # Fallback to the last available trade date
            from sqlalchemy import desc
            latest_record = self.db.query(DailyDerivativesAnalysis).filter(
                DailyDerivativesAnalysis.trade_date <= self.target_date
            ).order_by(desc(DailyDerivativesAnalysis.trade_date)).first()

            if not latest_record:
                raise ValueError(f"No DailyDerivativesAnalysis data found for {self.target_date} or earlier.")

            actual_trade_date = latest_record.trade_date
            date_fallback_note = f"Note: No data available for {self.target_date.strftime('%Y-%m-%d')}. Using last available data from {actual_trade_date.strftime('%Y-%m-%d')}."

            records = self.db.query(DailyDerivativesAnalysis).filter(
                DailyDerivativesAnalysis.trade_date == actual_trade_date
            ).all()

        # Fetch overlapping data from persistent tables
        from backend.ingest.nse_models import OiAnalysisMetrics, VolatilityAnalysisMetrics
        oi_records = {r.symbol: r for r in self.db.query(OiAnalysisMetrics).filter(OiAnalysisMetrics.trade_date == actual_trade_date).all()}
        vol_records = {r.symbol: r for r in self.db.query(VolatilityAnalysisMetrics).filter(VolatilityAnalysisMetrics.trade_date == actual_trade_date).all()}

        # Symbol Mapping for Sectors
        sym_master = self.db.query(SymbolMaster).all()
        sector_map = {s.symbol: s.sector_index for s in sym_master}
        for r in records:
            r.sector = sector_map.get(r.symbol, 'Unknown')

        record_dicts = []
        for r in records:
            d = dict(r.__dict__)
            sym = d['symbol']
            if sym in oi_records:
                oi = oi_records[sym]
                d['chg_oi_fut_pct'] = oi.fut_oi_chg_pct
                d['chg_oi_futures'] = oi.fut_oi - (oi.fut_oi / (1 + (oi.fut_oi_chg_pct / 100.0))) if oi.fut_oi and oi.fut_oi_chg_pct else 0

                chg_oi_ce = oi.call_oi - (oi.call_oi / (1 + (oi.call_oi_chg_pct / 100.0))) if oi.call_oi and oi.call_oi_chg_pct else 0
                chg_oi_pe = oi.put_oi - (oi.put_oi / (1 + (oi.put_oi_chg_pct / 100.0))) if oi.put_oi and oi.put_oi_chg_pct else 0
                d['chg_oi_options'] = chg_oi_ce + chg_oi_pe

            if sym in vol_records:
                vol = vol_records[sym]
                d['ivr'] = vol.ivr or 0
                d['ivp'] = vol.ivp or 0

            # Row-by-row AI/Quant Inferences
            price_chg = d.get('price_pct_change') or 0
            oi_chg_pct = d.get('chg_oi_fut_pct') or 0
            pcr = d.get('pcr_oi') or 0
            basis = d.get('basis_1_bps') or 0

            insights = []
            if price_chg > 0.5 and oi_chg_pct > 2:
                insights.append("Long Buildup.")
            elif price_chg < -0.5 and oi_chg_pct > 2:
                insights.append("Short Buildup.")
            elif price_chg > 0.5 and oi_chg_pct < -2:
                insights.append("Short Covering.")
            elif price_chg < -0.5 and oi_chg_pct < -2:
                insights.append("Long Unwinding.")
            else:
                insights.append("Neutral.")

            if pcr > 1.3:
                insights.append("Overbought PCR.")
            elif pcr > 0 and pcr < 0.6:
                insights.append("Oversold PCR.")

            if basis < -15:
                insights.append("Discounted Basis.")
            elif basis > 40:
                insights.append("High Premium.")

            d['quant_insight'] = " ".join(insights)
            record_dicts.append(d)

        df = pd.DataFrame(record_dicts)

        # 2. Exec Summary
        quant_summary = self._get_quant_summary(records)
        ai_inference = await self.get_ai_inference(quant_summary)

        # 3. Top 5 Longs/Shorts (Based on OI % Chg and Price Dir)
        # Calculate derived metrics safely
        def calc_oi_pct(row):
            try:
                oi_chg = float(row.get('chg_oi_futures', 0))
                total_oi = float(row.get('futures_total_oi', 0))
                if total_oi - oi_chg == 0: return 0.0
                return (oi_chg / (total_oi - oi_chg)) * 100.0
            except:
                return 0.0

        def calc_price_pct(row):
            # Fallback if price_pct_change isn't dynamically populated
            try:
                return float(row.get('price_pct_change', 0))
            except:
                return 0.0

        if 'chg_oi_fut_pct' in df.columns:
            df['oi_chg_pct'] = pd.to_numeric(df['chg_oi_fut_pct'], errors='coerce').fillna(0)
        else:
            df['oi_chg_pct'] = df.apply(calc_oi_pct, axis=1)

        if 'price_pct_change' in df.columns:
            df['price_chg'] = pd.to_numeric(df['price_pct_change'], errors='coerce').fillna(0)
        else:
            df['price_chg'] = df.apply(calc_price_pct, axis=1)

        longs = df[(df['oi_chg_pct'] > 0) & (df['price_chg'] > 0)].sort_values('oi_chg_pct', ascending=False).head(5)
        shorts = df[(df['oi_chg_pct'] > 0) & (df['price_chg'] < 0)].sort_values('oi_chg_pct', ascending=False).head(5)

        ce_writers = df.sort_values('chg_oi_options', ascending=False).head(5) # Approximation since raw ce missing
        pe_writers = df.sort_values('chg_oi_options', ascending=False).head(5)

        sym_to_fetch = list(set(longs['symbol'].tolist() + shorts['symbol'].tolist() +
                               ce_writers['symbol'].tolist() + pe_writers['symbol'].tolist()))

        hist_df = self._get_5_day_history(sym_to_fetch)

        long_charts = [{'symbol': s, 'path': self._generate_bar_chart('OI Buildup (Long)', hist_df, s, 'futures_total_oi', '#38a169')} for s in longs['symbol']]
        short_charts = [{'symbol': s, 'path': self._generate_bar_chart('OI Buildup (Short)', hist_df, s, 'futures_total_oi', '#e53e3e')} for s in shorts['symbol']]
        ce_charts = [{'symbol': s, 'path': self._generate_bar_chart('CE Writing', hist_df, s, 'chg_oi_options', '#e53e3e')} for s in ce_writers['symbol']]
        pe_charts = [{'symbol': s, 'path': self._generate_bar_chart('PE Writing', hist_df, s, 'chg_oi_options', '#38a169')} for s in pe_writers['symbol']]

        # 4. Expiry Analysis (Check if target_date is near expiry)
        near_expiry = next((r.near_expiry_date for r in records if r.symbol == 'NIFTY' and r.near_expiry_date), None)
        is_expiry_eve = False
        expiry_eve_data = {}
        if near_expiry:
            days_to_exp = (near_expiry - self.target_date).days
            if days_to_exp <= 1:
                is_expiry_eve = True
                # Simple logic for ATM/Max pain estimation
                idx_records = [r for r in records if r.symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']]
                for r in idx_records:
                    atm = round(r.close_price / 50) * 50 if r.close_price else 0
                    straddle = r.atm_straddle_near_month or 0
                    expiry_eve_data[r.symbol] = {
                        'atm': atm,
                        'straddle': straddle,
                        'upper_bound': atm + straddle,
                        'lower_bound': atm - straddle
                    }

        # 5. Render
        env = Environment(loader=FileSystemLoader(self.template_dir))
        template = env.get_template('report_template.html')

        html_content = template.render(
            date=self.target_date.strftime("%Y-%m-%d"),
            date_fallback_note=date_fallback_note,
            quant_summary=quant_summary,
            ai_inference=ai_inference,
            long_charts=long_charts,
            short_charts=short_charts,
            ce_charts=ce_charts,
            pe_charts=pe_charts,
            is_expiry_eve=is_expiry_eve,
            expiry_eve_data=expiry_eve_data,
            all_data=record_dicts
        )

        filename = f"Morning_Report_{self.target_date.strftime('%Y-%m-%d')}.pdf"
        output_path = os.path.join(self.reports_dir, filename)

        try:
            if HTML is None:
                raise ImportError("Weasyprint is missing. Please run 'pip install weasyprint' (and ensure Pango/Cairo C-libraries are installed on your OS) to generate PDF reports.")
            HTML(string=html_content, base_url=self.base_dir).write_pdf(output_path)
        finally:
            self._cleanup_charts()

        return output_path
