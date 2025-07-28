from ib_insync import *
import pandas as pd
from datetime import datetime
import os

ib = IB()
ib.connect('127.0.0.1', 7496, clientId=99)

# === TRACKED SYMBOLS ===
symbols = ['IBKR', 'AVGO', 'TPG', 'RBC']
exchange = 'SMART'

# === LIVE PRICES + POSITIONS ===
print("\n📊 LIVE POSITIONS & PNL")
positions = ib.positions()
data = []
for p in positions:
    contract = Stock(p.contract.symbol, exchange, currency=p.contract.currency)
    try:
        ib.qualifyContracts(contract)
        market_data = ib.reqMktData(contract, '', False, False)
        ib.sleep(1)
        price = market_data.last if market_data.last is not None else 'DELAYED/UNAVAIL'
        pnl = p.position * market_data.last if market_data.last else 'N/A'
        ib.cancelMktData(contract)
    except:
        price, pnl = 'N/A', 'N/A'
    data.append({
        'Symbol': p.contract.symbol,
        'Currency': p.contract.currency,
        'Size': p.position,
        'Last Price': price,
        'Unrealized PnL': pnl
    })
df_pos = pd.DataFrame(data)
print(df_pos.to_string(index=False))

# === FX BALANCES ===
print("\n💱 FX CASH BALANCES")
fx_data = []
for item in ib.accountSummary():
    if item.tag == 'CashBalance':
        fx_data.append({'Currency': item.currency, 'Cash Balance': item.value})
df_fx = pd.DataFrame(fx_data)
print(df_fx.to_string(index=False))

# === TRADE LOGGER ===
def log_trade(symbol, action, size, entry, stop, target, notes=""):
    log_path = "trades.csv"
    trade = {
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Symbol": symbol,
        "Action": action,
        "Size": size,
        "Entry": entry,
        "Stop": stop,
        "Target": target,
        "Notes": notes
    }
    df_log = pd.DataFrame([trade])
    if os.path.exists(log_path):
        df_log.to_csv(log_path, mode='a', header=False, index=False)
    else:
        df_log.to_csv(log_path, index=False)
    print(f"📝 Logged trade: {symbol} {action} {size} @ {entry}")

# === ORDER LOGIC: IBKR Trigger Example ===
print("\n🧠 SMART MONEY TRIGGER")
trigger_price = 65.00
ibkr = Stock('IBKR', exchange, 'USD')
ib.qualifyContracts(ibkr)
data = ib.reqMktData(ibkr, '', False, False)
ib.sleep(1)
if data.last and data.last <= trigger_price:
    order = LimitOrder('BUY', 10, data.last)
    ib.placeOrder(ibkr, order)
    log_trade("IBKR", "BUY", 10, data.last, "manual", "swing target", "Auto-triggered")
    print(f"📥 Order placed: BUY 10 IBKR @ {data.last}")
else:
    print(f"IBKR is above {trigger_price} (Current: {data.last}) → no trade")

ib.disconnect()
