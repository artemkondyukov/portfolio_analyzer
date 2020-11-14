import altair as alt
import pandas as pd
import streamlit as st

from operation import get_operations, get_exchange_rate
from portfolio import Currency, Portfolio, get_account_id


ACCOUNT_ID = get_account_id()
TOKEN = open(".tinkoff_token", "r").read().strip()
USD_RUB = get_exchange_rate("USD", TOKEN)

p = Portfolio([Currency(currency="USD", balance=0.),
               Currency(currency="RUB", balance=0.)],
              [])

operations = get_operations(ACCOUNT_ID, TOKEN)

dfs = []
new_p = p
for operation in operations:
    new_p = operation.perform(new_p)
    dfs.append(new_p.to_table())

    if "price" not in dfs[-1].columns:
        continue

    dfs[-1].loc[:, "date"] = [operation.datetime] * dfs[-1].shape[0]
    dfs[-1].loc[:, "amount"] = dfs[-1].price * dfs[-1].balance
    dfs[-1].loc[:, "exchange_rate"] = \
        (dfs[-1].currency == "USD") * USD_RUB + \
        (dfs[-1].currency == "RUB")
    dfs[-1].loc[:, "amount"] = dfs[-1].price * dfs[-1].balance * dfs[-1].exchange_rate

source = pd.concat(dfs)
chart = alt.Chart(source).mark_area().encode(
    x="date:T",
    y=alt.Y("sum(amount)", stack="normalize"),
    color="sector"
)

st.write(source)
st.write(chart)
