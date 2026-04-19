import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
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
        # Fetch FII Data
        fii_data = self.db.query(FAOParticipantOI).filter(
            FAOParticipantOI.trade_date == self.target_date,
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
        query = text("""
            SELECT symbol, trade_date, close_price, futures_total_oi,
                   chg_oi_options, chg_oi_futures
            FROM daily_derivatives_analysis
            WHERE symbol IN :syms AND trade_date <= :dt
            ORDER BY symbol, trade_date DESC
        """)
        # We need roughly 5 trading days. Limit won't work well with IN clause across symbols in raw SQL easily.
        # Fetch last 15 days of data for the symbols and filter in pandas.
        dt_start = self.target_date - timedelta(days=20)
        res = self.db.execute(query, {"syms": tuple(symbols), "dt": self.target_date}).fetchall()
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

        plt.bar(dates, vals, color=color)
        plt.title(f"{symbol} - {title}", fontsize=9)
        plt.xticks(rotation=45, fontsize=7)
        plt.yticks(fontsize=7)
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

        if not records:
            raise ValueError(f"No DailyDerivativesAnalysis data found for {self.target_date}")

        # Symbol Mapping for Sectors
        sym_master = self.db.query(SymbolMaster).all()
        sector_map = {s.symbol: s.sector_index for s in sym_master}
        for r in records:
            r.sector = sector_map.get(r.symbol, 'Unknown')

        df = pd.DataFrame([r.__dict__ for r in records])

        # 2. Exec Summary
        quant_summary = self._get_quant_summary(records)
        ai_inference = await self.get_ai_inference(quant_summary)

        # 3. Top 5 Longs/Shorts (Based on OI % Chg and Price Dir)
        df['oi_chg_pct'] = pd.to_numeric(df['chg_oi_fut_pct'], errors='coerce').fillna(0)
        df['price_chg'] = pd.to_numeric(df['price_pct_change'], errors='coerce').fillna(0)

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
            quant_summary=quant_summary,
            ai_inference=ai_inference,
            long_charts=long_charts,
            short_charts=short_charts,
            ce_charts=ce_charts,
            pe_charts=pe_charts,
            is_expiry_eve=is_expiry_eve,
            expiry_eve_data=expiry_eve_data,
            all_data=records
        )

        filename = f"Morning_Report_{self.target_date.strftime('%Y-%m-%d')}.pdf"
        output_path = os.path.join(self.reports_dir, filename)

        try:
            HTML(string=html_content, base_url=self.base_dir).write_pdf(output_path)
        finally:
            self._cleanup_charts()

        return output_path
