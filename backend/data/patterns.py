from datetime import datetime, date

class DatePatternManager:
    """
    Manages NSE Filename Patterns.
    """

    @staticmethod
    def get_url(file_type: str, target_date: date) -> str:
        # Formats
        ddMMyyyy = target_date.strftime("%d%m%Y")
        ddMMMyyyy = target_date.strftime("%d%b%Y").upper() # 27OCT2023
        MMyyyy = target_date.strftime("%b%Y").upper() # OCT2023
        yyyy = target_date.strftime("%Y")

        patterns = {
            "MTO": f"https://archives.nseindia.com/archives/equities/mto/MTO_{ddMMyyyy}.DAT",
            "BHAVCOPY_FO": f"https://archives.nseindia.com/content/historical/DERIVATIVES/{yyyy}/{MMyyyy}/fo{ddMMMyyyy}bhav.csv.zip",
            "PARTICIPANT_OI": f"https://archives.nseindia.com/content/nsccl/fao_participant_oi_{ddMMyyyy}.csv",
            "BULK_DEALS": f"https://archives.nseindia.com/content/equities/bulk.csv", # Usually live, archives differ
            # ... Add other 8 patterns
        }

        return patterns.get(file_type, "")
