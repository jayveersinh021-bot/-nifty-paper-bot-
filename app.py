
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="NIFTY 50 Paper Bot", page_icon="📈", layout="wide")

st.title("📈 NIFTY 50 AI-Style Paper Trading Bot")
st.caption("Paper trading only — no real orders are placed.")

# -----------------------------
# Settings
# -----------------------------
with st.sidebar:
    st.header("Bot Settings")
    capital = st.number_input("Virtual capital (₹)", min_value=10000, value=100000, step=10000)
    fast = st.slider("Fast EMA", 5, 50, 9)
    slow = st.slider("Slow EMA", 20, 200, 21)
    rsi_period = st.slider("RSI period", 5, 30, 14)
    stop_loss_pct = st.number_input("Stop loss %", 0.1, 10.0, 0.7, 0.1)
    target_pct = st.number_input("Target %", 0.1, 20.0, 1.4, 0.1)

st.info("For Version 1, upload a NIFTY 50 CSV containing Date/Datetime and Close columns. This keeps the bot fully paper-trading and avoids broker credentials.")

uploaded = st.file_uploader("Upload NIFTY 50 historical CSV", type=["csv"])

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

if uploaded:
    df = pd.read_csv(uploaded)
    cols = {c.lower().strip(): c for c in df.columns}

    date_col = next((cols[c] for c in ["datetime", "date", "timestamp"] if c in cols), None)
    close_col = next((cols[c] for c in ["close", "closing price"] if c in cols), None)

    if not close_col:
        st.error("CSV માં 'Close' column હોવો જરૂરી છે.")
        st.stop()

    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.sort_values(date_col)

    df[close_col] = pd.to_numeric(df[close_col], errors="coerce")
    df = df.dropna(subset=[close_col]).copy()
    df["Close"] = df[close_col]

    df["EMA_fast"] = df["Close"].ewm(span=fast, adjust=False).mean()
    df["EMA_slow"] = df["Close"].ewm(span=slow, adjust=False).mean()
    df["RSI"] = rsi(df["Close"], rsi_period)

    # Simple rule-based signal:
    # BUY when fast EMA crosses above slow EMA and RSI >= 50
    # SELL/EXIT when fast EMA crosses below slow EMA or RSI < 45
    df["signal"] = "HOLD"
    cross_up = (df["EMA_fast"] > df["EMA_slow"]) & (df["EMA_fast"].shift(1) <= df["EMA_slow"].shift(1))
    cross_down = (df["EMA_fast"] < df["EMA_slow"]) & (df["EMA_fast"].shift(1) >= df["EMA_slow"].shift(1))
    df.loc[cross_up & (df["RSI"] >= 50), "signal"] = "BUY"
    df.loc[cross_down | (df["RSI"] < 45), "signal"] = "EXIT"

    # Paper backtest: one unit of NIFTY index exposure at a time.
    cash = float(capital)
    position = 0.0
    entry = None
    trades = []

    for i, row in df.iterrows():
        price = float(row["Close"])
        sig = row["signal"]

        if position == 0 and sig == "BUY":
            position = 1.0
            entry = price
            trades.append({
                "Date": row[date_col] if date_col else i,
                "Action": "BUY",
                "Price": price,
                "Reason": "EMA cross + RSI"
            })
        elif position == 1 and entry is not None:
            sl = entry * (1 - stop_loss_pct/100)
            tp = entry * (1 + target_pct/100)
            if price <= sl or price >= tp or sig == "EXIT":
                pnl = price - entry
                cash += pnl
                trades.append({
                    "Date": row[date_col] if date_col else i,
                    "Action": "EXIT",
                    "Price": price,
                    "Reason": "SL/Target/Signal",
                    "PnL": pnl
                })
                position = 0.0
                entry = None

    if position == 1 and entry is not None:
        last_price = float(df["Close"].iloc[-1])
        unrealized = last_price - entry
    else:
        unrealized = 0.0

    trade_df = pd.DataFrame(trades)
    realized = trade_df["PnL"].sum() if "PnL" in trade_df else 0.0
    total_pnl = realized + unrealized

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Virtual Capital", f"₹{capital:,.0f}")
    c2.metric("Realized P&L", f"₹{realized:,.2f}")
    c3.metric("Unrealized P&L", f"₹{unrealized:,.2f}")
    c4.metric("Total P&L", f"₹{total_pnl:,.2f}")

    st.subheader("Price & indicators")
    chart = df.set_index(date_col)["Close"] if date_col else df["Close"]
    st.line_chart(pd.DataFrame({
        "NIFTY Close": chart,
        "Fast EMA": df.set_index(date_col)["EMA_fast"] if date_col else df["EMA_fast"],
        "Slow EMA": df.set_index(date_col)["EMA_slow"] if date_col else df["EMA_slow"],
    }))

    st.subheader("Latest signal")
    latest = df.iloc[-1]
    st.write({
        "Close": round(float(latest["Close"]), 2),
        "RSI": round(float(latest["RSI"]), 2),
        "Signal": latest["signal"]
    })

    st.subheader("Paper trade history")
    if not trade_df.empty:
        st.dataframe(trade_df, use_container_width=True)
    else:
        st.write("No trades generated for this dataset.")

    st.download_button(
        "Download trade history CSV",
        trade_df.to_csv(index=False).encode("utf-8"),
        "nifty_paper_trades.csv",
        "text/csv"
    )
else:
    st.write("Upload CSV to run the paper-trading backtest.")
    st.markdown("""
### CSV format
Your file should contain at least:
- `Date` or `Datetime`
- `Close`

Example:

```csv
Date,Close
2026-01-01,26000
2026-01-02,26120
```

### Important
This is a learning/backtesting bot, not financial advice. The strategy is deliberately simple and does not guarantee profits.
""")
