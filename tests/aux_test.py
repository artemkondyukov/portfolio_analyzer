import pytest
from portfolio_analyzer.aux import calculate_yield


def test_calculate_yield():
    res = calculate_yield([5], [20], 5.100955724302702)
    assert res == pytest.approx(0.44025, 1e-4)
    res = calculate_yield([5, 10, 40], [20, 6, 9], 55)
    assert res == pytest.approx(.0, 1e-4)
    res = calculate_yield([1, 2, 3, 4, 5], [20, 21, 22, 23, 24], 10)
    assert res < 0
