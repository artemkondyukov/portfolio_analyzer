import altair as alt
from copy import deepcopy
import json
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

API_URL = "https://api-invest.tinkoff.ru/openapi/"
TOKEN = open(".tinkoff_token", "r").read().strip()


@st.cache
def get_sector(ticker):
    try:
        return yf.Ticker(ticker).info["sector"]
    except (ValueError, IndexError):
        return "Other"


def get_price(figi, price_type="lastPrice"):
    response = requests.get(f"{API_URL}market/orderbook",
                            headers={"Authorization": f"Bearer {TOKEN}"},
                            params={"figi": figi,
                                    "depth": 1}
                            )
    return json.loads(response.content)["payload"][price_type]


class Currency:
    def __init__(self, **kwargs):
        self.currency = kwargs["currency"]
        self.balance = kwargs["balance"]

    def __repr__(self):
        return f"Currency: {self.currency} \n" \
               f"Balance: {self.balance} \n"


class Position:
    def __init__(self, **kwargs):
        self.ticker = kwargs["ticker"]
        self.figi = kwargs["figi"]
        self.currency = kwargs["averagePositionPrice"]["currency"]
        self.type = kwargs["instrumentType"]
        self.balance = kwargs["balance"]
        self.sector = kwargs.get("sector", None) or get_sector(self.ticker)
        self.price = kwargs.get("price", None) or get_price(self.figi)

    def __repr__(self):
        return f"Ticker: {self.ticker} \n" \
               f"FIGI: {self.figi} \n" \
               f"Currency: {self.currency} \n" \
               f"Type: {self.type} \n" \
               f"Balance: {self.balance} \n" \
               f"Sector: {self.sector} \n"


class Portfolio:
    def __init__(self, currencies, positions):
        self.currencies = currencies
        self.positions = positions

    def __repr__(self):
        return "CURRENCIES \n" +\
               "\n".join([repr(c) for c in self.currencies]) +\
               "\nPOSITIONS \n" +\
               "\n".join([repr(p) for p in self.positions])

    def to_table(self) -> pd.DataFrame:
        result = pd.DataFrame([p.__dict__ for p in self.positions])
        return result


def get_account_id(account_type="TinkoffIis") -> int:
    acc_response = requests.get(f"{API_URL}user/accounts",
                                headers={"Authorization": f"Bearer {TOKEN}"})

    accounts_dict = json.loads(acc_response.content.decode("utf-8"))["payload"]["accounts"]

    for account in accounts_dict:
        if account["brokerAccountType"] == account_type:
            return int(account["brokerAccountId"])

    raise ValueError(f"No account with type {account_type}!")


def get_portfolio(account_id) -> Portfolio:
    portfolio_response = requests.get(f"{API_URL}portfolio",
                                      headers={"Authorization": f"Bearer {TOKEN}"},
                                      params={"brokerAccountId": account_id}
                                      )
    payload_positions = json.loads(portfolio_response.content)["payload"]["positions"]

    currencies_response = requests.get(f"{API_URL}portfolio/currencies",
                                       headers={"Authorization": f"Bearer {TOKEN}"},
                                       params={"brokerAccountId": ACCOUNT_ID}
                                       )
    payload_currencies = json.loads(currencies_response.content)["payload"]["currencies"]
    currencies = [Currency(**c) for c in payload_currencies]
    positions = [Position(**p) for p in payload_positions if p["instrumentType"] != "Currency"]

    return Portfolio(currencies, positions)


ACCOUNT_ID = get_account_id()

source_table = get_portfolio(ACCOUNT_ID).to_table()
source_table.loc[:, "year"] = 2020
source_table.loc[:, "amount"] = source_table.price * source_table.balance
new_source_table = deepcopy(source_table)
new_source_table.year = 2021

st.write(source_table)

chart = alt.Chart(source_table.append(new_source_table)).mark_area().encode(
    x="year:T",
    y=alt.Y("sum(amount)", stack="normalize"),
    color="sector"
)

st.write(chart)
