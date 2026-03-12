import streamlit as st
import requests
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("Crypto Full Analyzer – تحليل فني شامل")

API_KEY = "9027ddd4eadf4bff8281da22868c2094"

coin = st.text_input("اكتب رمز العملة مثل DOT أو CVX أو BTC").lower()

if coin:

    df_daily = pd.DataFrame()
    df_hourly = pd.DataFrame()
    source_used = []

    # ----------------------------
    # بيانات يومية 90 يوم
    # ----------------------------
    try:
        url_daily = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={coin.upper()}&tsym=USD&limit=90&api_key={API_KEY}"
        data_daily = requests.get(url_daily).json()
        data_list = data_daily.get("Data", {}).get("Data", [])
        if data_list:
            df_daily = pd.DataFrame(data_list)
            df_daily["time"] = pd.to_datetime(df_daily["time"], unit="s")
            df_daily["open"] = df_daily["open"].astype(float)
            df_daily["high"] = df_daily["high"].astype(float)
            df_daily["low"] = df_daily["low"].astype(float)
            df_daily["close"] = df_daily["close"].astype(float)
            df_daily["volume"] = df_daily["volumeto"].astype(float)
            source_used.append("CryptoCompare Daily")
    except:
        pass

    # ----------------------------
    # بيانات ساعية 7 أيام
    # ----------------------------
    try:
        url_hourly = f"https://min-api.cryptocompare.com/data/v2/histohour?fsym={coin.upper()}&tsym=USD&limit=168&api_key={API_KEY}"
        data_hourly = requests.get(url_hourly).json()
        data_list = data_hourly.get("Data", {}).get("Data", [])
        if data_list:
            df_hourly = pd.DataFrame(data_list)
            df_hourly["time"] = pd.to_datetime(df_hourly["time"], unit="s")
            df_hourly["open"] = df_hourly["open"].astype(float)
            df_hourly["high"] = df_hourly["high"].astype(float)
            df_hourly["low"] = df_hourly["low"].astype(float)
            df_hourly["close"] = df_hourly["close"].astype(float)
            df_hourly["volume"] = df_hourly["volumeto"].astype(float)
            source_used.append("CryptoCompare Hourly")
    except:
        pass

    # ----------------------------
    # تحقق من وجود بيانات
    # ----------------------------
    if df_daily.empty and df_hourly.empty:
        st.error("لا توجد بيانات متاحة لهذه العملة من المصادر المجانية المتاحة حالياً")
        st.stop()

    st.subheader(f"المصادر المستخدمة: {', '.join(source_used)}")

    # ----------------------------
    # اختيار أي مجموعة بيانات للتحليل الفني
    # ----------------------------
    df = pd.concat([df_daily, df_hourly], ignore_index=True).sort_values("time")

    # ----------------------------
    # المؤشرات الفنية
    # ----------------------------
    df["EMA20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["EMA50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["EMA200"] = ta.trend.ema_indicator(df["close"], window=200)

    bb = ta.volatility.BollingerBands(df["close"], window=20)
    df["BB_high"] = bb.bollinger_hband()
    df["BB_low"] = bb.bollinger_lband()
    df["BB_mid"] = bb.bollinger_mavg()

    df["RSI"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    macd = ta.trend.MACD(df["close"])
    df["MACD"] = macd.macd()

    price = df["close"].iloc[-1]
    st.subheader("السعر الحالي")
    st.write(f"{price:.6f} USD")

    # ----------------------------
    # دعم ومقاومة
    # ----------------------------
    support = df["low"].tail(20).min()
    resistance = df["high"].tail(20).max()
    st.subheader("الدعم والمقاومة")
    st.write("الدعم:", support)
    st.write("المقاومة:", resistance)

    # ----------------------------
    # Fibonacci
    # ----------------------------
    high = df["high"].max()
    low = df["low"].min()
    fib_levels = {
        "0.236": high - (high-low)*0.236,
        "0.382": high - (high-low)*0.382,
        "0.5": high - (high-low)*0.5,
        "0.618": high - (high-low)*0.618,
        "0.786": high - (high-low)*0.786
    }
    st.subheader("مستويات فيبوناتشي")
    for k,v in fib_levels.items():
        st.write(k,":",v)

    # ----------------------------
    # Bollinger Bands
    # ----------------------------
    st.subheader("Bollinger Bands")
    st.write(f"العلوي: {df['BB_high'].iloc[-1]:.6f} | المتوسط: {df['BB_mid'].iloc[-1]:.6f} | السفلي: {df['BB_low'].iloc[-1]:.6f}")

    # ----------------------------
    # مناطق الشراء / البيع / التجميع
    # ----------------------------
    rsi = df["RSI"].iloc[-1]
    macd_val = df["MACD"].iloc[-1]
    avg_volume = df["volume"].tail(20).mean()
    last_volume = df["volume"].iloc[-1]

    status = ""
    if rsi < 30:
        status = "تشبع بيع / منطقة شراء محتملة 🔵"
    elif rsi > 70:
        status = "تشبع شراء / منطقة بيع محتملة 🔴"
    else:
        status = "حيادية 🟡"

    if last_volume > avg_volume*1.5:
        status += " | نشاط الحيتان مرتفع 🐋"

    st.subheader("تحليل حالة العملة")
    st.write(f"RSI: {rsi:.2f}, MACD: {macd_val:.6f}")
    st.write(f"الحالة العامة: {status}")

    # ----------------------------
    # Volume Profile
    # ----------------------------
    st.subheader("Volume Profile")
    bins = np.linspace(df["low"].min(), df["high"].max(), 20)
    df["bin"] = pd.cut(df["close"], bins)
    vp = df.groupby("bin")["volume"].sum().reset_index()
    vp = vp.dropna()
    vp["Price Range"] = vp["bin"].apply(lambda x: f"{x.left:.6f}-{x.right:.6f}")
    vp = vp[["Price Range","volume"]]
    vp.columns = ["نطاق السعر","حجم التداول"]
    st.bar_chart(vp.set_index("نطاق السعر"))

    # ----------------------------
    # التوصية النهائية
    # ----------------------------
    recommendation = ""
    if (rsi < 40 and price < fib_levels["0.5"]) or last_volume > avg_volume*1.5:
        recommendation = "توصية: شراء 👍"
    else:
        recommendation = "توصية: انتظار ⏳"

    st.subheader("التوصية النهائية")
    st.write(recommendation)
