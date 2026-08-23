import pytest
from datetime import date
from backend.ingest.dividend_matcher import find_best_bm_for_ca, MATCH_WINDOW_DAYS

class MockBM:
    def __init__(self, id, d, purpose, amount):
        self.id = id
        self.date = d
        self.purpose = purpose
        self.extracted_dividend_amount = amount

def test_coalindia_scenario():
    bm1 = MockBM(1, date(2026, 4, 27), "Recommend Final Dividend", 5.0)
    bm2 = MockBM(2, date(2026, 7, 15), "Declare Interim Dividend", 6.0)
    bms = [bm1, bm2]

    ca1 = {"dividend_type": "Final", "amount": 5.0, "ex_date_obj": date(2026, 7, 20)}
    ca2 = {"dividend_type": "Interim", "amount": 6.0, "ex_date_obj": date(2026, 7, 20)}

    matched_bm_ids = set()

    # Match Final CA
    best_bm_for_final = find_best_bm_for_ca(ca1, bms, matched_bm_ids)
    assert best_bm_for_final is not None
    assert best_bm_for_final.id == 1
    matched_bm_ids.add((best_bm_for_final.id, "Final"))

    # Match Interim CA
    best_bm_for_interim = find_best_bm_for_ca(ca2, bms, matched_bm_ids)
    assert best_bm_for_interim is not None
    assert best_bm_for_interim.id == 2

def test_one_bm_two_types():
    bm = MockBM(1, date(2026, 5, 10), "Final and Special Dividend", 10.0)
    bms = [bm]

    ca1 = {"dividend_type": "Final", "amount": 10.0, "ex_date_obj": date(2026, 5, 20)}
    ca2 = {"dividend_type": "Special", "amount": 10.0, "ex_date_obj": date(2026, 5, 20)}

    matched_bm_ids = set()
    best_bm1 = find_best_bm_for_ca(ca1, bms, matched_bm_ids)
    assert best_bm1.id == 1
    matched_bm_ids.add((best_bm1.id, "Final"))

    best_bm2 = find_best_bm_for_ca(ca2, bms, matched_bm_ids)
    assert best_bm2 is not None
    assert best_bm2.id == 1

def test_reject_cross_type_reuse():
    bm = MockBM(1, date(2026, 5, 10), "Final Dividend", 5.0)
    bms = [bm]
    ca = {"dividend_type": "Interim", "amount": 5.0, "ex_date_obj": date(2026, 5, 20)}

    matched = find_best_bm_for_ca(ca, bms, set())
    assert matched is None

def test_180_day_boundary():
    bm = MockBM(1, date(2026, 1, 1), "Final Dividend", 5.0)
    bms = [bm]
    ca = {"dividend_type": "Final", "amount": 5.0, "ex_date_obj": date(2026, 8, 1)} # > 180 days

    matched = find_best_bm_for_ca(ca, bms, set())
    assert matched is None

def test_bogus_amount_date_strip():
    from backend.ingest.text_utils import strip_date_fragments
    import re
    text = "Board Meeting to be held on 08-May-2023 to declare final dividend"
    cleaned = strip_date_fragments(text)
    # The date should be gone
    assert "08-May-2023" not in cleaned
    # Check amount extraction logic roughly
    div_matches = re.findall(r'(?:dividend|intdiv|findiv|special)[^\d]{0,25}?(?:\s+|-\s*|of\s+)(\d+(?:\.\d+)?)\b', cleaned, flags=re.IGNORECASE)
    assert len(div_matches) == 0

def test_is_valid_amount():
    from backend.ingest.text_utils import is_valid_dividend_amount
    assert not is_valid_dividend_amount("2024")
    assert not is_valid_dividend_amount("1998")
    assert is_valid_dividend_amount("5.50")
    assert is_valid_dividend_amount("8")
