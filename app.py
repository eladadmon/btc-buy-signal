import streamlit as st
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt

# Simulated BTC data
days = 100
np.random.seed(42)
price = np.cumsum(np.random.randn(days) * 200 + 50000)
dates = pd.date_range(end=datetime.datetime.now(), periods=days)

# Calculate indicators
price_series = pd.Series(price, index=dates)
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

# Buy signal logic
latest = price_series.index[-1]
prev = price_series.index[-2]
buy_signal = (
    (rsi[latest] < 30) and
    (macd[prev] < macd_signal[prev]) and
    (macd[latest] > macd_signal[latest]) and
    (price_series[latest] > sma_50[latest])
)

# Streamlit UI
st.title("Bitcoin Buy Signal Dashboard")

st.subheader("Latest BTC Price")
st.metric(label="Price (USD)", value=f"${price_series[latest]:,.2f}")

st.subheader("Technical Indicators")
st.write(f"RSI: {rsi[latest]:.2f}")
st.write(f"MACD: {macd[latest]:.2f}")
st.write(f"MACD Signal: {macd_signal[latest]:.2f}")
st.write(f"50-day SMA: ${sma_50[latest]:,.2f}")

if buy_signal:
    st.success("✅ BUY SIGNAL TRIGGERED")
else:
    st.info("No buy signal at the moment.")

# Chart
st.subheader("BTC Price & Buy Signal Chart")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(price_series, label='BTC Price')
ax.plot(sma_50, label='50-day SMA', linestyle='--')
ax.set_title("Price vs SMA")
ax.legend()
st.pyplot(fig)

st.caption("Note: This demo uses simulated data. Connect to Binance or Coinbase for real-time prices.")
