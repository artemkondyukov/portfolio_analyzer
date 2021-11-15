import pytest
from portfolio_analyzer.aux import calculate_yield


def test_calculate_yield():
    res = calculate_yield([5], [20], 5.100955724302702)
    assert res == pytest.approx(0.44025, 1e-4)
    res = calculate_yield([5, 10, 40], [20, 6, 9], 55)
    assert res == pytest.approx(.0, 1e-4)
    res = calculate_yield([1, 2, 3, 4, 5], [20, 21, 22, 23, 24], 10)
    assert res < 0
    res = calculate_yield([5000, 3000, 1000], [360, 153, 5], 7056.95545014398)
    assert res == pytest.approx(-0.30593, 1e-5)
    res = calculate_yield([5000, 1000, -2000, -5000], [30, 50, 20, 10], 420.38569155645564)
    assert res == pytest.approx(36.7834, 1e-4)
