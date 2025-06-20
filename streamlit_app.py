import streamlit as st
import pandas as pd
import requests
import ta
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=1800*1000, key="refresh")

st.set_page_config(page_title="Ultra-Scalping Bot 30M", layout="wide")
st.title("🤖 Ultra Scalping Bot 30 Menit — **Profit Kecil, Cepat, Tidak Di-Hold**")

symbol = st.text_input("Pair (BTCUSDT, ETHUSDT, dst):", value="BTCUSDT").upper()

def fetch_ohlc(symbol, interval="30m", limit=3):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=[
        'open_time','open','high','low','close','volume',
        'close_time','qav','trades','taker_base_vol','taker_quote_vol','ignore'
    ])
    df[['open','high','low','close','volume']] = df[['open','high','low','close','volume']].astype(float)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    return df

def scalping_signal_and_tp_sl(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    entry = last['close']

    # Penentuan arah: candle terakhir bullish/bearish (atau bisa tambah indikator lain)
    if last['close'] > prev['close']:
        signal = "LONG"
    else:
        signal = "SHORT"

    # TP/SL dinamis berdasarkan ATR/volatilitas dua candle terakhir (ultra scalping)
    high2 = max(last['high'], prev['high'])
    low2 = min(last['low'], prev['low'])
    atr2 = high2 - low2

    # Target profit dan stop loss ultra kecil, tidak nunggu target jauh
    min_pct = 0.001   # 0.1% profit
    max_pct = 0.003   # 0.3% profit
    tp_range = min(max(atr2 * 0.5, entry * min_pct), entry * max_pct)
    sl_range = min(max(atr2 * 0.3, entry * min_pct), entry * max_pct)

    if signal == "LONG":
        tp = entry + tp_range
        sl = entry - sl_range
    else:
        tp = entry - tp_range
        sl = entry + sl_range

    return signal, entry, tp, sl, atr2

if symbol:
    try:
        df = fetch_ohlc(symbol)
        signal, entry, tp, sl, atr2 = scalping_signal_and_tp_sl(df)

        fig = go.Figure([
            go.Candlestick(x=df['open_time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price"),
        ])
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"### 🔔 Sinyal Scalping Ultra-Pendek (30m) **{symbol}**")
        st.write(f"**Sinyal:** `{signal}` (berdasar arah candle 30 menit terakhir)")
        st.write(f"**Entry:** `{entry:.4f}`")
        st.write(f"**Take Profit (TP):** `{tp:.4f}` (~0.1-0.3%/ATR dua candle terakhir)")
        st.write(f"**Stop Loss (SL):** `{sl:.4f}` (~0.1-0.3%/ATR dua candle terakhir)")
        st.write(f"**ATR dua candle terakhir:** `{atr2:.6f}` (indikasi volatilitas)")

        st.markdown("""
        **Cara Kerja:**
        - Bot selalu entry tiap 30 menit.
        - Profit/SL kecil, posisi close sebelum candle berikut.
        - Bot tidak pernah "hold", langsung exit begitu target TP/SL tersentuh, siap entry baru di periode berikut.
        """)

        st.dataframe(df)

    except Exception as e:
        st.error(f"Error: {e}")
