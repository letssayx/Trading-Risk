"""Field mapping for all NSE file formats - Based on actual file headers"""
from typing import Dict, Any, List, Optional
import pandas as pd
import logging
from datetime import date
from backend.ingest.date_utils import parse_nse_date

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

        # UDIFF FO bhavcopy (Check first as it's more specific with XpryDt)
        if 'TckrSymb' in columns and 'FinInstrmTp' in columns and 'XpryDt' in columns:
            return {'type': 'fo_udiff', 'name': 'bhavcopy_fo'}

        # UDIFF CM bhavcopy
        if 'TckrSymb' in columns and 'SctySrs' in columns and 'TradDt' in columns:
            return {'type': 'cm_udiff', 'name': 'bhavcopy_eq'}

        # Old EQ bhavcopy
        if 'SYMBOL' in columns and 'SERIES' in columns and 'DATE1' in columns:
            return {'type': 'eq_old', 'name': 'bhavcopy_eq'}

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
        if 'Record Type' in columns or 'Name of Security' in columns:
            return {'type': 'mto', 'name': 'mto_delivery'}

        # MWPL Client
        if 'Underlying Stock' in columns and 'Client 1' in columns:
            return {'type': 'mwpl', 'name': 'mwpl_client_position'}

        # MWPL Raw check (if headers are in row 2)
        if len(df.columns) > 0 and "MWPL" in str(df.columns[0]):
             return {'type': 'mwpl', 'name': 'mwpl_client_position'}

        # P/E Ratio
        if 'SYMBOL' in columns and 'P/E' in columns: # Official often has 'P/E'
             return {'type': 'pe_ratio', 'name': 'pe_ratio'}
        if 'SYMBOL' in columns and 'SYMBOL P/E' in columns: # Older/Archive
            return {'type': 'pe_ratio', 'name': 'pe_ratio'}

        # Security Master (EQUITY_L)
        if 'SYMBOL' in columns and 'NAME OF COMPANY' in columns and ' ISIN NUMBER' in columns:
             return {'type': 'security_master_l', 'name': 'security_master'}
        # New Bhavcopy as Security Master fallback
        if 'TckrSymb' in columns and 'ISIN' in columns:
            return {'type': 'security_master', 'name': 'security_master'}

        # VaR Stats
        if 'Security VaR' in columns or 'Security Symbol' in columns and 'VaR Margin' in columns:
            return {'type': 'var_stats', 'name': 'var_stats'}

        # Contract Delta
        if 'Delta' in columns and 'Strike Price' in columns:
            return {'type': 'contract_delta', 'name': 'contract_delta'}

        # Margin Trading
        if 'Quantity Funded' in columns or 'Amount Funded' in columns:
            return {'type': 'margin_trading', 'name': 'margin_trading'}

        return {'type': 'unknown', 'name': 'unknown'}

    @classmethod
    def map_to_records(cls, df: pd.DataFrame, format_info: Dict, trade_date: Optional[date] = None) -> List[Dict]:
        """Map dataframe to database records based on format"""
        format_type = format_info['type']

        if format_type == 'cm_udiff':
            return cls._map_cm_udiff(df, trade_date)
        elif format_type == 'fo_udiff':
            return cls._map_fo_udiff(df)
        elif format_type == 'eq_old':
            return cls._map_eq_old(df)
        elif format_type == 'deals':
             target = format_info.get('target_table', 'bulk_deals')
             return cls._map_deals(df, target)
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
        elif format_type == 'pe_ratio':
            return cls._map_pe(df, trade_date)
        elif format_type == 'security_master':
            return cls._map_security_master(df)
        elif format_type == 'security_master_l':
            return cls._map_security_master_l(df)
        elif format_type == 'var_stats':
            return cls._map_var_stats(df, trade_date)
        elif format_type == 'contract_delta':
            return cls._map_contract_delta(df, trade_date)
        elif format_type == 'margin_trading':
            return cls._map_margin_trading(df, trade_date)

        return []

    # --- Mapping Implementations ---

    @classmethod
    def _map_cm_udiff(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        if 'SctySrs' in df.columns:
            df = df[df['SctySrs'] == 'EQ'].copy()

        for _, row in df.iterrows():
            record = {
                'symbol': str(row.get('TckrSymb', '')).strip(),
                'series': 'EQ',
                'trade_date': trade_date or parse_nse_date(row.get('TradDt')),
                'prev_close': cls._clean_numeric(row.get('PrvsClsgPric')),
                'open_price': cls._clean_numeric(row.get('OpnPric')),
                'high_price': cls._clean_numeric(row.get('HghPric')),
                'low_price': cls._clean_numeric(row.get('LwPric')),
                'last_price': cls._clean_numeric(row.get('LastPric')),
                'close_price': cls._clean_numeric(row.get('ClsPric')),
                'total_traded_qty': cls._clean_integer(row.get('TtlTradgVol')),
                'turnover_lacs': cls._clean_numeric(row.get('TtlTrfVal')),
                'no_of_trades': cls._clean_integer(row.get('TtlNbOfTxsExctd')),
            }
            if record['symbol']:
                records.append(record)
        return records

    @classmethod
    def _map_fo_udiff(cls, df: pd.DataFrame) -> List[Dict]:
        records = []
        for _, row in df.iterrows():
            record = {
                'ticker_symb': str(row.get('TckrSymb', '')).strip(),
                'instrument_type': str(row.get('FinInstrmTp', '')).strip(),
                'trade_date': parse_nse_date(row.get('TradDt')),
                'expiry_date': parse_nse_date(row.get('XpryDt')),
                'strike_price': cls._clean_numeric(row.get('StrkPric')),
                'option_type': str(row.get('OptnTp', '')).strip(),
                'instrument_name': str(row.get('FinInstrmNm', '')).strip(),
                'open_price': cls._clean_numeric(row.get('OpnPric')),
                'high_price': cls._clean_numeric(row.get('HghPric')),
                'low_price': cls._clean_numeric(row.get('LwPric')),
                'close_price': cls._clean_numeric(row.get('ClsPric')),
                'settle_price': cls._clean_numeric(row.get('SttlmPric')),
                'open_interest': cls._clean_integer(row.get('OpnIntrst')),
                'change_in_oi': cls._clean_integer(row.get('ChngInOpnIntrst')),
                'total_trading_vol': cls._clean_integer(row.get('TtlTradgVol')),
                'total_trf_val': cls._clean_numeric(row.get('TtlTrfVal')),
            }
            if record['ticker_symb']:
                records.append(record)
        return records

    @classmethod
    def _map_eq_old(cls, df: pd.DataFrame) -> List[Dict]:
        records = []
        if 'SERIES' in df.columns:
            df = df[df['SERIES'] == 'EQ'].copy()

        for _, row in df.iterrows():
            record = {
                'symbol': str(row.get('SYMBOL', '')).strip(),
                'series': 'EQ',
                'trade_date': parse_nse_date(row.get('DATE1')),
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
    def _map_deals(cls, df: pd.DataFrame, table_name: str) -> List[Dict]:
        records = []
        date_col = 'DATE' if 'DATE' in df.columns else 'Date'
        trade_date = None

        for _, row in df.iterrows():
            if date_col in row and trade_date is None:
                trade_date = parse_nse_date(row[date_col])

            record = {
                'date': trade_date,
                'symbol': str(row.get('SYMBOL', row.get('Symbol', ''))).strip(),
                'security_name': str(row.get('SECURITY NAME', row.get('Security Name', ''))).strip(),
                'client_name': str(row.get('CLIENT NAME', row.get('Client Name', ''))).strip(),
                'buy_sell': str(row.get('BUY/SELL', row.get('Buy/Sell', ''))).strip(),
                'quantity_traded': cls._clean_integer(row.get('QUANTITY TRADED', row.get('Quantity Traded'))),
                'trade_price': cls._clean_numeric(row.get('TRADE PRICE/ WEIGHTED. AVG. PRICE',
                                                          row.get('Trade Price / Wght. Avg. Price'))),
                'remarks': str(row.get('REMARKS', row.get('Remarks', ''))).strip(),
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
        # Find the start of data (skip header rows)
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

            # Check if this is an instrument header
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
        for _, row in df.iterrows():
            record = {
                'trade_date': parse_nse_date(row.get('Date')),
                'symbol': str(row.get('Symbol', '')).strip(),
                'underlying_close_price': cls._clean_numeric(row.get('Underlying Close Price (A)')),
                'underlying_annualised_vol': cls._clean_numeric(row.get('Underlying Annualised Volatility (F)')),
                'futures_close_price': cls._clean_numeric(row.get('Futures Close Price (G)')),
                'futures_annualised_vol': cls._clean_numeric(row.get('Futures Annualised Volatility (L)')),
                'applicable_daily_vol': cls._clean_numeric(row.get('Applicable Daily Volatility (M)')),
                'applicable_annualised_vol': cls._clean_numeric(row.get('Applicable Annualised Volatility (N)')),
            }
            if record['symbol']:
                records.append(record)
        return records

    @classmethod
    def _map_mto(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        for _, row in df.iterrows():
            # Skip header rows often found in DAT files
            if str(row.iloc[0]).strip() in ['Record Type', '20']:
                continue

            # MTO DAT format usually: Record Type, Sr No, Name of Security, Quantity Traded, Deliverable Quantity, % Deliverable
            # NSELib tries to parse it into CSV.

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

        # Header already handled in NSELib most likely, but check
        if 'Client 1' not in df.columns:
             # Try to find header row again if not found by NSELib
             pass

        for _, row in df.iterrows():
            underlying = str(row.get('Underlying Stock', '')).strip()
            if not underlying or underlying == 'nan':
                continue

            for i in range(1, 16):
                client_col = f'Client {i}'
                if client_col in row and pd.notna(row[client_col]):
                    records.append({
                        'date': trade_date,
                        'underlying_stock': underlying,
                        'client_position_num': i,
                        'position_pct': cls._clean_numeric(row[client_col]),
                    })
        return records

    @classmethod
    def _map_pe(cls, df: pd.DataFrame, trade_date: Optional[date]) -> List[Dict]:
        records = []
        for _, row in df.iterrows():
            record = {
                'date': trade_date,
                'symbol': str(row.get('SYMBOL', '')).strip(),
                'symbol_pe': cls._clean_numeric(row.get('P/E', row.get('SYMBOL P/E'))),
                'sector_pe': cls._clean_numeric(row.get('Sectoral Index P/E', row.get('SECTORAL INDEX P/E'))),
                # Note: 'ADJUSTED P/E' often not in recent files, but check
                'adjusted_pe': cls._clean_numeric(row.get('ADJUSTED P/E')),
            }
            if record['symbol']:
                records.append(record)
        return records

    @classmethod
    def _map_security_master_l(cls, df: pd.DataFrame) -> List[Dict]:
        """Maps EQUITY_L.csv format"""
        records = []
        for _, row in df.iterrows():
            record = {
                'fin_instrm_id': str(row.get('ISIN NUMBER', '')).strip(), # Use ISIN as ID if ID missing? Or Ticker?
                # DB expects fin_instrm_id. Often in Bhavcopy it's a number.
                # In EQUITY_L, we have SYMBOL, NAME, SERIES, ISIN.
                # If we lack FinInstrmId, we might need to map differently or allow nullable?
                # But 'nse_models.SecurityMaster' defines 'fin_instrm_id' as PK.
                # If we don't have it, we can't insert into that specific table correctly unless we fake it or use ISIN.
                # Let's use ISIN as key for now if that's what we have.
                'ticker_symb': str(row.get('SYMBOL', '')).strip(),
                'security_series': str(row.get(' SERIES', row.get('SERIES', ''))).strip(),
                'instrument_name': str(row.get('NAME OF COMPANY', '')).strip(),
                'isin': str(row.get(' ISIN NUMBER', row.get('ISIN NUMBER', ''))).strip(),
                'listed_date': parse_nse_date(row.get(' DATE OF LISTING', row.get('DATE OF LISTING'))),
                'status': 'Active' # Implicit
            }
            # For FinInstrmId, if we don't have it, we use ISIN?
            if not record['fin_instrm_id']:
                 record['fin_instrm_id'] = record['isin']

            if record['ticker_symb']:
                records.append(record)
        return records

    @classmethod
    def _map_security_master(cls, df: pd.DataFrame) -> List[Dict]:
        records = []
        if 'SctySrs' in df.columns:
            df = df[df['SctySrs'] == 'EQ'].copy()

        for _, row in df.iterrows():
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
                'additional_info': row.get('AddtlInf', ''),
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
