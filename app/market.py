import httpx, ccxt, pandas as pd, numpy as np
from .config import TOP_N, QUOTE

async def top_coins():
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get("https://api.coingecko.com/api/v3/coins/markets",
            params={"vs_currency":"usd","order":"market_cap_desc","per_page":TOP_N,"page":1,"sparkline":"false"})
        r.raise_for_status()
        return r.json()

def make_exchange():
    ex = ccxt.binance({"enableRateLimit": True, "options":{"defaultType":"spot"}})
    ex.load_markets()
    return ex

async def universe():
    coins = await top_coins()
    ex = make_exchange()
    pairs = [(coin, f"{coin['symbol'].upper()}/{QUOTE}") for coin in coins]
    return ex, [(c,s) for c,s in pairs if s in ex.markets and ex.markets[s].get("spot")]

async def fear_greed():
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get("https://api.alternative.me/fng/?limit=1")
        r.raise_for_status()
        d = r.json()["data"][0]
        return int(d["value"]), d["value_classification"]

async def globals_data():
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get("https://api.coingecko.com/api/v3/global")
        r.raise_for_status()
        d = r.json()["data"]
        return d["total_market_cap"]["usd"], d["total_volume"]["usd"], d["market_cap_percentage"]["btc"]

def indicators(df):
    c=df.close
    df["ema20"]=c.ewm(span=20,adjust=False).mean()
    df["ema50"]=c.ewm(span=50,adjust=False).mean()
    delta=c.diff()
    gain=delta.clip(lower=0).ewm(alpha=1/14,adjust=False).mean()
    loss=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean()
    rs=gain/loss.replace(0,np.nan)
    df["rsi"]=100-(100/(1+rs))
    macd=c.ewm(span=12,adjust=False).mean()-c.ewm(span=26,adjust=False).mean()
    df["macd_hist"]=macd-macd.ewm(span=9,adjust=False).mean()
    tr=pd.concat([df.high-df.low,(df.high-c.shift()).abs(),(df.low-c.shift()).abs()],axis=1).max(axis=1)
    df["atr"]=tr.rolling(14).mean()
    return df

def analyze(ex,symbol):
    def get(tf):
        rows=ex.fetch_ohlcv(symbol,timeframe=tf,limit=150)
        return indicators(pd.DataFrame(rows,columns=["ts","open","high","low","close","volume"]))
    m=get("30m").iloc[-1]; h=get("4h").iloc[-1]
    avg=float(get("30m").volume.tail(20).mean())
    ratio=float(m.volume/avg) if avg else 0
    score=sum([m.ema20>m.ema50,h.ema20>h.ema50,m.macd_hist>0,45<=m.rsi<=68,ratio>=1.2])
    return {"price":float(m.close),"trend30":"صاعد" if m.ema20>m.ema50 else "هابط",
            "trend4h":"صاعد" if h.ema20>h.ema50 else "هابط","rsi":float(m.rsi),
            "volume_ratio":ratio,"score":int(score)}
