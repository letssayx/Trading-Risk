import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

new_thead = """<thead id="mr-data-head">
                                <tr>
                                    <th style="text-align: left; position: sticky; top: 0; left: 0; background: #1e1e1e; z-index: 3; min-width: 90px; max-width: 90px; width: 90px;">Date</th>
                                    <th style="text-align: left; position: sticky; top: 0; left: 90px; background: #1e1e1e; z-index: 3;">Symbol</th>
                                    <th style="white-space: pre-wrap;">Close<br>Price</th>
                                    <th style="white-space: pre-wrap;">VWAP</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total Vol</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total OI</th>
                                    <th style="white-space: pre-wrap;">Put-Call<br>Ratio (OI)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (PE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(PE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (CE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(CE)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Options)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Futures)</th>
                                    <th style="white-space: pre-wrap;">Fut 1<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 2<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 3<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Call OI</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Put OI</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Next)</th>
                                    <th style="white-space: pre-wrap;">IV Rank<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">IV Percentile<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Far)</th>
                                    <th style="white-space: pre-wrap;">1-Sigma Daily<br>Volatility</th>
                                    <th style="white-space: pre-wrap;">Rollover<br>Percentage</th>
                                    <th style="white-space: pre-wrap;">MWPL %<br>(Top Client)</th>
                                    <th style="white-space: pre-wrap;">Basis 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Basis 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">P/E<br>Ratio</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">Price %<br>Change</th>
                                    <th style="white-space: pre-wrap;">Relative Vol<br>(20d)</th>
                                    <th style="white-space: pre-wrap;">14-Day<br>ATR %</th>
                                    <th style="white-space: pre-wrap;">20-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">50-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">100-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">200-Day<br>EMA</th>
                                </tr>
                            </thead>"""

start_thead = content.find('<thead id="mr-data-head">')
end_thead = content.find('</thead>', start_thead) + len('</thead>')

new_content = content[:start_thead] + new_thead + content[end_thead:]

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(new_content)
