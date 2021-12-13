import numpy as np
import pandas as pd
from typing import Union, List


def calculate_yield(amounts: List[float], days: List[int], current_amount: float) -> float:
    """
      Calculates annual percentage yield (APY) of an investor using the info about their PIA pay-ins.

      :param amounts: amounts of pay-in transactions
      :param days: periods of time (in days) after the pay-in (or withdrawal) transaction till now
      :param current_amount: current amount on a personal investment account
      :return: approximate annual percentage yield (APY)
      """
    df = pd.DataFrame(list(zip(amounts, days)),
                      columns=['amounts', 'days']).sort_values('days', ascending=False)

    # generating polynomial coefficients for the "daily rate" calculation
    # polynomial: SUM of (amount * (rate ** days_of_holding)), where rate is 1 + "daily percent"
    max_days = max(df.days)
    coeffs = np.zeros(max_days + 1)
    for _, rows in df.iterrows():
        coeffs[max_days - int((rows['days']))] = rows['amounts']
    coeffs[-1] = (-1) * current_amount

    # calculating roots of a polynomial
    roots = np.roots(coeffs)
    # leaving only real numbers
    real_roots = roots.real[abs(roots.imag) < 1e-5]
    # only positive real numbers
    pos_real_roots = real_roots[real_roots > 0.]
    # here's a tricky part; in fact there's still no proof of the solution uniqueness =/
    # so we just return the biggest daily percent...
    rate = sorted(pos_real_roots, reverse=True)

    # find an annual percentage yield
    annual_percentage_yield = -1. + rate[0] ** 365
    return annual_percentage_yield
