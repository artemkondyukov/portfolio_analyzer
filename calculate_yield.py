from datetime import datetime
import numpy as np
from pytz import timezone
from scipy.optimize import minimize

from operation import Operation, PayIn


def calculate_yield(operations: [Operation], current_amount):
    amounts, dates = zip(
        *[
            (operation.payment, operation.datetime)
            for operation in operations
            if operation.__class__ == PayIn
        ]
    )

    def loss_function(rate):
        cash_flow = [
            amount * (rate ** (datetime.now(tz=timezone('Europe/Moscow')) - date).days)
            for amount, date in
            zip(amounts, dates)
        ]
        return np.power(sum(cash_flow) - current_amount, 2)

    opt_res = minimize(loss_function, np.array([1.]))

    return -1 + opt_res.x ** 365
