import yfinance as yf
import pandas as pd
import ta
import requests
from datetime import datetime

# 🔑 TELEGRAM
BOT_TOKEN = "8550191978:AAEo2HeVwMBU9C4k0ZpT6j0K5SK4bXXg0NU"
CHAT_ID = "1160483967"

def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# 🔗 OPTION CHAIN FETCH
def get_option_chain(index):
    if index == "NIFTY":
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    else:
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY"

    headers = {"User-Agent": "Mozilla/5.0"}
    s = requests.Session()
    s.get("https://www.nseindia.com", headers=headers)
    res = s.get(url, headers=headers)
    return res.json()

# 📊 OI ANALYSIS
def analyze_oi(data):
    ce_oi = pe_oi = 0

    for item in data['records']['data']:
        if 'CE' in item and 'PE' in item:
            ce_oi += item['CE']['openInterest']
            pe_oi += item['PE']['openInterest']

    pcr = pe_oi / ce_oi if ce_oi != 0 else 0

    if pcr > 1.2:
        return "BULLISH", pcr
    elif pcr < 0.8:
        return "BEARISH", pcr
    return "NEUTRAL", pcr

# 🎯 OI WALLS
def get_oi_walls(data):
    max_ce = max_pe = 0
    ce_strike = pe_strike = 0

    for item in data['records']['data']:
        if 'CE' in item and item['CE']['openInterest'] > max_ce:
            max_ce = item['CE']['openInterest']
            ce_strike = item['strikePrice']

        if 'PE' in item and item['PE']['openInterest'] > max_pe:
            max_pe = item['PE']['openInterest']
            pe_strike = item['strikePrice']

    return ce_strike, pe_strike

# 🧠 GAMMA SIGNAL
def gamma_signal(price, ce_wall, pe_wall, pcr):
    if price > ce_wall and pcr > 1:
        return "BUY"
    elif price < pe_wall and pcr < 1:
        return "SELL"
    return None

# 📈 HTF TREND
def htf_trend(df):
    df['ema50'] = ta.trend.ema_indicator(df['Close'], window=50)
    df['ema200'] = ta.trend.ema_indicator(df['Close'], window=200)

    if df['ema50'].iloc[-1] > df['ema200'].iloc[-1]:
        return "BUY"
    elif df['ema50'].iloc[-1] < df['ema200'].iloc[-1]:
        return "SELL"
    return None

# 📉 ENTRY
def entry_levels(df, signal):
    entry = df['Close'].iloc[-1]
    swing_high = df['High'].rolling(15).max().iloc[-1]
    swing_low = df['Low'].rolling(15).min().iloc[-1]

    if signal == "BUY":
        sl = swing_low
        target = entry + (entry - sl) * 2
    else:
        sl = swing_high
        target = entry - (sl - entry) * 2

    return entry, sl, target

# 🎯 OPTION SELECT
def select_option(symbol, entry, signal):
    step = 100 if symbol == "^NSEBANK" else 50
    atm = round(entry / step) * step

    if signal == "BUY":
        return f"{atm - step} CE"
    else:
        return f"{atm + step} PE"

# 🔄 MAIN
indices = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK"
}

message = "🔥 PRO OPTIONS BOT 🔥\n\n"

for name, symbol in indices.items():

    df15 = yf.download(symbol, period="5d", interval="15m")
    df5 = yf.download(symbol, period="5d", interval="5m")

    trend = htf_trend(df15)

    if not trend:
        message += f"{name} → No trend\n\n"
        continue

    oc_data = get_option_chain(name)
    oi_bias, pcr = analyze_oi(oc_data)
    ce_wall, pe_wall = get_oi_walls(oc_data)

    price = df5['Close'].iloc[-1]
    gamma = gamma_signal(price, ce_wall, pe_wall, pcr)

    if gamma and gamma == trend:
        entry, sl, target = entry_levels(df5, gamma)
        option = select_option(symbol, entry, gamma)

        message += f"""📊 {name}
Signal: {gamma}
Trend: {trend}
PCR: {round(pcr,2)}

CE Wall: {ce_wall}
PE Wall: {pe_wall}

🎯 Option: {option}
Entry: {round(entry,2)}
SL: {round(sl,2)}
Target: {round(target,2)}

Time: {datetime.now().strftime('%H:%M')}

"""

    else:
        message += f"{name} → No strong setup\n\n"

send(message)
print(message)
