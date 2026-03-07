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
        body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 12px; color: #333; }
        h1 { color: #1a365d; border-bottom: 2px solid #1a365d; padding-bottom: 5px; }
        h2 { color: #2b6cb0; border-bottom: 1px solid #e2e8f0; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 10px; }
        th, td { border: 1px solid #cbd5e0; padding: 6px; text-align: right; }
        th { background-color: #f7fafc; color: #4a5568; font-weight: bold; text-align: center; }
        .text-left { text-align: left; }
        .highlight-green { color: #38a169; font-weight: bold; }
        .highlight-red { color: #e53e3e; font-weight: bold; }
        .ai-inference { background-color: #ebf8ff; border-left: 4px solid #3182ce; padding: 15px; margin: 20px 0; font-style: italic; font-size: 11px; }
        .page-break { page-break-after: always; }
        .chart-container { text-align: center; margin: 20px 0; }
        .chart-container img { max-width: 100%; height: auto; }
        .section { margin-bottom: 30px; }
    </style>
</head>
<body>
    <h1>Daily Derivatives Report</h1>
    <p><strong>Date:</strong> {{ date }}</p>

    <div class="ai-inference">
        <h3>Market Inference</h3>
        <p>{{ ai_inference | replace('\n', '<br>') | safe }}</p>
    </div>

    <div class="section">
        <h2>Top 10 High Conviction Watchlist</h2>
        <table>
            <thead>
                <tr>
                    <th class="text-left">Symbol</th>
                    <th>Close</th>
                    <th>MWPL %</th>
                    <th>Basis %</th>
                    <th>Rollover %</th>
                    <th>PCR (OI)</th>
                    <th>ATM IV</th>
                    <th>25d Skew</th>
                </tr>
            </thead>
            <tbody>
                {% for row in top_10 %}
                <tr>
                    <td class="text-left"><strong>{{ row.symbol }}</strong></td>
                    <td>{{ "%.2f"|format(row.underlying_close) }}</td>
                    <td>{{ "%.1f"|format(row.mwpl_utilization_pct) }}%</td>
                    <td>{{ "%.2f"|format(row.basis_pct) }}%</td>
                    <td>{{ "%.1f"|format(row.rollover_pct) }}%</td>
                    <td>{{ "%.2f"|format(row.pcr_oi) }}</td>
                    <td>{{ "%.1f"|format(row.atm_iv * 100) }}%</td>
                    <td>{{ "%.1f"|format(row.skew_25d * 100) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="page-break"></div>

    <div class="section chart-container">
        <h2>Market Snapshot</h2>
        <img src="file://{{ chart_path }}" alt="Market Snapshot Chart">
    </div>

    <div class="page-break"></div>

    <div class="section">
        <h2>Full Market Data Dump</h2>
        <table>
            <thead>
                <tr>
                    <th class="text-left">Symbol</th>
                    <th>Close</th>
                    <th>Basis %</th>
                    <th>Rollover %</th>
                    <th>MWPL %</th>
                    <th>PCR (OI)</th>
                    <th>PCR (Vol)</th>
                    <th>ATM IV</th>
                    <th>25d Skew</th>
                </tr>
            </thead>
            <tbody>
                {% for row in all_data %}
                <tr>
                    <td class="text-left">{{ row.symbol }}</td>
                    <td>{{ "%.2f"|format(row.underlying_close) }}</td>
                    <td>{{ "%.2f"|format(row.basis_pct) }}%</td>
                    <td>{{ "%.1f"|format(row.rollover_pct) }}%</td>
                    <td>{{ "%.1f"|format(row.mwpl_utilization_pct) }}%</td>
                    <td>{{ "%.2f"|format(row.pcr_oi) }}</td>
                    <td>{{ "%.2f"|format(row.pcr_volume) }}</td>
                    <td>{{ "%.1f"|format(row.atm_iv * 100) }}%</td>
                    <td>{{ "%.1f"|format(row.skew_25d * 100) }}%</td>
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
            prompt = "Act as an institutional derivatives quant. Analyze the following Top 10 stocks based on MWPL utilization, Skew, PCR and Basis, and provide a 2 paragraph high conviction trading call summary. Focus heavily on MWPL squeeze setups.\n\nData:\n"

            for row in top_10_data:
                prompt += f"{row.symbol}: MWPL={row.mwpl_utilization_pct}%, Skew={row.skew_25d*100}%, Basis={row.basis_pct}%, PCR={row.pcr_oi}\n"

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
        """Generates a bar chart of MWPL Utilization for the top 10 stocks."""
        symbols = [r.symbol for r in top_10_data]
        mwpl = [r.mwpl_utilization_pct for r in top_10_data]

        plt.figure(figsize=(10, 6))
        plt.bar(symbols, mwpl, color='#2b6cb0')
        plt.title('Top 10 Stocks by MWPL Utilization')
        plt.xlabel('Symbol')
        plt.ylabel('MWPL Utilization (%)')
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
        ).order_by(DailyDerivativesAnalysis.mwpl_utilization_pct.desc()).all()

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
