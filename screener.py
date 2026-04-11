import requests
import time
from datetime import datetime
import yfinance as yf
import os

# ── 設定 ──────────────────────────────────────────
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# 判定の閾値
VOL_SURGE_X  = 2.0   # 出来高が前日の何倍以上で通知するか
BREAKOUT_PCT = 2.0   # 直近5日高値から何%超えたらブレイクアウトか
DAY_CHANGE   = 5.0   # 前日比何%以上で大陽線とするか
RSI_OVERSOLD = 30.0  # RSIがこの値以下で売られすぎ通知
SHORT_RATIO  = 10.0  # 空売り比率がこの値以上でショートスクイーズ候補
# ────────────────────────────────────────────────

# S&P500 + ナスダック100 固定リスト
TICKERS = list(set([
    "MMM","AOS","ABT","ABBV","ACN","ADBE","AMD","AES","AFL","A","APD","ABNB","AKAM","ALB","ARE",
    "ALGN","ALLE","LNT","ALL","GOOGL","GOOG","MO","AMZN","AMCR","AEE","AAL","AEP","AXP","AIG",
    "AMT","AWK","AMP","AME","AMGN","APH","ADI","ANSS","AON","APA","AAPL","AMAT","APTV","ACGL",
    "ADM","ANET","AJG","AIZ","T","ATO","ADSK","AZO","AVB","AVY","AXON","BKR","BALL","BAC","BK",
    "BBWI","BAX","BDX","BRK-B","BBY","BIO","TECH","BIIB","BLK","BX","BA","BCR","BSX","BMY","AVGO",
    "BR","BRO","BF-B","BLDR","BG","CDNS","CZR","CPT","CPB","COF","CAH","KMX","CCL","CARR","CAT",
    "CBOE","CBRE","CDW","CE","COR","CNC","CNX","CDAY","CF","CRL","SCHW","CHTR","CVX","CMG","CB",
    "CHD","CI","CINF","CTAS","CSCO","C","CFG","CLX","CME","CMS","KO","CTSH","CL","CMCSA","CMA",
    "CAG","COP","ED","STZ","CEG","COO","CPRT","GLW","CTVA","CSGP","COST","CTRA","CCI","CSX",
    "CMI","CVS","DHI","DHR","DRI","DVA","DAY","DECK","DE","DAL","DVN","DXCM","FANG","DLR","DFS",
    "DG","DLTR","D","DPZ","DOV","DOW","DHC","DTE","DUK","DD","EMN","ETN","EBAY","ECL","EIX",
    "EW","EA","ELV","LLY","EMR","ENPH","ETR","EOG","EPAM","EQT","EFX","EQIX","EQR","ESS","EL",
    "ETSY","EG","EVRST","ES","EXC","EXPE","EXPD","EXR","XOM","FFIV","FDS","FICO","FAST","FRT",
    "FDX","FIS","FITB","FSLR","FE","FI","FLT","FMC","F","FTNT","FTV","FOXA","FOX","BEN","FCX",
    "GRMN","IT","GE","GEHC","GEV","GEN","GNRC","GD","GIS","GM","GPC","GILD","GPN","GL","GDDY",
    "GS","HAL","HIG","HAS","HCA","DOC","HSIC","HSY","HES","HPE","HLT","HOLX","HD","HON","HRL",
    "HST","HWM","HPQ","HUBB","HUM","HBAN","HII","IBM","IEX","IDXX","ITW","INCY","IR","PODD",
    "INTC","ICE","IFF","IP","IPG","INTU","ISRG","IVZ","INVH","IQV","IRM","JBHT","JBL","JKHY",
    "J","JNJ","JCI","JPM","JNPR","K","KVUE","KDP","KEY","KEYS","KMB","KIM","KMI","KLAC","KHC",
    "KR","LHX","LH","LRCX","LW","LVS","LDOS","LEN","LNC","LIN","LYV","LKQ","LMT","L","LOW",
    "LULU","LYB","MTB","MRO","MPC","MKTX","MAR","MMC","MLM","MAS","MA","MTCH","MKC","MCD","MCK",
    "MDT","MRK","META","MET","MTD","MGM","MCHP","MU","MSFT","MAA","MRNA","MHK","MOH","TAP","MDLZ",
    "MPWR","MNST","MCO","MS","MOS","MSI","MSCI","NDAQ","NTAP","NFLX","NWL","NEM","NWSA","NWS",
    "NEE","NKE","NI","NDSN","NSC","NTRS","NOC","NCLH","NRG","NUE","NVDA","NVR","NXPI","ORLY",
    "OXY","ODFL","OMC","ON","OKE","ORCL","OTIS","PCAR","PKG","PANW","PH","PAYX","PAYC","PYPL",
    "PNR","PEP","PFE","PCG","PM","PSX","PNW","PXD","PNC","POOL","PPG","PPL","PFG","PG","PGR",
    "PRU","PEG","PTCT","PTC","PSA","PHM","QRVO","PWR","QCOM","DGX","RL","RJF","RTX","O","REG",
    "REGN","RF","RSG","RMD","RVTY","ROK","ROL","ROP","ROST","RCL","SPGI","CRM","SBAC","SLB",
    "STX","SRE","NOW","SHW","SPG","SWKS","SJM","SW","SNA","SOLV","SO","LUV","SWK","SBUX","STT",
    "STLD","STE","SYK","SMCI","SYF","SNPS","SYY","TMUS","TROW","TTWO","TPR","TRGP","TGT","TEL",
    "TDY","TFX","TER","TSLA","TXN","TMO","TJX","TSCO","TT","TDG","TRV","TRMB","TFC","TYL","TSN",
    "USB","UBER","UDR","ULTA","UNP","UAL","UPS","URI","UNH","UHS","VLO","VTR","VLTO","VRSN",
    "VRSK","VZ","VRTX","VTRS","VICI","V","VST","VMC","WRB","GWW","WAB","WBA","WMT","DIS","WBD",
    "WM","WAT","WEC","WFC","WELL","WST","WDC","WY","WHR","WMB","WTW","WYNN","XEL","XYL","YUM",
    "ZBRA","ZBH","ZTS",
    # ナスダック100追加分
    "ADSK","AEP","ABNB","ALGN","GOOGL","GOOG","AMZN","AMD","AMGN","ADI","ANSS","AAPL","AMAT",
    "ASML","AZN","TEAM","ADBE","AVGO","BIIB","BKNG","CDNS","CHTR","CTAS","CSCO","CTSH","CMCSA",
    "CPRT","CSGP","COST","CRWD","CSX","DDOG","DXCM","FANG","DLTR","EA","ENPH","EXC","FAST",
    "FTNT","GEHC","GILD","HON","IDXX","ILMN","INTC","INTU","ISRG","KDP","KHC","KLAC","LRCX",
    "LULU","MAR","MRVL","MELI","META","MCHP","MU","MSFT","MDLZ","MNST","NFLX","NVDA","NXPI",
    "ORLY","ODFL","ON","PCAR","PANW","PAYX","PYPL","PEP","QCOM","REGN","ROST","CRM","SBUX",
    "SNPS","TMUS","TSLA","TXN","VRSK","VRTX","WBA","WBD","WDAY","XEL","ZS","ZM","HIMS","NBIS",
]))

