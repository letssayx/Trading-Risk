import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from sqlalchemy.orm import Session
from datetime import date
import tempfile
import json
import asyncio

from backend.ingest.nse_models import DailyDerivativesAnalysis

class MorningReportGenerator:
    """Generates the PDF report and handles AI inference using DeepSeek."""

    def __init__(self, db: Session, target_date: date):
        self.db = db
        self.target_date = target_date
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_dir = os.path.join(self.base_dir, 'templates')
        self.reports_dir = os.path.join(self.base_dir, '../../../../reports')

        os.makedirs(self.template_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        self.setup_templates()

    def setup_templates(self):
        """Creates the HTML template if it doesn't exist."""
        template_path = os.path.join(self.template_dir, 'report_template.html')
        if not os.path.exists(template_path):
            with open(template_path, 'w') as f:
                f.write("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Morning Derivatives Report - {{ date }}</title>
    <style>
        @page { size: A4 landscape; margin: 1cm; }
        body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 10px; color: #333; }
        h1 { color: #1a365d; border-bottom: 2px solid #1a365d; padding-bottom: 5px; font-size: 18px; }
        h2 { color: #2b6cb0; border-bottom: 1px solid #e2e8f0; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 9px; }
        th, td { border: 1px solid #cbd5e0; padding: 4px; text-align: right; }
        th { background-color: #f7fafc; color: #4a5568; font-weight: bold; text-align: center; }
        .text-left { text-align: left; }
        .highlight-green { color: #38a169; font-weight: bold; }
        .highlight-red { color: #e53e3e; font-weight: bold; }
        .ai-inference { background-color: #ebf8ff; border-left: 4px solid #3182ce; padding: 15px; margin: 20px 0; font-style: italic; font-size: 11px; }
        .page-break { page-break-after: always; }
        .chart-container { text-align: center; margin: 20px 0; }
        .chart-container img { max-width: 80%; height: auto; }
        .section { margin-bottom: 30px; }
    </style>
</head>
<body>
    <h1>Daily Derivatives Report - Institutional Matrix</h1>
    <p><strong>Date:</strong> {{ date }}</p>

    <div class="ai-inference">
        <h3>Market Inference</h3>
        <p>{{ ai_inference | replace('\n', '<br>') | safe }}</p>
    </div>

    <div class="section">
        <h2>Top 10 High Conviction Watchlist (by Highest ATM IV)</h2>
        <table>
            <thead>
                <tr>
                    <th class="text-left">Symbol</th>
                    <th>Near Fut Close</th>
                    <th>EQ Close</th>
                    <th>Basis 1 (bps)</th>
                    <th>Rollover %</th>
                    <th>MWPL (Top) %</th>
                    <th>PCR (OI)</th>
                    <th>ATM IV (Near)</th>
                    <th>25d Skew (Near)</th>
                    <th>Beta (252)</th>
                    <th>ATR (14)</th>
                    <th>1-Sig Vol</th>
                    <th>Z-Score</th>
                </tr>
            </thead>
            <tbody>
                {% for row in top_10 %}
                <tr>
                    <td class="text-left"><strong>{{ row.symbol }}</strong></td>
                    <td>{{ "%.2f"|format(row.close_price or 0) }}</td>
                    <td>{{ "%.2f"|format(row.eq_close_price or 0) }}</td>
                    <td>{{ "%.0f"|format(row.basis_1_bps or 0) }}</td>
                    <td>{{ "%.1f"|format(row.rollover_pct or 0) }}%</td>
                    <td>
                        {% if row.mwpl_array and row.mwpl_array|length > 0 %}
                            {% set first_key = row.mwpl_array[0].keys()|list|first %}
                            {{ "%.1f"|format(row.mwpl_array[0][first_key] or 0) }}%
                        {% else %}
                            0.0%
                        {% endif %}
                    </td>
                    <td>{{ "%.2f"|format(row.pcr_oi or 0) }}</td>
                    <td>{{ "%.1f"|format((row.atm_iv_near or 0) * 100) }}%</td>
                    <td>{{ "%.1f"|format((row.skew_25d_near or 0) * 100) }}%</td>
                    <td>{{ "%.2f"|format(row.beta_252 or 0) }}</td>
                    <td>{{ "%.2f"|format(row.atr_14_cash or 0) }}</td>
                    <td>{{ "%.1f"|format((row.daily_volatility or 0) * 100) }}%</td>
                    <td>{{ "%.2f"|format(row.z_score or 0) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="page-break"></div>

    <div class="section chart-container">
        <h2>Market Snapshot - IV Profile</h2>
        <img src="file://{{ chart_path }}" alt="Market Snapshot Chart">
    </div>

    <div class="page-break"></div>

    <div class="section">
        <h2>Full Market Data Dump</h2>
        <table>
            <thead>
                <tr>
                    <th class="text-left">Symbol</th>
                    <th>Near Fut Close</th>
                    <th>EQ Close</th>
                    <th>Total Vol</th>
                    <th>Total OI</th>
                    <th>PCR (OI)</th>
                    <th>HI OI PE Value</th>
                    <th>HI OI CE Value</th>
                    <th>ATM Straddle</th>
                    <th>Basis 1 (bps)</th>
                    <th>MWPL (Top) %</th>
                    <th>ATM IV (Near)</th>
                    <th>25d Skew (Near)</th>
                    <th>Roll %</th>
                    <th>1-Sig Vol</th>
                    <th>Z-Score</th>
                    <th>Beta (252)</th>
                    <th>Del Vol 5d</th>
                    <th>EMA 50</th>
                </tr>
            </thead>
            <tbody>
                {% for row in all_data %}
                <tr>
                    <td class="text-left">{{ row.symbol }}</td>
                    <td>{{ "%.2f"|format(row.close_price or 0) }}</td>
                    <td>{{ "%.2f"|format(row.eq_close_price or 0) }}</td>
                    <td>{{ "{:,.0f}".format(row.futures_total_vol or 0) }}</td>
                    <td>{{ "{:,.0f}".format(row.futures_total_oi or 0) }}</td>
                    <td>{{ "%.2f"|format(row.pcr_oi or 0) }}</td>
                    <td>{{ "%.2f"|format(row.highest_oi_pe_value or 0) }}</td>
                    <td>{{ "%.2f"|format(row.highest_oi_ce_value or 0) }}</td>
                    <td>{{ "%.2f"|format(row.atm_straddle_near_month or 0) }}</td>
                    <td>{{ "%.0f"|format(row.basis_1_bps or 0) }}</td>
                    <td>
                        {% if row.mwpl_array and row.mwpl_array|length > 0 %}
                            {% set first_key = row.mwpl_array[0].keys()|list|first %}
                            {{ "%.1f"|format(row.mwpl_array[0][first_key] or 0) }}%
                        {% else %}
                            0.0%
                        {% endif %}
                    </td>
                    <td>{{ "%.1f"|format((row.atm_iv_near or 0) * 100) }}%</td>
                    <td>{{ "%.1f"|format((row.skew_25d_near or 0) * 100) }}%</td>
                    <td>{{ "%.1f"|format(row.rollover_pct or 0) }}%</td>
                    <td>{{ "%.1f"|format((row.daily_volatility or 0) * 100) }}%</td>
                    <td>{{ "%.2f"|format(row.z_score or 0) }}</td>
                    <td>{{ "%.2f"|format(row.beta_252 or 0) }}</td>
                    <td>{{ "%.1f"|format(row.mavg_delivery_vol_5d or 0) }}%</td>
                    <td>{{ "%.2f"|format(row.ema_50_cash or 0) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
""")

    async def get_ai_inference(self, top_10_data: list) -> str:
        """Calls DeepSeek to generate a summary inference based on the data."""
        # Note: Since the real DeepSeek call might require environment variables we don't have,
        # we will use a dummy prompt here. In real scenario, it integrates via OpenRouter.
        try:
            prompt = "Act as an institutional derivatives quant. Analyze the following Top 10 stocks based on IV, Skew, PCR and Basis, and provide a 2 paragraph high conviction trading call summary. Focus heavily on Volatility and Skew setups.\n\nData:\n"

            for row in top_10_data:
                mwpl_str = "0"
                if row.mwpl_array and len(row.mwpl_array) > 0:
                    first_key = list(row.mwpl_array[0].keys())[0]
                    mwpl_str = str(row.mwpl_array[0][first_key])
                prompt += f"{row.symbol}: ATM IV={row.atm_iv_near*100 if row.atm_iv_near else 0}%, Skew Near={row.skew_25d_near*100 if row.skew_25d_near else 0}%, Basis BPS={row.basis_1_bps}, PCR={row.pcr_oi}, MWPL={mwpl_str}%\n"

            # Using OpenRouter DeepSeek (we'll implement the actual API call logic using litellm or httpx if needed)
            import httpx
            import os

            openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
            if not openrouter_api_key:
                return "AI Inference skipped: OPENROUTER_API_KEY not found. Please review the Top 10 tables manually."

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

    def generate_chart(self, top_10_data: list) -> str:
        """Generates a bar chart of ATM IV for the top 10 stocks."""
        symbols = [r.symbol for r in top_10_data]
        ivs = [(r.atm_iv_near * 100) if r.atm_iv_near else 0 for r in top_10_data]

        plt.figure(figsize=(10, 6))
        plt.bar(symbols, ivs, color='#e53e3e')
        plt.title('Top 10 Stocks by ATM IV (Near)')
        plt.xlabel('Symbol')
        plt.ylabel('ATM IV (%)')
        plt.xticks(rotation=45)
        plt.tight_layout()

        chart_path = os.path.join(self.reports_dir, f'chart_{self.target_date.strftime("%Y-%m-%d")}.png')
        plt.savefig(chart_path)
        plt.close()

        return os.path.abspath(chart_path)

    async def generate_report(self) -> str:
        """Generates the PDF report using Jinja2 and WeasyPrint."""

        # 1. Fetch data
        records = self.db.query(DailyDerivativesAnalysis).filter(
            DailyDerivativesAnalysis.trade_date == self.target_date
        ).order_by(DailyDerivativesAnalysis.atm_iv_near.desc().nulls_last()).all()

        if not records:
            raise ValueError(f"No DailyDerivativesAnalysis data found for {self.target_date}")

        top_10 = records[:10]

        # 2. Generate AI Inference
        ai_inference = await self.get_ai_inference(top_10)

        # 3. Generate Chart
        chart_path = self.generate_chart(top_10)

        # 4. Render HTML
        env = Environment(loader=FileSystemLoader(self.template_dir))
        template = env.get_template('report_template.html')

        html_content = template.render(
            date=self.target_date.strftime("%Y-%m-%d"),
            ai_inference=ai_inference,
            top_10=top_10,
            all_data=records,
            chart_path=chart_path
        )

        # 4. Convert to PDF
        filename = f"Morning_Report_{self.target_date.strftime('%Y-%m-%d')}.pdf"
        output_path = os.path.join(self.reports_dir, filename)

        HTML(string=html_content).write_pdf(output_path)

        return output_path
