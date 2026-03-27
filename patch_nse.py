import re

with open("backend/ingest/nse_lib.py", "r") as f:
    code = f.read()

replacement = """    def get_contract_delta(self, trade_date: date) -> pd.DataFrame:
        \"\"\"Get Contract Delta.\"\"\"
        # Archive URL: https://nsearchives.nseindia.com/archives/nsccl/delta/N_DELTA_TRD_ddmmyyyy.DAT
        # New URL: https://nsearchives.nseindia.com/archives/nsccl/delta/Contract_Delta_ddmmyyyy.csv
        date_str = trade_date.strftime("%d%m%Y")
        urls = [
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/Contract_Delta_{date_str}.csv",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/contract_delta_{date_str}.csv",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/N_DELTA_TRD_{date_str}.DAT"
        ]

        for url in urls:
            resp = self.get(url)
            if resp and resp.status_code == 200:
                try:
                    df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
                    df.columns = [str(c).strip() for c in df.columns]
                    return df
                except:
                    pass
        return pd.DataFrame()"""

# Find and replace the get_contract_delta method
start_idx = code.find("def get_contract_delta")
end_idx = code.find("def get_fii_dii_cash", start_idx)

new_code = code[:start_idx] + replacement[4:] + "\n\n    " + code[end_idx:]

with open("backend/ingest/nse_lib.py", "w") as f:
    f.write(new_code)
