import pytest
from portfolio_analyzer.aux import calculate_yield


def test_calculate_yield():
    res = calculate_yield([5], [20], 5.100955724302702)
    assert res == pytest.approx(0.44025, 1e-4)
