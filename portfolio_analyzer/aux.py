import numpy as np
from scipy.optimize import minimize


def calculate_yield(amounts, days, current_amount):
    """
    Calculates annual percentage yield (APY) of an investor using the info about their PIA pay-ins.

    :param amounts: amounts of pay-in transactions
    :param days: periods of time (in days) after the pay-in transaction till now
    :param current_amount: current amount on a personal investment account
    :return: approximate annual percentage yield (APY)
    """
    def loss_function(rate):
        cash_flow = [
            # resulting sum
            amount * (rate ** days_of_holding)
            for amount, days_of_holding in
            zip(amounts, days)
        ]
        return np.power(sum(cash_flow) - current_amount, 2)

    # find a "daily" percentage yield
    opt_daily_percentage = minimize(loss_function, np.array([1.]),
                                    method='Powell', options={'xtol': 1e-30, 'ftol': 1e-30})
    # find an annual percentage yield
    APY = -1. + np.power(opt_daily_percentage.x, 365)
    return APY[0]
