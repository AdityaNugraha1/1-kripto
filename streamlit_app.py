import streamlit as st
import pandas as pd
import requests
import ta
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Ultra Real-Time Scalping Bot", layout="wide")
st.title("⚡️ Ultra Real-Time Scalping Crypto Bot (Sinyal TP/SL Dinamis)")

# User Input
symbol = st.text_input("Pair (BTCUSDT, ETHUSDT, dst):", value="BTCUSDT").upper()
interval = "1m"
n_candles = 50
refresh_rate = st.slider("Frekuensi Update Otomatis (detik)", 2, 60, 5)

# Unique key for each refresh
refresh_count = st_autorefresh(interval=refresh_rate*1000, key="datarefresh")

# --- Function to fetch OHLCV data from Binance ---
def fetch_ohlc(symbol, interval="1m", limit=50):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        data = requests.get(url, timeout=8).json()
        # Handle error response from Binance
        if isinstance(data, dict) and data.get("code"):
            return None
        if not data or len(data) < 3:
            return None
        df = pd.DataFrame(data, columns=[
            'open_time','open','high','low','close','volume',
            'close_time','qav','trades','taker_base_vol','taker_quote_vol','ignore'
        ])
        df[['open','high','low','close','volume']] = df[['open','high','low','close','volume']].astype(float)
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        return df
    except Exception:
        return None

# --- Signal Logic for Ultra-Scalping ---
def realtime_scalping_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    entry = last['close']
    # Sinyal: arah candle terakhir
    if last['close'] > prev['close']:
        signal = "LONG"
    else:
        signal = "SHORT"

    # TP/SL ultra kecil dari ATR 5m
    atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=5).average_true_range().iloc[-1]
    min_pct = 0.0008   # 0.08%
    max_pct = 0.003    # 0.3%
    tp_range = min(max(atr, entry * min_pct), entry * max_pct)
    sl_range = min(max(atr * 0.7, entry * min_pct), entry * max_pct)

    if signal == "LONG":
        tp = entry + tp_range
        sl = entry - sl_range
    else:
        tp = entry - tp_range
        sl = entry + sl_range

    return signal, entry, tp, sl, atr

# --- MAIN OUTPUT ---
try:
    df = fetch_ohlc(symbol, interval=interval, limit=n_candles)
    if df is None or len(df) < 3:
        st.warning("⚠️ Data Binance tidak cukup (pair mungkin salah/baru, koneksi lambat, atau simbol tidak support interval ini).")
    else:
        signal, entry, tp, sl, atr = realtime_scalping_signal(df)

        # Plotly Chart, key selalu unik
        fig = go.Figure([
            go.Candlestick(
                x=df['open_time'], open=df['open'], high=df['high'],
                low=df['low'], close=df['close'], name="Price"
            ),
        ])
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{refresh_count}")

        # Output Sinyal
        st.markdown(f"""
        ### 🚦 Sinyal Scalping Real-Time [{symbol}]
        - **Sinyal:** `{signal}`
        - **Entry:** `{entry:.4f}`
        - **Take Profit (TP):** `{tp:.4f}`
        - **Stop Loss (SL):** `{sl:.4f}`
        - **ATR 5m:** `{atr:.6f}`
        - **Update:** {pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d %H:%M:%S')} UTC
        """)

        # Table 5 candle terakhir, key selalu unik
        st.dataframe(df.tail(5)[['open_time','close','high','low','volume']], use_container_width=True, key=f"table_{refresh_count}")

except Exception as e:
    st.error(f"Error: {e}")
