from backend.risk.measures.var import calculate_parametric_var
from backend.analysis.scanners.smart_money import BlockTradeScanner
from backend.data.mock import MockProvider

def verify_institutional_modules():
    print("Verifying Institutional Modules...")

    # 1. VaR Check
    var = calculate_parametric_var(1000000, 0.02, 0.99)
    print(f"VaR (1M, 2% vol, 99%): {var}")
    assert var > 0

    # 2. Smart Money Scanner
    scanner = BlockTradeScanner()
    tick = {"volume": 5000}
    res = scanner.scan(tick, avg_volume=1000)
    print(f"Block Trade Signal: {res}")
    assert res['signal'] == "BLOCK_TRADE"

    # 3. Mock Provider
    prov = MockProvider()
    data = prov.get_option_chain("NIFTY", "NOW")
    print(f"Mock Data Timestamp: {data['timestamp']}")
    assert data['timestamp'] is not None

    print("\nInstitutional Verification Successful.")

if __name__ == "__main__":
    verify_institutional_modules()
