
# NIFTY 50 Paper Trading Bot — Version 1

## What it does
- Starts with virtual capital (default ₹1,00,000)
- Reads NIFTY 50 historical CSV data
- Calculates EMA and RSI
- Generates BUY/HOLD/EXIT signals
- Simulates one-unit paper trades
- Uses configurable stop-loss and target
- Shows realized/unrealized P&L
- Lets you download trade history

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the Streamlit URL on your iPhone.

## CSV
The CSV needs:
- Date or Datetime
- Close

This version deliberately does NOT connect to a broker and cannot place real-money orders.
