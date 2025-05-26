import streamlit as st
import pandas as pd
import numpy as np
import ccxt
import matplotlib.pyplot as plt
import feedparser

# Fetch BTC/USD data using ccxt from Coinbase
def get_ccxt_coinbase_data():
    coinbase = ccxt.coinbase()
    ohlcv = coinbase.fetch_ohlcv('BTC/USD', timeframe='30m', limit=100)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df[["close", "volume"]]

# Fetch order book depth data
def get_order_book_summary():
    coinbase = ccxt.coinbase()
    order_book = coinbase.fetch_order_book('BTC/USD')
    bids = order_book['bids']
    asks = order_book['asks']

    total_bid_volume = sum([bid[1] for bid in bids])
    total_ask_volume = sum([ask[1] for ask in asks])
    total_volume = total_bid_volume + total_ask_volume

    buy_pressure = (total_bid_volume / total_volume) * 100 if total_volume > 0 else 0
    sell_pressure = 100 - buy_pressure

    return total_bid_volume, total_ask_volume, buy_pressure, sell_pressure

# Calculate indicators
def calculate_indicators(df):
    price = df["close"]
    volume = df["volume"]
    delta = price.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    ema_12 = price.ewm(span=12, adjust=False).mean()
    ema_26 = price.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    sma_50 = price.rolling(window=50).mean()

    obv = (np.sign(price.diff()) * volume).fillna(0).cumsum()

    df["RSI"] = rsi
    df["MACD"] = macd
    df["MACD_Signal"] = macd_signal
    df["SMA_50"] = sma_50
    df["OBV"] = obv
    return df

# Load and process data
data = get_ccxt_coinbase_data()

# Check for empty data
if data.empty:
    st.error("❌ No data retrieved from Coinbase via ccxt. Please try again later.")
    st.stop()

# Calculate indicators
data = calculate_indicators(data)
latest = data.iloc[-1]
prev = data.iloc[-2]

# Determine buy signal components
rsi_trigger = latest['RSI'] < 30
macd_trigger = prev['MACD'] < prev['MACD_Signal'] and latest['MACD'] > latest['MACD_Signal']
sma_trigger = latest['close'] > latest['SMA_50']
obv_trend = data['OBV'].iloc[-1] > data['OBV'].iloc[-10]  # simple OBV uptrend check

# Confidence scoring
score = 0
if rsi_trigger: score += 40
if macd_trigger: score += 30
if sma_trigger: score += 20
if obv_trend: score += 10

buy_signal = score >= 90

# Streamlit UI
st.title("Bitcoin Buy Signal Dashboard")

st.subheader("Latest BTC Price")
st.metric(label="Price (USD)", value=f"${latest['close']:,.2f}")

st.subheader("Technical Indicators")
st.write(f"RSI: {latest['RSI']:.2f}")
st.write(f"MACD: {latest['MACD']:.2f}")
st.write(f"MACD Signal: {latest['MACD_Signal']:.2f}")
st.write(f"50-period SMA: ${latest['SMA_50']:,.2f}")
st.write(f"OBV: {latest['OBV']:,.0f}")

st.subheader("Buy Signal Confidence Score")
st.metric(label="Confidence Score", value=f"{score}%")

if buy_signal:
    st.success("✅ BUY SIGNAL TRIGGERED")
else:
    st.info("No buy signal at the moment.")

# Market depth summary
st.subheader("Market Depth Snapshot")
bid_vol, ask_vol, buy_pct, sell_pct = get_order_book_summary()
st.write(f"**Buy Volume (Bids):** {bid_vol:.2f} BTC")
st.write(f"**Sell Volume (Asks):** {ask_vol:.2f} BTC")
st.write(f"**Buy Pressure:** {buy_pct:.2f}%")
st.write(f"**Sell Pressure:** {sell_pct:.2f}%")

# Chart
st.subheader("BTC Price & Buy Signal Chart")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(data["close"], label='BTC Price')
ax.plot(data["SMA_50"], label='50-period SMA', linestyle='--')
ax.set_title("Price vs SMA")
ax.legend()
st.pyplot(fig)

# Live News Feed
st.subheader("📰 Latest Bitcoin News")
feed = feedparser.parse("https://coindesk.com/arc/outboundfeeds/rss/?outputType=xml")
news_items = feed.entries[:5]
for item in news_items:
    st.markdown(f"**[{item.title}]({item.link})**\n- {item.published}")

st.caption("Live BTC/USD data from Coinbase via ccxt (30-minute candles) with market depth, OBV, signal confidence scoring, and Bitcoin news.")
