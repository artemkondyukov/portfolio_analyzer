from copy import deepcopy
from datetime import datetime
import json
from pytz import timezone
import requests

from portfolio import Position, Portfolio

API_URL = "https://api-invest.tinkoff.ru/openapi/"


def get_currency_by_figi(figi: str) -> str:
    if figi == "BBG0013HGFT4":
        return "USD"
    elif figi == "BBG0013HJJ31":
        return "EUR"
    raise ValueError(f"No currency with FIGI {figi}")


def get_exchange_rate(currency: str, token: str) -> float:
    if currency == "USD":
        figi = "BBG0013HGFT4"
    elif currency == "EUR":
        figi = "BBG0013HJJ31"
    else:
        raise ValueError(f"No currency {currency}")

    response = requests.get(f"{API_URL}market/orderbook",
                            headers={"Authorization": f"Bearer {token}"},
                            params={"figi": figi,
                                    "depth": 1}
                            )

    usd_rub_orderbook = json.loads(response.content)["payload"]
    return usd_rub_orderbook["lastPrice"]


def fix_iso_format(iso: str) -> str:
    if "." not in iso:
        return iso
    before_dot, after_dot = iso.split(".")
    before_plus, after_plus = after_dot.split("+")
    if len(before_plus) not in [3, 6]:
        before_plus += "0" * (3 - len(before_plus) % 3)
    return f"{before_dot}.{before_plus}+{after_plus}"


class Operation:
    def __init__(self, **kwargs):
        self.datetime: datetime = datetime.fromisoformat(fix_iso_format(kwargs["date"]))
        self.isMarginCall: bool = kwargs["isMarginCall"]
        self.payment: float = kwargs["payment"]
        self.currency: str = kwargs["currency"]
        self.status: str = kwargs["status"]
        self.id: str = kwargs["id"]

    def perform(self, portfolio: Portfolio) -> Portfolio:
        raise NotImplementedError


class CashFlow(Operation):
    def perform(self, portfolio: Portfolio) -> Portfolio:
        result = deepcopy(portfolio)

        for currency in result.currencies:
            if currency.currency == self.currency:
                currency.balance += self.payment

        return result


class BuySellCurrency(Operation):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.figi: str = kwargs["figi"]
        self.operation_currency: str = get_currency_by_figi(self.figi)
        self.quantity: int = kwargs["quantity"]
        self.quantity_executed: int = kwargs["quantityExecuted"]
        self.price: float = kwargs["price"]

    def perform(self, portfolio: Portfolio) -> Portfolio:
        result = deepcopy(portfolio)

        for currency in result.currencies:
            if currency.currency == self.currency:
                currency.balance += self.payment

        for currency in result.currencies:
            if currency.currency == self.operation_currency:
                currency.balance += self.quantity_executed

        return result


class BuySellAsset(Operation):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.figi: str = kwargs["figi"]
        self.quantity: int = kwargs["quantity"]
        self.quantity_executed: int = kwargs["quantityExecuted"]
        self.price: float = kwargs["price"]
        self.instrument_type: float = kwargs["instrumentType"]

    def __repr__(self):
        return f"Datetime: {self.datetime} \n" \
               f"FIGI: {self.figi} \n" \
               f"Currency: {self.currency} \n" \
               f"Payment: {self.payment} \n" \
               f"Quantity: {self.quantity_executed} \n"

    def perform(self, portfolio: Portfolio) -> Portfolio:
        result = deepcopy(portfolio)

        for currency in result.currencies:
            if currency.currency == self.currency:
                currency.balance += self.payment

        has_position = False
        for position in result.positions:
            if position.figi == self.figi:
                has_position = True
                if self.payment > 0:
                    position.balance -= self.quantity_executed
                else:
                    position.balance += self.quantity_executed
                break

        if not has_position:
            result.positions.append(Position(
                figi=self.figi,
                currency=self.currency,
                type=self.instrument_type,
                balance=self.quantity_executed,
            ))

        return result


class OperationFactory:
    @staticmethod
    def create_operation(operation_type, **kwargs):
        if operation_type in ["PayIn", "Coupon", "PartRepayment", "BrokerCommission", "Dividend"]:
            return CashFlow(**kwargs)
        elif operation_type in ["Sell", "Buy"]:
            if kwargs.get("instrumentType") == "Currency":
                return BuySellCurrency(**kwargs)
            else:
                return BuySellAsset(**kwargs)

        raise ValueError(f"Wrong operation_type: {operation_type}")


def get_operations(account_id: int, token: str) -> list:
    date_from = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone('Europe/Moscow'))
    date_to = datetime.now(tz=timezone('Europe/Moscow'))
    response = requests.get(f"{API_URL}operations",
                            headers={"Authorization": f"Bearer {token}"},
                            params={
                                "brokerAccountId": account_id,
                                "from": date_from.isoformat(),
                                "to": date_to.isoformat(),
                            }
                            )
    operations = []
    for operation in json.loads(response.content)["payload"]["operations"][::-1]:
        operation_type = operation["operationType"]
        operation = OperationFactory.create_operation(operation_type=operation_type, **operation)
        operations.append(operation)

    return operations
