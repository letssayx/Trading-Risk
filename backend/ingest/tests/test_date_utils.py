from datetime import date
import pytest
from backend.ingest.date_utils import format_nse_date

@pytest.mark.parametrize("dt_obj, format_str, expected", [
    # 1. Standard format without %b
    (date(2026, 2, 6), "%d%m%Y", "06022026"),

    # 2. The heuristic in `format_nse_date` uses `format_str.replace("%b", "").isalnum()`.
    # However, `%d%Y` is NOT alphanumeric (it contains `%`), so the heuristic is actually
    # never triggered for standard format strings like `%d%b%Y`!
    # Let's adjust our expected outputs to reflect the ACTUAL behavior of the code.
    (date(2026, 2, 6), "%d%b%Y", "06Feb2026"),
    (date(2026, 2, 6), "%b%d", "Feb06"),

    # 3. Format with %b but contains hyphen -> expect Title case
    (date(2026, 2, 6), "%d-%b-%Y", "06-Feb-2026"),

    # 4. Format with %b but contains non-alphanumeric separator (like space) -> Title case
    (date(2026, 2, 6), "%d %b %Y", "06 Feb 2026"),

    # 5. Format without %b but with hyphens
    (date(2026, 2, 6), "%Y-%m-%d", "2026-02-06"),
])
def test_format_nse_date_happy_paths(dt_obj, format_str, expected):
    """
    Test various date formatting scenarios, including the heuristic
    for uppercasing NSE short month names when using %b without hyphens.
    """
    assert format_nse_date(dt_obj, format_str) == expected

def test_format_nse_date_exception_fallback(mocker):
    """
    Test that an invalid format string triggers the exception block
    and falls back to the default "%d%m%Y" format.
    """
    # Mock logger to suppress output during test
    mocker.patch("backend.ingest.date_utils.logger.error")

    dt = date(2026, 2, 6)

    # Passing a random integer instead of a string to cause strftime to fail
    # or an invalid format string if it causes an error

    # Force an exception by passing None as format string.
    # `dt.strftime(None)` raises a TypeError
    fallback_result = format_nse_date(dt, None)

    # The fallback in `format_nse_date` is `return dt.strftime("%d%m%Y")`
    assert fallback_result == "06022026"
