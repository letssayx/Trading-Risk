from typing import Dict, Any, List, Optional
import pandas as pd
import logging
from datetime import date
from backend.ingest.date_utils import parse_nse_date
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
        if 'DELTA' in upper_cols:
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
        if 'SYMBOL' in columns and 'SYMBOL P/E' in columns:
            return {'type': 'pe_ratio', 'name': 'pe_ratio'}

        # P/E Ratio (Index format) / India VIX
        if 'Index Name' in columns and 'P/E' in columns:
            # We return pe_ratio_idx by default. The importer caller sets the correct type if it explicitly wants india_vix.
            # But wait, if someone uploads this file manually, how do we know if they want pe_ratio_idx or india_vix?
            # We can map both, but typical manual upload would use the key they requested.
            # We will use 'pe_ratio_idx' as the detected type, but `map_to_records` needs to support `india_vix`.
            return {'type': 'pe_ratio_idx', 'name': 'pe_ratio_idx'}

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
        if 'Delta' in columns and 'Strike Price' in columns:
            return {'type': 'contract_delta', 'name': 'contract_delta'}
        if 'DELTA' in upper_cols and 'SYMBOL' in upper_cols:
             return {'type': 'contract_delta', 'name': 'contract_delta'}

        # Margin Trading
        if 'Quantity Funded' in columns or 'Amount Funded' in columns:
            return {'type': 'margin_trading', 'name': 'margin_trading'}
        if 'QUANTITY FUNDED' in upper_cols:
             return {'type': 'margin_trading', 'name': 'margin_trading'}

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
            df = df[df[series_col] == 'EQ'].copy()
            if len(df) == 0 and initial_count > 0:
                logger.warning(f"Bhavcopy EQ: Filtered all rows. Series column '{series_col}' found but no 'EQ' rows.")

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
                'total_traded_qty': cls._clean_integer(cls._get_val(row, ['TtlTradgVol', 'TTL_TRD_QNTY', 'Total Traded Quantity'])),
                'turnover_lacs': cls._clean_numeric(cls._get_val(row, ['TtlTrfVal', 'TURNOVER_LACS', 'Turnover'])),
                'no_of_trades': cls._clean_integer(cls._get_val(row, ['TtlNbOfTxsExctd', 'NO_OF_TRADES'])),
            }
            if record['symbol']:
                records.append(record)
        return records

    @classmethod
    def _map_corporate_actions(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        # Columns usually: SYMBOL, COMPANY NAME, SERIES, PURPOSE, FACE VALUE, EX-DATE, RECORD DATE, BC START DATE, BC END DATE, ND START DATE, ND END DATE
        for _, row in df.iterrows():
            ex_date_val = parse_nse_date(cls._get_val(row, ['Ex-Date', 'EX-DATE']))

            record = {
                'date': ex_date_val or trade_date,
                'ex_date': ex_date_val,
                'symbol': str(cls._get_val(row, ['SYMBOL', 'Symbol']) or '').strip(),
                'company_name': str(cls._get_val(row, ['COMPANY NAME', 'Company Name']) or '').strip(),
                'series': str(cls._get_val(row, ['SERIES', 'Series']) or '').strip(),
                'face_value': cls._clean_numeric(cls._get_val(row, ['FACE VALUE', 'Face Value'])),
                'purpose': str(cls._get_val(row, ['PURPOSE', 'Purpose']) or '').strip(),
                'record_date': parse_nse_date(cls._get_val(row, ['RECORD DATE', 'Record Date'])),
                'bc_start_date': parse_nse_date(cls._get_val(row, ['BC START DATE', 'BC Start Date'])),
                'bc_end_date': parse_nse_date(cls._get_val(row, ['BC END DATE', 'BC End Date'])),
                'nd_start_date': parse_nse_date(cls._get_val(row, ['ND START DATE', 'ND Start Date'])),
                'nd_end_date': parse_nse_date(cls._get_val(row, ['ND END DATE', 'ND End Date'])),
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
            df = df[df['SERIES'] == 'EQ'].copy()

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
                'buy_sell': str(cls._get_val(row, ['BUY/SELL', 'Buy/Sell']) or '').strip(),
                'quantity_traded': cls._clean_integer(cls._get_val(row, ['QUANTITY TRADED', 'Quantity Traded'])),
                'trade_price': cls._clean_numeric(cls._get_val(row, ['TRADE PRICE/ WEIGHTED. AVG. PRICE', 'Trade Price / Wght. Avg. Price'])),
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
        for _, row in df.iterrows():
            first_val = str(row.iloc[0]).strip()
            if first_val.lower() == 'record type' or first_val == '':
                continue

            record = {
                'trade_date': trade_date,
                'settlement_type': 'N',
                'sr_no': cls._clean_integer(row.iloc[1] if len(row) > 1 else None),
                'security_name': str(row.iloc[2] if len(row) > 2 else '').strip(),
                'quantity_traded': cls._clean_integer(row.iloc[3] if len(row) > 3 else None),
                'deliverable_qty': cls._clean_integer(row.iloc[4] if len(row) > 4 else None),
                'deliverable_pct': cls._clean_numeric(row.iloc[5] if len(row) > 5 else None),
            }
            if record['security_name']:
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
                symbol = str(row.get('Index Name', '')).strip()
                if symbol == 'India VIX':
                    continue # Skip India VIX from pe_ratio_idx since we have a dedicated table
                row_date = parse_nse_date(row.get('Index Date'))
                record = {
                    'date': row_date or trade_date,
                    'symbol': symbol,
                    'pe': cls._clean_numeric(row.get('P/E')),
                    'pb': cls._clean_numeric(row.get('P/B')),
                    'div_yield': cls._clean_numeric(row.get('Div Yield'))
                }
                if record['symbol']:
                    records.append(record)
            return records

        for _, row in df.iterrows():
            record = {
                'date': trade_date,
                'symbol': str(row.get('SYMBOL', '')).strip(),
                'symbol_pe': cls._clean_numeric(row.get('SYMBOL P/E')),
                'adjusted_pe': cls._clean_numeric(row.get('ADJUSTED P/E')),
            }
            if record['symbol']:
                records.append(record)
        return records

    @classmethod
    def _map_india_vix(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        for _, row in df.iterrows():
            symbol = str(row.get('Index Name', '')).strip()
            if symbol != 'India VIX':
                continue

            row_date = parse_nse_date(row.get('Index Date'))
            record = {
                'date': row_date or trade_date,
                'open_value': cls._clean_numeric(row.get('Open Index Value')),
                'high_value': cls._clean_numeric(row.get('High Index Value')),
                'low_value': cls._clean_numeric(row.get('Low Index Value')),
                'close_value': cls._clean_numeric(row.get('Closing Index Value')),
                'points_change': cls._clean_numeric(row.get('Points Change')),
                'percent_change': cls._clean_numeric(row.get('Change(%)'))
            }
            records.append(record)
        return records

    @classmethod
    def _map_security_master(cls, df: pd.DataFrame) -> List[Dict]:
        records = []
        if 'SctySrs' in df.columns:
            # Only take EQ and F&O listed companies per user request
            df = df[df['SctySrs'].isin(['EQ', 'FO', 'F&O'])].copy()

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
        for _, row in df.iterrows():
            record = {
                'date': trade_date,
                'symbol': str(row.get('Symbol', '')).strip(),
                'expiry_date': parse_nse_date(row.get('Expiry Date')),
                'strike_price': cls._clean_numeric(row.get('Strike Price')),
                'option_type': str(row.get('Option Type', '')).strip(),
                'delta': cls._clean_numeric(row.get('Delta')),
            }
            if record['symbol']:
                records.append(record)
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