def get_data(ticker):
    """Yahoo Financeから過去30日分のデータを取得"""
    try:
        df = yf.download(ticker, period="30d", interval="1d", progress=False, auto_adjust=True)
        if df is None or len(df) < 3:
            return None
        df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        print(f"  ⚠️ {ticker} 取得失敗: {e}")
        return None

def calc_rsi(df, period=14):
    """RSIを計算する"""
    try:
        close = df["Close"]
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    except:
        return None

def get_short_ratio(ticker):
    """空売り比率を取得する"""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        ratio = info.get("shortPercentOfFloat", None)
        if ratio is not None:
            return round(ratio * 100, 1)
        return None
    except:
        return None

def check_signals(ticker, df):
    """シグナル判定"""
    if df is None or len(df) < 3:
        return None

    latest = df.iloc[-1]
    prev   = df.iloc[-2]
    past5  = df.iloc[-6:-1] if len(df) >= 6 else df.iloc[:-1]

    signals = []
    details = {}

    # ① 出来高急増（前日比）
    try:
        vol_today = float(latest["Volume"])
        vol_prev  = float(prev["Volume"])
        if vol_prev > 0:
            vol_ratio = vol_today / vol_prev
            if vol_ratio >= VOL_SURGE_X:
                signals.append("📊 出来高急増")
                details["出来高"] = f"{vol_ratio:.1f}x"
    except:
        pass

    # ② ブレイクアウト（直近5日高値超え）
    try:
        close_today = float(latest["Close"])
        recent_high = float(past5["High"].max())
        if recent_high > 0:
            bo_pct = (close_today - recent_high) / recent_high * 100
            if bo_pct >= BREAKOUT_PCT:
                signals.append("🚀 ブレイクアウト")
                details["高値超え"] = f"+{bo_pct:.1f}%"
    except:
        pass

    # ③ 大陽線（前日比+5%以上）
    try:
        close_today = float(latest["Close"])
        close_prev  = float(prev["Close"])
        if close_prev > 0:
            day_chg = (close_today - close_prev) / close_prev * 100
            if day_chg >= DAY_CHANGE:
                signals.append("🕯 大陽線")
                details["騰落率"] = f"+{day_chg:.1f}%"
    except:
        pass

    # ④ RSI売られすぎ（30以下）
    rsi = calc_rsi(df)
    if rsi is not None and rsi <= RSI_OVERSOLD:
        signals.append("📉 RSI売られすぎ")
        details["RSI"] = f"{rsi:.1f}"

    # ⑤ 空売り比率（ショートスクイーズ候補）
    short_ratio = get_short_ratio(ticker)
    if short_ratio is not None and short_ratio >= SHORT_RATIO:
        signals.append("💥 空売り高い")
        details["空売り比率"] = f"{short_ratio}%"

    if not signals:
        return None

    try:
        price = float(latest["Close"])
    except:
        price = 0

    return {
        "ticker":  ticker,
        "price":   price,
        "signals": signals,
        "details": details,
    }

