from typing import Dict, Any, List, Optional
import pandas as pd
import logging
from datetime import date
from backend.ingest.date_utils import parse_nse_date, parse_nse_datetime
import re

logger = logging.getLogger(__name__)

class FieldMapper:
    """Maps all NSE file formats to database fields"""

    # Mapping for FII Stats (special handling due to multi-row format)
    FII_STATS_INSTRUMENTS = [
        'INDEX FUTURES', 'BANKNIFTY FUTURES', 'FINNIFTY FUTURES',
        'MIDCPNIFTY FUTURES', 'NIFTY FUTURES', 'NIFTYNXT50 FUTURES',
        'INDEX OPTIONS', 'BANKNIFTY OPTIONS', 'FINNIFTY OPTIONS',
        'MIDCPNIFTY OPTIONS', 'NIFTY OPTIONS', 'NIFTYNXT50 OPTIONS',
        'STOCK FUTURES', 'STOCK OPTIONS'
    ]

    @classmethod
    def detect_format(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect file format and return metadata"""
        columns = set(df.columns)

        # Normalize columns for case-insensitive and whitespace-insensitive matching
        columns_map = {str(c).strip().upper(): c for c in columns}
        upper_cols = set(columns_map.keys())

        # UDIFF Detection - Check Sgmt first if available
        if 'SGMT' in upper_cols:
            try:
                # Check first value in Sgmt column
                sgmt_col = columns_map['SGMT']
                first_val = str(df[sgmt_col].iloc[0]).strip().upper() if len(df) > 0 else ''
                if first_val == 'CM':
                    return {'type': 'cm_udiff', 'name': 'bhavcopy_eq'}
                elif first_val == 'FO':
                    return {'type': 'fo_udiff', 'name': 'bhavcopy_fo'}
            except:
                pass

        # UDIFF FO bhavcopy (New Format) - Prioritize over EQ if ambiguous
        if 'TCKRSYMB' in upper_cols and 'FININSTRMTP' in upper_cols and 'XPRYDT' in upper_cols:
             if 'OPTNTP' in upper_cols or 'STRKPRIC' in upper_cols:
                 return {'type': 'fo_udiff', 'name': 'bhavcopy_fo'}

        # UDIFF CM bhavcopy (New Format)
        if 'TCKRSYMB' in upper_cols and 'SCTYSRS' in upper_cols and 'TRADDT' in upper_cols:
            return {'type': 'cm_udiff', 'name': 'bhavcopy_eq'}

        # Old EQ bhavcopy / Variations
        if 'SYMBOL' in upper_cols and 'SERIES' in upper_cols:
            if 'DATE1' in upper_cols or 'PREV_CLOSE' in upper_cols or 'OPEN' in upper_cols:
                return {'type': 'eq_old', 'name': 'bhavcopy_eq'}

        # Contract Delta (Check first to avoid confusion with FO Bhavcopy)
        if 'DELTA' in upper_cols or 'DELTA FACTOR' in upper_cols:
             return {'type': 'contract_delta', 'name': 'contract_delta'}

        # Old FO Bhavcopy / Variations
        if ('SYMBOL' in upper_cols or 'TICKER' in upper_cols) and ('EXPIRY_DT' in upper_cols or 'EXPIRY DATE' in upper_cols):
             return {'type': 'fo_udiff', 'name': 'bhavcopy_fo'}

        # Block/Bulk Deals
        if 'CLIENT NAME' in columns or 'Client Name' in columns:
            return {'type': 'deals', 'name': 'deals_generic'}

        # Participant OI
        if 'Client Type' in columns and 'Future Index Long' in columns:
            return {'type': 'participant_oi', 'name': 'fao_participant_oi'}

        # FII Stats (special format - often no headers in row 0)
        try:
            if 'FII DERIVATIVES STATISTICS' in str(df.iloc[0:2]).upper():
                return {'type': 'fii_stats', 'name': 'fii_derivatives_stats'}
        except:
            pass

        # FO Volatility
        if 'Symbol' in columns and 'Underlying Close Price (A)' in columns:
            return {'type': 'volatility', 'name': 'fo_volatility'}

        # MTO Delivery
        df_cols_list = df.columns.tolist()
        if 'Record Type' in columns or 'Name of Security' in columns or (len(df_cols_list) > 0 and 'Record Type' in str(df_cols_list[0])):
            return {'type': 'mto', 'name': 'mto_delivery'}

        # MWPL Client - Robust check for "Underlying Stock" and "Client 1"
        # 1. Check existing headers
        if 'Underlying Stock' in columns and 'Client 1' in columns:
            return {'type': 'mwpl', 'name': 'mwpl_client_position'}

        # 2. Check if first column name contains "MWPL"
        if len(df.columns) > 0 and "MWPL" in str(df.columns[0]):
             return {'type': 'mwpl', 'name': 'mwpl_client_position'}

        # 3. Deep Scan (first 20 rows) for header row
        for i in range(min(20, len(df))):
            row_vals = [str(x).strip() for x in df.iloc[i].values if pd.notna(x)]
            # Check for "Underlying Stock" (exact or partial) and "Client 1" (partial)
            has_underlying = any("Underlying Stock" in v for v in row_vals)
            has_client1 = any("Client" in v and "1" in v for v in row_vals)

            if has_underlying and has_client1:
                return {'type': 'mwpl', 'name': 'mwpl_client_position'}

        # P/E Ratio
        if 'SYMBOL' in upper_cols and 'SYMBOL P/E' in upper_cols:
            return {'type': 'pe_ratio', 'name': 'pe_ratio'}

        # Historical Index Data (ind_close_all) includes P/E, P/B, Div Yield and OHLCV
        if 'INDEX NAME' in upper_cols and 'P/E' in upper_cols and 'OPEN INDEX VALUE' in upper_cols:
            # We map this to historical_index_data which handles all in one
            return {'type': 'historical_index_data', 'name': 'historical_index_data'}

        # P/E Ratio (Index format) / India VIX fallback
        if 'INDEX NAME' in upper_cols and 'P/E' in upper_cols:
            # We return pe_ratio_idx by default. The importer caller sets the correct type if it explicitly wants india_vix.
            # We will use 'pe_ratio_idx' as the detected type, but `map_to_records` needs to support `india_vix`.
            return {'type': 'pe_ratio_idx', 'name': 'pe_ratio_idx'}

        # Pure India VIX Historical Data file (e.g. downloaded manually from NSE website)
        if 'DATE' in upper_cols and 'OPEN' in upper_cols and 'HIGH' in upper_cols and 'LOW' in upper_cols and 'CLOSE' in upper_cols and 'PREVIOUS' in upper_cols:
            return {'type': 'india_vix_historical', 'name': 'india_vix'}

        # Security Master
        if 'FinInstrmId' in columns and 'TckrSymb' in columns and 'ISIN' in columns:
            return {'type': 'security_master', 'name': 'security_master'}
        if 'FININSTRMID' in upper_cols and 'TCKRSYMB' in upper_cols:
             return {'type': 'security_master', 'name': 'security_master'}

        # VaR Stats
        if 'Security VaR' in columns or 'Security Symbol' in columns and 'VaR Margin' in columns:
            return {'type': 'var_stats', 'name': 'var_stats'}
        if len(df.columns) > 8 and ('Security Symbol' in columns or 'Symbol' in columns):
             return {'type': 'var_stats', 'name': 'var_stats'}

        # Contract Delta
        if ('DELTA' in columns or 'Delta Factor' in columns) and 'SYMBOL' in columns:
            return {'type': 'contract_delta', 'name': 'contract_delta'}
        if ('DELTA' in upper_cols or 'DELTA FACTOR' in upper_cols) and 'SYMBOL' in upper_cols:
             return {'type': 'contract_delta', 'name': 'contract_delta'}

        # Margin Trading
        if 'Quantity Funded' in columns or 'Amount Funded' in columns:
            return {'type': 'margin_trading', 'name': 'margin_trading'}
        if 'QUANTITY FUNDED' in upper_cols:
             return {'type': 'margin_trading', 'name': 'margin_trading'}

        # Corporate Actions
        if 'PURPOSE' in upper_cols and 'FACE VALUE' in upper_cols:
             return {'type': 'corporate_actions', 'name': 'corporate_actions'}

        # Board Meetings
        if 'BOARDMEETINGDATE' in upper_cols or 'MEETING DATE' in upper_cols:
            return {'type': 'board_meetings', 'name': 'board_meetings'}

        # FII/DII Cash
        if 'CATEGORY' in upper_cols and 'BUY_VALUE' in upper_cols and 'SELL_VALUE' in upper_cols:
            return {'type': 'fii_dii_cash', 'name': 'fii_dii_cash'}

        return {'type': 'unknown', 'name': 'unknown'}

    @classmethod
    def map_to_records(cls, df: pd.DataFrame, format_info: Dict, trade_date: Optional[date] = None) -> List[Dict]:
        """Map dataframe to database records based on format"""
        format_type = format_info['type']

        if format_type == 'cm_udiff':
            return cls._map_cm_udiff(df, trade_date)
        elif format_type == 'fo_udiff':
            return cls._map_fo_udiff(df, trade_date)
        elif format_type == 'eq_old':
            return cls._map_eq_old(df, trade_date)
        elif format_type == 'deals':
             target = format_info.get('target_table', 'bulk_deals')
             return cls._map_deals(df, target, trade_date)
        elif format_type == 'participant_oi':
            return cls._map_participant_oi(df, trade_date)
        elif format_type == 'fii_stats':
            return cls._map_fii_stats(df, trade_date)
        elif format_type == 'volatility':
            return cls._map_volatility(df)
        elif format_type == 'mto':
            return cls._map_mto(df, trade_date)
        elif format_type == 'mwpl':
            return cls._map_mwpl(df, trade_date)
        elif format_type == 'pe_ratio' or format_type == 'pe_ratio_idx':
            return cls._map_pe(df, trade_date, format_type)
        elif format_type == 'india_vix':
            return cls._map_india_vix(df, trade_date)
        elif format_type == 'india_vix_historical':
            return cls._map_india_vix_historical(df, trade_date)
        elif format_type == 'security_master':
            return cls._map_security_master(df)
        elif format_type == 'var_stats':
            return cls._map_var_stats(df, trade_date)
        elif format_type == 'contract_delta':
            return cls._map_contract_delta(df, trade_date)
        elif format_type == 'margin_trading':
            return cls._map_margin_trading(df, trade_date)
        elif format_type == 'corporate_actions':
            return cls._map_corporate_actions(df, trade_date)
        elif format_type == 'board_meetings':
            return cls._map_board_meetings(df, trade_date)
        elif format_type == 'fii_dii_cash':
            return cls._map_fii_dii_cash(df, trade_date)
        elif format_type == 'historical_index_data':
            return cls._map_historical_index_data(df, trade_date)

        return []

    # --- Mapping Implementations ---

    @classmethod
    def _get_val(cls, row: pd.Series, keys: List[str]) -> Any:
        """Helper to get value from row using multiple possible keys (case-insensitive)"""
        # Create a mapping of upper-case keys to actual keys in row
        row_keys_map = {str(k).strip().upper(): k for k in row.index}

        for k in keys:
            upper_k = k.strip().upper()
            if upper_k in row_keys_map:
                return row[row_keys_map[upper_k]]
        return None

    @classmethod
    def _map_cm_udiff(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        # Filter EQ series if column exists
        series_col = cls._find_col(df, ['SctySrs', 'SERIES'])
        if series_col:
            initial_count = len(df)
            # Normalize whitespace in series column values
            df[series_col] = df[series_col].astype(str).str.strip()
            # To allow any non F&O stocks and different series types to be fetched/queried if the user wishes to force it
            # We relax the strict EQ filter if other symbols matter, but by default EQ, BE, SM, BZ etc exist. Let's keep EQ and others to avoid data loss.
            valid_series = ['EQ', 'BE', 'SM', 'BZ']
            df = df[df[series_col].isin(valid_series)].copy()
            if len(df) == 0 and initial_count > 0:
                logger.warning(f"Bhavcopy EQ: Filtered all rows. Series column '{series_col}' found but no valid series rows.")

        for _, row in df.iterrows():
            record = {
                'symbol': str(cls._get_val(row, ['TckrSymb', 'SYMBOL']) or '').strip(),
                'series': 'EQ',
                'trade_date': trade_date or parse_nse_date(cls._get_val(row, ['TradDt', 'DATE1'])),
                'prev_close': cls._clean_numeric(cls._get_val(row, ['PrvsClsgPric', 'PREV_CLOSE'])),
                'open_price': cls._clean_numeric(cls._get_val(row, ['OpnPric', 'OPEN_PRICE', 'OPEN'])),
                'high_price': cls._clean_numeric(cls._get_val(row, ['HghPric', 'HIGH_PRICE', 'HIGH'])),
                'low_price': cls._clean_numeric(cls._get_val(row, ['LwPric', 'LOW_PRICE', 'LOW'])),
                'last_price': cls._clean_numeric(cls._get_val(row, ['LastPric', 'LAST_PRICE', 'LAST'])),
                'close_price': cls._clean_numeric(cls._get_val(row, ['ClsPric', 'CLOSE_PRICE', 'CLOSE'])),
                'avg_price': cls._clean_numeric(cls._get_val(row, ['VWAP', 'AVG_PRICE', 'AVERAGE_PRICE'])),
                'total_traded_qty': cls._clean_integer(cls._get_val(row, ['TtlTradgVol', 'TTL_TRD_QNTY', 'Total Traded Quantity'])),
                'turnover_lacs': cls._clean_numeric(cls._get_val(row, ['TtlTrfVal', 'TURNOVER_LACS', 'Turnover'])),
                'no_of_trades': cls._clean_integer(cls._get_val(row, ['TtlNbOfTxsExctd', 'NO_OF_TRADES'])),
            }
            if record['symbol']:
                records.append(record)
        return records

    @classmethod
    def _parse_dividend(cls, purpose: str, face_value: Optional[float]) -> tuple[Optional[float], Optional[str]]:
        if not purpose:
            return None, None

        purpose_lower = purpose.lower()

        # Check for Bonus or Split first
        if 'bonus' in purpose_lower:
            return None, 'Bonus'
        if 'split' in purpose_lower or 'sub-division' in purpose_lower or 'sub division' in purpose_lower:
            return None, 'Split'
        if 'demerger' in purpose_lower or 'spin-off' in purpose_lower or 'spin off' in purpose_lower:
            return None, 'Demerger'

        if 'dividend' not in purpose_lower:
            return None, None

        import re
        dividend_type = 'Interim' if 'interim' in purpose_lower else 'Special' if 'special' in purpose_lower else 'Final'

        # Try Rs format: sum all amounts if multiple exist (e.g. "Dividend - Rs 3 & Special - Rs 3")
        rs_matches = re.findall(r'rs\.?\s*(\d+(?:\.\d+)?)', purpose_lower)
        if rs_matches:
            total_amount = sum(float(m) for m in rs_matches)
            return total_amount, dividend_type

        # Try percentage format: sum all percentages if multiple exist
        pct_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', purpose_lower)
        if pct_matches and face_value:
            total_pct = sum(float(m) for m in pct_matches)
            return (total_pct / 100.0) * face_value, dividend_type

        return None, dividend_type

    @classmethod
    def _map_corporate_actions(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        # Columns usually: SYMBOL, COMPANY NAME, SERIES, PURPOSE, FACE VALUE, EX-DATE, RECORD DATE, BC START DATE, BC END DATE, ND START DATE, ND END DATE
        for _, row in df.iterrows():
            ex_date_val = parse_nse_date(cls._get_val(row, ['Ex-Date', 'EX-DATE']))
            purpose = str(cls._get_val(row, ['PURPOSE', 'Purpose']) or '').strip()
            face_value = cls._clean_numeric(cls._get_val(row, ['FACE VALUE', 'Face Value']))

            parsed_div_amount, div_type = cls._parse_dividend(purpose, face_value)

            record = {
                'date': ex_date_val or trade_date,
                'ex_date': ex_date_val,
                'symbol': str(cls._get_val(row, ['SYMBOL', 'Symbol']) or '').strip(),
                'company_name': str(cls._get_val(row, ['COMPANY NAME', 'Company Name']) or '').strip(),
                'series': str(cls._get_val(row, ['SERIES', 'Series']) or '').strip(),
                'face_value': face_value,
                'purpose': purpose,
                'record_date': parse_nse_date(cls._get_val(row, ['RECORD DATE', 'Record Date'])),
                'bc_start_date': parse_nse_date(cls._get_val(row, ['BC START DATE', 'BC Start Date', 'BOOK CLOSURE START DATE'])),
                'bc_end_date': parse_nse_date(cls._get_val(row, ['BC END DATE', 'BC End Date', 'BOOK CLOSURE END DATE'])),
                'nd_start_date': parse_nse_date(cls._get_val(row, ['ND START DATE', 'ND Start Date'])),
                'nd_end_date': parse_nse_date(cls._get_val(row, ['ND END DATE', 'ND End Date'])),
                'parsed_dividend_amount': parsed_div_amount,
                'dividend_type': div_type,
                'broadcast_date': parse_nse_datetime(cls._get_val(row, ['BROADCAST DATE', 'caBroadcastDate']))
            }
            if record['symbol'] and record['date']:
                records.append(record)
        return records

    @classmethod
    def _map_board_meetings(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        for _, row in df.iterrows():
            bm_date_val = parse_nse_date(cls._get_val(row, ['BoardMeetingDate', 'MEETING DATE', 'Meeting Date']))
            broadcast_str = cls._get_val(row, ['BROADCAST DATE', 'bm_timestamp', 'Broadcast Date'])
            broadcast_dt = parse_nse_datetime(broadcast_str) if broadcast_str else None

            # Use broadcast_date for partition key 'date' (representing when the announcement happened)
            # Default to trade_date if no broadcast date.
            record_date = broadcast_dt.date() if broadcast_dt else trade_date

            record = {
                'date': record_date or bm_date_val,
                'meeting_date': bm_date_val, # explicitly store meeting date
                'symbol': str(cls._get_val(row, ['SYMBOL', 'Symbol']) or '').strip(),
                'company_name': str(cls._get_val(row, ['COMPANY NAME', 'Company Name']) or '').strip(),
                'purpose': str(cls._get_val(row, ['PURPOSE', 'Purpose']) or '').strip(),
                'bm_desc': str(cls._get_val(row, ['BM_DESC', 'Description']) or '').strip(),
                'extracted_dividend_amount': cls._clean_numeric(cls._get_val(row, ['EXTRACTED_DIVIDEND_AMOUNT'])),
                'extracted_dividend_type': str(cls._get_val(row, ['EXTRACTED_DIVIDEND_TYPE']) or '').strip() or None,
                'extracted_record_date': str(cls._get_val(row, ['EXTRACTED_RECORD_DATE']) or '').strip() or None
            }
            if record['symbol'] and record['date']:
                records.append(record)
        return records

    @classmethod
    def _map_fo_udiff(cls, df: pd.DataFrame, trade_date: Optional[date] = None) -> List[Dict]:
        records = []
        for _, row in df.iterrows():
            row_date = parse_nse_date(cls._get_val(row, ['TradDt', 'TIMESTAMP']))
            inst_type = str(cls._get_val(row, ['FinInstrmTp', 'INSTRUMENT', 'INSTRUMENT TYPE']) or '').strip()

            record = {
                'ticker_symb': str(cls._get_val(row, ['TckrSymb', 'SYMBOL', 'TICKER']) or '').strip(),
                'instrument_type': inst_type,
                'trade_date': row_date or trade_date,
                'expiry_date': parse_nse_date(cls._get_val(row, ['XpryDt', 'EXPIRY_DT', 'EXPIRY DATE'])),
                'strike_price': cls._clean_numeric(cls._get_val(row, ['StrkPric', 'STRIKE_PR', 'STRIKE PRICE'])),
                'option_type': str(cls._get_val(row, ['OptnTp', 'OPTION_TYP', 'OPTION TYPE']) or '').strip(),
                'instrument_name': str(cls._get_val(row, ['FinInstrmNm']) or '').strip(),
                'open_price': cls._clean_numeric(cls._get_val(row, ['OpnPric', 'OPEN'])),
                'high_price': cls._clean_numeric(cls._get_val(row, ['HghPric', 'HIGH'])),
                'low_price': cls._clean_numeric(cls._get_val(row, ['LwPric', 'LOW'])),
                'close_price': cls._clean_numeric(cls._get_val(row, ['ClsPric', 'CLOSE'])),
                'settle_price': cls._clean_numeric(cls._get_val(row, ['SttlmPric', 'SETTLE_PR'])),
                'open_interest': cls._clean_integer(cls._get_val(row, ['OpnIntrst', 'OPEN_INT'])),
                'change_in_oi': cls._clean_integer(cls._get_val(row, ['ChngInOpnIntrst', 'CHG_IN_OI'])),
                'total_trading_vol': cls._clean_integer(cls._get_val(row, ['TtlTradgVol', 'CONTRACTS', 'Total Traded Quantity'])),
                'total_trf_val': cls._clean_numeric(cls._get_val(row, ['TtlTrfVal', 'VAL_IN_LAKH'])),
            }
            if record['ticker_symb']:
                records.append(record)
        return records

    @classmethod
    def _find_col(cls, df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
        row_keys_map = {str(k).strip().upper(): k for k in df.columns}
        for k in candidates:
            if k.upper() in row_keys_map:
                return row_keys_map[k.upper()]
        return None

    @classmethod
    def _map_eq_old(cls, df: pd.DataFrame, trade_date: Optional[date] = None) -> List[Dict]:
        records = []
        if 'SERIES' in df.columns:
            df['SERIES'] = df['SERIES'].astype(str).str.strip()
            valid_series = ['EQ', 'BE', 'SM', 'BZ']
            df = df[df['SERIES'].isin(valid_series)].copy()

        for _, row in df.iterrows():
            record = {
                'symbol': str(row.get('SYMBOL', '')).strip(),
                'series': 'EQ',
                'trade_date': trade_date or parse_nse_date(row.get('DATE1')),
                'prev_close': cls._clean_numeric(row.get('PREV_CLOSE')),
                'open_price': cls._clean_numeric(row.get('OPEN_PRICE')),
                'high_price': cls._clean_numeric(row.get('HIGH_PRICE')),
                'low_price': cls._clean_numeric(row.get('LOW_PRICE')),
                'last_price': cls._clean_numeric(row.get('LAST_PRICE')),
                'close_price': cls._clean_numeric(row.get('CLOSE_PRICE')),
                'avg_price': cls._clean_numeric(cls._get_val(row, ['VWAP', 'AVG_PRICE', 'AVERAGE_PRICE'])),
                'total_traded_qty': cls._clean_integer(row.get('TTL_TRD_QNTY')),
                'turnover_lacs': cls._clean_numeric(row.get('TURNOVER_LACS')),
                'no_of_trades': cls._clean_integer(row.get('NO_OF_TRADES')),
                'deliverable_qty': cls._clean_integer(row.get('DELIV_QTY')),
                'deliverable_pct': cls._clean_numeric(row.get('DELIV_PER')),
            }
            if record['symbol']:
                records.append(record)
        return records

    @classmethod
    def _map_deals(cls, df: pd.DataFrame, table_name: str, trade_date: Optional[date] = None) -> List[Dict]:
        records = []
        date_col = cls._find_col(df, ['DATE', 'Date'])
        file_date = trade_date

        for _, row in df.iterrows():
            row_date = parse_nse_date(row.get(date_col)) if date_col else None
            effective_date = row_date or file_date

            record = {
                'date': effective_date,
                'symbol': str(cls._get_val(row, ['SYMBOL', 'Symbol', 'Scrip Name']) or '').strip(),
                'security_name': str(cls._get_val(row, ['SECURITY NAME', 'Security Name']) or '').strip(),
                'client_name': str(cls._get_val(row, ['CLIENT NAME', 'Client Name']) or '').strip(),
                'buy_sell': str(cls._get_val(row, ['BUY/SELL', 'Buy/Sell', 'Buy / Sell']) or '').strip(),
                'quantity_traded': cls._clean_integer(cls._get_val(row, ['QUANTITY TRADED', 'Quantity Traded'])),
                'trade_price': cls._clean_numeric(cls._get_val(row, ['TRADE PRICE/ WEIGHTED. AVG. PRICE', 'Trade Price / Wght. Avg. Price', 'Trade Price'])),
                'remarks': str(cls._get_val(row, ['REMARKS', 'Remarks']) or '').strip(),
            }
            if record['symbol']:
                records.append(record)
        return records

    @classmethod
    def _map_participant_oi(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        for _, row in df.iterrows():
            record = {
                'trade_date': trade_date,
                'client_type': str(row.get('Client Type', '')).strip(),
                'future_index_long': cls._clean_integer(row.get('Future Index Long')),
                'future_index_short': cls._clean_integer(row.get('Future Index Short')),
                'future_stock_long': cls._clean_integer(row.get('Future Stock Long')),
                'future_stock_short': cls._clean_integer(row.get('Future Stock Short')),
                'option_index_call_long': cls._clean_integer(row.get('Option Index Call Long')),
                'option_index_put_long': cls._clean_integer(row.get('Option Index Put Long')),
                'option_index_call_short': cls._clean_integer(row.get('Option Index Call Short')),
                'option_index_put_short': cls._clean_integer(row.get('Option Index Put Short')),
                'option_stock_call_long': cls._clean_integer(row.get('Option Stock Call Long')),
                'option_stock_put_long': cls._clean_integer(row.get('Option Stock Put Long')),
                'option_stock_call_short': cls._clean_integer(row.get('Option Stock Call Short')),
                'option_stock_put_short': cls._clean_integer(row.get('Option Stock Put Short')),
                'total_long_contracts': cls._clean_integer(row.get('Total Long Contracts')),
                'total_short_contracts': cls._clean_integer(row.get('Total Short Contracts')),
            }
            if record['client_type']:
                records.append(record)
        return records

    @classmethod
    def _map_fii_dii_cash(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        for _, row in df.iterrows():
            # If the dataframe has its own Date column from manual upload, use it instead of the argument trade_date
            row_date_str = str(cls._get_val(row, ['date', 'Date', 'DATE']) or '').strip()
            row_trade_date = trade_date
            if row_date_str and row_date_str != 'None':
                try:
                    row_trade_date = pd.to_datetime(row_date_str, format='mixed', dayfirst=True).date()
                except:
                    pass

            record = {
                'trade_date': row_trade_date,
                'category': str(cls._get_val(row, ['category', 'Category', 'CATEGORY']) or '').strip(),
                'buy_value': cls._clean_numeric(cls._get_val(row, ['buy_value', 'Buy Value', 'BUY_VALUE'])),
                'sell_value': cls._clean_numeric(cls._get_val(row, ['sell_value', 'Sell Value', 'SELL_VALUE'])),
                'net_value': cls._clean_numeric(cls._get_val(row, ['net_value', 'Net Value', 'NET_VALUE'])),
            }
            if record['category'] and record['trade_date']:
                records.append(record)
        return records

    @classmethod
    def _map_fii_stats(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        start_row = 0
        for i, row in df.iterrows():
            row_str = ' '.join([str(x) for x in row.values if pd.notna(x)])
            if 'BUY' in row_str and 'SELL' in row_str:
                start_row = i + 1
                break

        current_instrument = None
        for i in range(start_row, len(df)):
            row = df.iloc[i]
            if pd.isna(row.iloc[0]):
                continue

            instrument = str(row.iloc[0]).strip().upper()

            for inv in cls.FII_STATS_INSTRUMENTS:
                if inv in instrument:
                    current_instrument = inv
                    break

            if current_instrument and len(row) >= 7:
                try:
                    record = {
                        'date': trade_date,
                        'instrument_type': current_instrument,
                        'buy_contracts': cls._clean_integer(row.iloc[1]),
                        'buy_amt_crores': cls._clean_numeric(row.iloc[2]),
                        'sell_contracts': cls._clean_integer(row.iloc[3]),
                        'sell_amt_crores': cls._clean_numeric(row.iloc[4]),
                        'oi_contracts': cls._clean_integer(row.iloc[5]),
                        'oi_amt_crores': cls._clean_numeric(row.iloc[6]),
                    }
                    if any([record['buy_contracts'], record['sell_contracts'], record['oi_contracts']]):
                        records.append(record)
                except:
                    continue
        return records

    @classmethod
    def _map_volatility(cls, df: pd.DataFrame) -> List[Dict]:
        records = []
        col_map = {}
        for c in df.columns:
            c_str = str(c).strip()
            if c_str.startswith('Underlying Annualised Volatility (F)'):
                col_map['underlying_annualised_vol'] = c
            elif c_str.startswith('Futures Annualised Volatility (L)'):
                col_map['futures_annualised_vol'] = c
            elif c_str.startswith('Applicable Daily Volatility (M)'):
                col_map['applicable_daily_vol'] = c
            elif c_str.startswith('Applicable Annualised Volatility (N)'):
                col_map['applicable_annualised_vol'] = c

        for _, row in df.iterrows():
            record = {
                'trade_date': parse_nse_date(row.get('Date')),
                'symbol': str(row.get('Symbol', '')).strip(),
                'underlying_close_price': cls._clean_numeric(row.get('Underlying Close Price (A)')),
                'underlying_annualised_vol': cls._clean_numeric(row.get(col_map.get('underlying_annualised_vol', 'Underlying Annualised Volatility (F)'))),
                'futures_close_price': cls._clean_numeric(row.get('Futures Close Price (G)')),
                'futures_annualised_vol': cls._clean_numeric(row.get(col_map.get('futures_annualised_vol', 'Futures Annualised Volatility (L)'))),
                'applicable_daily_vol': cls._clean_numeric(row.get(col_map.get('applicable_daily_vol', 'Applicable Daily Volatility (M)'))),
                'applicable_annualised_vol': cls._clean_numeric(row.get(col_map.get('applicable_annualised_vol', 'Applicable Annualised Volatility (N)'))),
            }
            if record['symbol']:
                records.append(record)
        return records

    @classmethod
    def _map_mto(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []

        # Determine if 'record type' header exists inside the data rows (pre-deduplication artifact)
        # We can just skip those rows based on the 'Record Type' column value instead of forcing index 0
        cols = [str(c).strip().lower() for c in df.columns]

        def get_val_from_row(row, keywords):
            for idx, c in enumerate(cols):
                # For strict keyword matching like 'series', exact match is safer
                # For others like 'name of security', 'in' is fine
                if any((k == c if k == 'series' else k in c) for k in keywords):
                    return row.iloc[idx]
            return None

        for _, row in df.iterrows():
            # To handle both original parsing and deduplicated parsing (where 'Name of Security' becomes column 0),
            # we should access columns by exact or partial names instead of fragile index positions.

            rec_type = str(get_val_from_row(row, ['record type']) or '').strip().lower()
            if rec_type == 'record type':
                continue

            record = {
                'trade_date': trade_date,
                'settlement_type': str(get_val_from_row(row, ['series']) or 'EQ').strip(),
                'sr_no': cls._clean_integer(get_val_from_row(row, ['sr no', 'sr_no', 'serial'])),
                'security_name': str(get_val_from_row(row, ['name of security', 'security_name']) or '').strip(),
                'quantity_traded': cls._clean_integer(get_val_from_row(row, ['quantity traded', 'traded qty'])),
                'deliverable_qty': cls._clean_integer(get_val_from_row(row, ['deliverable quantity', 'deliverable qty'])),
                'deliverable_pct': cls._clean_numeric(get_val_from_row(row, ['% of deliverable', 'deliverable pct'])),
            }
            if record['security_name'] and record['settlement_type'] == 'EQ':
                # Re-calculate accurate deliverable pct after deduplication sum (to prevent broken > 100% data)
                if record['quantity_traded'] and record['deliverable_qty'] and record['quantity_traded'] > 0:
                    record['deliverable_pct'] = round((record['deliverable_qty'] / record['quantity_traded']) * 100, 2)

                records.append(record)
        return records

    @classmethod
    def _map_mwpl(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []

        # Handle raw DF where headers are not yet set
        header_row_idx = None

        # Check if 'Client 1' is NOT in columns (meaning columns are likely ints or messed up)
        # Or if "Underlying Stock" isn't present
        columns_str = [str(c).strip() for c in df.columns]
        if not any("Client" in c and "1" in c for c in columns_str) or not any("Underlying Stock" in c for c in columns_str):
             # Scan first 20 rows to find header row
             for i in range(min(20, len(df))):
                 # Convert row to string values for checking
                 row_vals = [str(x).strip() for x in df.iloc[i].values if pd.notna(x)]

                 has_underlying = any("Underlying Stock" in v for v in row_vals)
                 has_client1 = any("Client" in v and "1" in v for v in row_vals)

                 if has_underlying and has_client1:
                     header_row_idx = i
                     break

             if header_row_idx is not None:
                 logger.info(f"Found MWPL Header at row {header_row_idx}")
                 # Set the header
                 headers = [str(x).strip() for x in df.iloc[header_row_idx].values]
                 # Slice data after header
                 df = df.iloc[header_row_idx + 1:].copy()
                 # Assign new columns
                 df.columns = headers
                 df.reset_index(drop=True, inplace=True)
             else:
                 logger.warning("MWPL Mapping: Could not locate header row containing 'Underlying Stock' and 'Client 1'")
                 return []

        # Normalize columns (strip whitespace) to ensure 'Client 1' lookup works
        df.columns = [str(c).strip() for c in df.columns]

        # Identify "Client X" columns dynamically
        client_col_map = {}
        for col in df.columns:
            # Regex to find "Client 1", "Client  2", "Client-3" etc.
            match = re.match(r'Client\s*[_-]?\s*(\d+)', col, re.IGNORECASE)
            if match:
                client_num = int(match.group(1))
                client_col_map[client_num] = col

        logger.info(f"MWPL Mapping: Identified {len(client_col_map)} client columns.")

        # Get the actual 'Underlying Stock' column name since we stripped whitespace
        underlying_col = next((c for c in df.columns if "Underlying Stock" in str(c)), 'Underlying Stock')

        for _, row in df.iterrows():
            underlying = str(row.get(underlying_col, '')).strip()
            if not underlying or underlying == 'nan' or underlying == 'None':
                continue

            for i, client_col_name in client_col_map.items():
                val = row[client_col_name]
                if pd.notna(val):
                    records.append({
                        'date': trade_date,
                        'underlying_stock': underlying,
                        'client_position_num': i,
                        'position_pct': cls._clean_numeric(val),
                    })
        return records

    @classmethod
    def _map_pe(cls, df: pd.DataFrame, trade_date: Optional[date], format_type: str = 'pe_ratio') -> List[Dict]:
        records = []

        if format_type == 'pe_ratio_idx':
            for _, row in df.iterrows():
                symbol = str(cls._get_val(row, ['Index Name']) or '').strip()
                if symbol == 'India VIX':
                    continue # Skip India VIX from pe_ratio_idx since we have a dedicated table
                row_date = parse_nse_date(cls._get_val(row, ['Index Date']))
                record = {
                    'date': row_date or trade_date,
                    'symbol': symbol,
                    'pe': cls._clean_numeric(cls._get_val(row, ['P/E'])),
                    'pb': cls._clean_numeric(cls._get_val(row, ['P/B'])),
                    'div_yield': cls._clean_numeric(cls._get_val(row, ['Div Yield']))
                }
                if record['symbol']:
                    records.append(record)
            return records

        for _, row in df.iterrows():
            record = {
                'date': trade_date,
                'symbol': str(cls._get_val(row, ['SYMBOL']) or '').strip(),
                'symbol_pe': cls._clean_numeric(cls._get_val(row, ['SYMBOL P/E'])),
                'adjusted_pe': cls._clean_numeric(cls._get_val(row, ['ADJUSTED P/E'])),
            }
            if record['symbol']:
                records.append(record)
        return records

    @classmethod
    def _map_india_vix(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        for _, row in df.iterrows():
            symbol = str(cls._get_val(row, ['Index Name']) or '').strip()
            if symbol != 'India VIX':
                continue

            row_date = parse_nse_date(cls._get_val(row, ['Index Date']))
            record = {
                'date': row_date or trade_date,
                'open_value': cls._clean_numeric(cls._get_val(row, ['Open Index Value'])),
                'high_value': cls._clean_numeric(cls._get_val(row, ['High Index Value'])),
                'low_value': cls._clean_numeric(cls._get_val(row, ['Low Index Value'])),
                'close_value': cls._clean_numeric(cls._get_val(row, ['Closing Index Value'])),
                'points_change': cls._clean_numeric(cls._get_val(row, ['Points Change'])),
                'percent_change': cls._clean_numeric(cls._get_val(row, ['Change(%)']))
            }
            records.append(record)
        return records

    @classmethod
    def _map_historical_index_data(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        for _, row in df.iterrows():
            row_date = parse_nse_date(cls._get_val(row, ['Index Date', 'Date']))
            if not row_date:
                row_date = trade_date
            if not row_date:
                continue

            index_name = str(cls._get_val(row, ['Index Name', 'INDEX NAME']) or '').strip()
            if not index_name:
                continue

            # Skip VIX as it's processed separately usually, but we could include it if we wanted.
            # Actually, let's keep it here in the new table if present.

            record = {
                'trade_date': row_date,
                'index_name': index_name,
                'open_price': cls._clean_numeric(cls._get_val(row, ['Open Index Value', 'OPEN INDEX VALUE'])),
                'high_price': cls._clean_numeric(cls._get_val(row, ['High Index Value', 'HIGH INDEX VALUE'])),
                'low_price': cls._clean_numeric(cls._get_val(row, ['Low Index Value', 'LOW INDEX VALUE'])),
                'close_price': cls._clean_numeric(cls._get_val(row, ['Closing Index Value', 'CLOSING INDEX VALUE'])),
                'total_traded_qty': cls._clean_integer(cls._get_val(row, ['Volume', 'VOLUME'])),
                'turnover_cr': cls._clean_numeric(cls._get_val(row, ['Turnover (Rs. Cr)', 'Turnover', 'TURNOVER'])),
                'pe_ratio': cls._clean_numeric(cls._get_val(row, ['P/E'])),
                'pb_ratio': cls._clean_numeric(cls._get_val(row, ['P/B'])),
                'div_yield': cls._clean_numeric(cls._get_val(row, ['Div Yield']))
            }
            records.append(record)
        return records

    @classmethod
    def _map_india_vix_historical(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        for _, row in df.iterrows():
            row_date = parse_nse_date(cls._get_val(row, ['Date']))
            if not row_date:
                # Fallback to trade_date if the Date column couldn't be parsed
                row_date = trade_date

            if not row_date:
                continue

            record = {
                'date': row_date,
                'open_value': cls._clean_numeric(cls._get_val(row, ['Open'])),
                'high_value': cls._clean_numeric(cls._get_val(row, ['High'])),
                'low_value': cls._clean_numeric(cls._get_val(row, ['Low'])),
                'close_value': cls._clean_numeric(cls._get_val(row, ['Close'])),
                'points_change': cls._clean_numeric(cls._get_val(row, ['Change'])),
                'percent_change': cls._clean_numeric(cls._get_val(row, ['%Change']))
            }
            records.append(record)
        return records

    @classmethod
    def _map_security_master(cls, df: pd.DataFrame) -> List[Dict]:
        records = []
        if 'SctySrs' in df.columns:
            # Only take EQ and F&O listed companies per user request (and others if explicitly asked to import non-F&O)
            pass

        for _, row in df.iterrows():

            # Format additional_info to text properly if it's there
            addtl_inf = row.get('AddtlInf', '')
            if pd.isna(addtl_inf):
                addtl_inf = ''
            else:
                addtl_inf = str(addtl_inf).strip()

            record = {
                'fin_instrm_id': str(row.get('FinInstrmId', '')).strip(),
                'ticker_symb': str(row.get('TckrSymb', '')).strip(),
                'security_series': row.get('SctySrs', ''),
                'instrument_name': row.get('FinInstrmNm', ''),
                'isin': row.get('ISIN', ''),
                'new_brd_lot_qty': cls._clean_integer(row.get('NewBrdLotQty')),
                'par_val': cls._clean_numeric(row.get('ParVal')),
                'issued_capital': cls._clean_numeric(row.get('IssdCptl')),
                'listed_date': parse_nse_date(row.get('ListgDt')),
                'additional_info': addtl_inf,
                'special_ex_date': parse_nse_date(row.get('SpclExDt')),
                'status': row.get('Sts', ''),
            }
            if record['fin_instrm_id']:
                records.append(record)
        return records

    @classmethod
    def _map_var_stats(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        for _, row in df.iterrows():
            record = {
                'date': trade_date,
                'symbol': str(row.get('Security Symbol', row.get('Symbol', ''))).strip(),
                'series': str(row.get('Series', '')).strip(),
                'security_var': cls._clean_numeric(row.get('Security VaR')),
                'index_var': cls._clean_numeric(row.get('Index VaR')),
                'var_margin': cls._clean_numeric(row.get('VaR Margin')),
                'extreme_loss_rate': cls._clean_numeric(row.get('Extreme Loss Rate')),
                'adho_margin': cls._clean_numeric(row.get('Adhoc Margin')),
                'applicable_margin_rate': cls._clean_numeric(row.get('Applicable Margin Rate')),
            }
            if record['symbol']:
                records.append(record)
        return records

    @classmethod
    def _map_contract_delta(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        # Support both 'Expiry Date' and 'Expiry day', 'Delta' and 'Delta Factor' (case insensitive using _get_val)
        for _, row in df.iterrows():
            expiry = cls._get_val(row, ['Expiry Date', 'Expiry day', 'EXPIRY DATE', 'EXPIRY DAY'])
            delta = cls._get_val(row, ['Delta Factor', 'Delta', 'DELTA FACTOR', 'DELTA'])

            record = {
                'date': trade_date,
                'symbol': str(cls._get_val(row, ['Symbol', 'SYMBOL']) or '').strip(),
                'expiry_date': parse_nse_date(expiry),
                'strike_price': cls._clean_numeric(cls._get_val(row, ['Strike Price', 'STRIKE PRICE'])),
                'option_type': str(cls._get_val(row, ['Option Type', 'OPTION TYPE']) or '').strip(),
                'delta': cls._clean_numeric(delta),
            }
            if record['symbol'] and record['symbol'].lower() != 'nan' and record['symbol'] != 'None':
                records.append(record)

        if not records:
            logger.error(f"Contract delta mapping produced 0 records from {len(df)} rows. Columns: {df.columns.tolist()}")
        return records

    @classmethod
    def _map_margin_trading(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        for _, row in df.iterrows():
            record = {
                'date': trade_date,
                'symbol': str(row.get('Symbol', '')).strip(),
                'quantity_funded': cls._clean_integer(row.get('Quantity Funded')),
                'amount_funded': cls._clean_numeric(row.get('Amount Funded')),
            }
            if record['symbol']:
                records.append(record)
        return records

    @classmethod
    def _clean_numeric(cls, value: Any) -> Optional[float]:
        if pd.isna(value) or value is None or str(value).strip() == '-':
            return None
        try:
            return float(str(value).replace(',', '').strip())
        except:
            return None

    @classmethod
    def _clean_integer(cls, value: Any) -> Optional[int]:
        cleaned = cls._clean_numeric(value)
        return int(cleaned) if cleaned is not None else None
