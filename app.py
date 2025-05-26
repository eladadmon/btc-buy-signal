import streamlit as st
import pandas as pd
import numpy as np
import requests
import datetime
import matplotlib.pyplot as plt

# Fetch real BTC price data from Binance (last 100 hours)
def get_binance_data():
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "limit": 100
    }
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["close"] = df["close"].astype(float)
    df["timestamp"] = pd.to_datetime(df["open_time"], unit='ms')
    df.set_index("timestamp", inplace=True)
    return df[["close"]]

# Calculate indicators
def calculate_indicators(df):
    price_series = df["close"]
    delta = price_series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    ema_12 = price_series.ewm(span=12, adjust=False).mean()
    ema_26 = price_series.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    sma_50 = price_series.rolling(window=50).mean()

    df["RSI"] = rsi
    df["MACD"] = macd
    df["MACD_Signal"] = macd_signal
    df["SMA_50"] = sma_50
    return df

# Load and process data
data = get_binance_data()

# Check for empty data
if data.empty:
    st.error("❌ No data retrieved from Binance. Please try again later.")
    st.stop()

# Continue with indicators
data = calculate_indicators(data)
latest = data.iloc[-1]
prev = data.iloc[-2]

buy_signal = (
    (latest['RSI'] < 30) and
    (prev['MACD'] < prev['MACD_Signal']) and
    (latest['MACD'] > latest['MACD_Signal']) and
    (latest['close'] > latest['SMA_50'])
)

# Streamlit UI
st.title("Bitcoin Buy Signal Dashboard")

st.subheader("Latest BTC Price")
st.metric(label="Price (USD)", value=f"${latest['close']:,.2f}")

st.subheader("Technical Indicators")
st.write(f"RSI: {latest['RSI']:.2f}")
st.write(f"MACD: {latest['MACD']:.2f}")
st.write(f"MACD Signal: {latest['MACD_Signal']:.2f}")
st.write(f"50-period SMA: ${latest['SMA_50']:,.2f}")

if buy_signal:
    st.success("✅ BUY SIGNAL TRIGGERED")
else:
    st.info("No buy signal at the moment.")

# Chart
st.subheader("BTC Price & Buy Signal Chart")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(data["close"], label='BTC Price')
ax.plot(data["SMA_50"], label='50-period SMA', linestyle='--')
ax.set_title("Price vs SMA")
ax.legend()
st.pyplot(fig)

st.caption("Live data pulled from Binance API (BTC/USDT, hourly candles).")