def send_discord(results):
    """Discord通知を送る"""
    if not WEBHOOK_URL:
        print("❌ DISCORD_WEBHOOK_URL が設定されていません")
        return

    now = datetime.now().strftime("%m/%d %H:%M")

    if not results:
        requests.post(WEBHOOK_URL, json={
            "content": f"📭 {now} スクリーニング完了 — 該当銘柄なし"
        })
        return

    embeds = []
    for r in results:
        tag_str = "　".join(r["signals"])
        det_str = "　".join(f"{k}: {v}" for k, v in r["details"].items())
        embeds.append({
            "title":       f"{r['ticker']}　${r['price']:.2f}",
            "description": f"{tag_str}\n{det_str}",
            "color":       0x00e676,
        })

    for i in range(0, len(embeds), 10):
        payload = {
            "content": f"🔍 **スクリーニング結果** {now} — {len(results)}銘柄ヒット",
            "embeds":  embeds[i:i+10],
        }
        requests.post(WEBHOOK_URL, json=payload)
        time.sleep(1)

def main():
    print(f"\n{'='*40}")
    print(f"開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"合計: {len(TICKERS)}銘柄をスキャン")
    print(f"{'='*40}")

    results = []

    for ticker in TICKERS:
        print(f"チェック中: {ticker}")
        df  = get_data(ticker)
        sig = check_signals(ticker, df)
        if sig:
            print(f"  ✅ シグナル: {sig['signals']}")
            results.append(sig)
        else:
            print(f"  ─ シグナルなし")
        time.sleep(0.3)

    send_discord(results)
    print(f"\n完了: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
