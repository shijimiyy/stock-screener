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
# ────────────────────────────────────────────────

def get_sp500_tickers():
    """S&P500全銘柄リストを自動取得"""
    try:
        import pandas as pd
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]
        tickers = df["Symbol"].tolist()
        # ドットをハイフンに変換（例：BRK.B → BRK-B）
        tickers = [t.replace(".", "-") for t in tickers]
        print(f"S&P500銘柄数: {len(tickers)}")
        return tickers
    except Exception as e:
        print(f"S&P500リスト取得失敗: {e}")
        # フォールバック用の主要銘柄
        return [
            "NVDA", "AMD", "META", "TSLA", "NBIS",
            "HIMS", "AAPL", "MSFT", "AMZN", "GOOGL"
        ]

def get_data(ticker):
    """Yahoo Financeから過去10日分のデータを取得"""
    try:
        df = yf.download(ticker, period="10d", interval="1d", progress=False)
        if df is None or len(df) < 3:
            return None
        return df
    except Exception as e:
        print(f"  ⚠️ {ticker} 取得失敗: {e}")
        return None

def check_signals(ticker, df):
    """シグナル判定"""
    if df is None or len(df) < 3:
        return None

    latest  = df.iloc[-1]
    prev    = df.iloc[-2]
    past5   = df.iloc[-6:-1] if len(df) >= 6 else df.iloc[:-1]

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
    print(f"{'='*40}")

    tickers = get_sp500_tickers()
    results = []

    for ticker in tickers:
        print(f"チェック中: {ticker}")
        df  = get_data(ticker)
        sig = check_signals(ticker, df)
        if sig:
            print(f"  ✅ シグナル: {sig['signals']}")
            results.append(sig)
        else:
            print(f"  ─ シグナルなし")
        time.sleep(0.5)

    send_discord(results)
    print(f"\n完了: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
