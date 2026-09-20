from flask import Flask, jsonify, render_template, request
import yfinance as yf
import pandas as pd
import numpy as np
from functools import lru_cache
from datetime import datetime, timezone

app = Flask(__name__)


def clean(v):
    try:
        if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
            return None
        if pd.isna(v):
            return None
        if hasattr(v, 'item'):
            v = v.item()
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, (np.floating,)):
            return float(v)
        return v
    except Exception:
        return None


def num(v):
    v = clean(v)
    return float(v) if isinstance(v, (int, float)) else None


def first_value(series, names):
    if series is None:
        return None
    for name in names:
        try:
            if name in series.index:
                return num(series.loc[name])
        except Exception:
            pass
    return None


def latest_annual(df, names):
    if df is None or df.empty:
        return None
    for name in names:
        if name in df.index:
            row = df.loc[name]
            for value in row.tolist():
                v = num(value)
                if v is not None:
                    return v
    return None


def annual_growth(df, names):
    if df is None or df.empty:
        return None
    for name in names:
        if name in df.index:
            row = df.loc[name].dropna()
            vals = [num(v) for v in row.tolist() if num(v) is not None]
            if len(vals) >= 2 and vals[1] != 0:
                return (vals[0] / vals[1] - 1) * 100
    return None


@lru_cache(maxsize=64)
def get_stock(symbol):
    ticker = symbol.upper().replace('.JK', '') + '.JK'
    tk = yf.Ticker(ticker)
    info = tk.info or {}
    hist = tk.history(period='1y', interval='1d', auto_adjust=False)
    financials = tk.financials
    balance = tk.balance_sheet
    cashflow = tk.cashflow

    price = num(info.get('currentPrice') or info.get('regularMarketPrice'))
    prev = num(info.get('previousClose') or info.get('regularMarketPreviousClose'))
    change = price - prev if price is not None and prev is not None else None
    change_pct = change / prev * 100 if change is not None and prev else None

    revenue = latest_annual(financials, ['Total Revenue', 'Operating Revenue'])
    net_income = latest_annual(financials, ['Net Income', 'Net Income Common Stockholders'])
    equity = latest_annual(balance, ['Stockholders Equity', 'Common Stock Equity', 'Total Equity Gross Minority Interest'])
    assets = latest_annual(balance, ['Total Assets'])
    debt = latest_annual(balance, ['Total Debt', 'Long Term Debt And Capital Lease Obligation', 'Long Term Debt'])
    ocf = latest_annual(cashflow, ['Operating Cash Flow', 'Total Cash From Operating Activities'])
    fcf = latest_annual(cashflow, ['Free Cash Flow'])

    shares = num(info.get('sharesOutstanding'))
    eps = num(info.get('trailingEps'))
    bvps = equity / shares if equity is not None and shares else None
    pe = price / eps if price is not None and eps not in (None, 0) else num(info.get('trailingPE'))
    pbv = price / bvps if price is not None and bvps not in (None, 0) else num(info.get('priceToBook'))
    roe = (net_income / equity * 100) if net_income is not None and equity else num(info.get('returnOnEquity'))
    roa = (net_income / assets * 100) if net_income is not None and assets else num(info.get('returnOnAssets'))
    npm = (net_income / revenue * 100) if net_income is not None and revenue else None
    debt_assets = (debt / assets * 100) if debt is not None and assets else None
    dividend_yield = num(info.get('dividendYield'))
    if dividend_yield is not None and dividend_yield < 1:
        dividend_yield *= 100

    chart = []
    if not hist.empty:
        for idx, row in hist.tail(252).iterrows():
            chart.append({'date': idx.strftime('%Y-%m-%d'), 'close': round(float(row['Close']), 2)})

    return {
        'symbol': symbol.upper(),
        'name': info.get('longName') or info.get('shortName') or symbol.upper(),
        'sector': info.get('sector'),
        'industry': info.get('industry'),
        'price': clean(price),
        'change': clean(change),
        'change_pct': clean(change_pct),
        'market_cap': clean(num(info.get('marketCap'))),
        'pe': clean(pe), 'pbv': clean(pbv), 'eps': clean(eps), 'bvps': clean(bvps),
        'roe': clean(roe), 'roa': clean(roa), 'npm': clean(npm),
        'dividend_yield': clean(dividend_yield),
        'revenue': clean(revenue), 'net_income': clean(net_income),
        'assets': clean(assets), 'equity': clean(equity), 'debt': clean(debt),
        'debt_assets': clean(debt_assets), 'operating_cash_flow': clean(ocf), 'free_cash_flow': clean(fcf),
        'revenue_growth': clean(annual_growth(financials, ['Total Revenue', 'Operating Revenue'])),
        'net_income_growth': clean(annual_growth(financials, ['Net Income', 'Net Income Common Stockholders'])),
        'chart': chart,
        'source': 'Yahoo Finance melalui yfinance',
        'retrieved_at': datetime.now(timezone.utc).isoformat()
    }


def sharia_note(data):
    # This is intentionally NOT an OJK eligibility decision. Official DES is authoritative.
    debt = data.get('debt_assets')
    notes = []
    if debt is not None:
        notes.append(f"Rasio utang terhadap aset dari data pasar yang tersedia: {debt:.1f}% (indikator, bukan penetapan DES OJK).")
    notes.append('Status DES OJK harus diverifikasi pada Daftar Efek Syariah resmi karena data pasar tidak memuat seluruh komponen penyaringan syariah.')
    notes.append('Pendapatan bunga/tidak halal dan jenis kegiatan usaha tidak dapat disimpulkan hanya dari data Yahoo Finance.')
    return notes


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/health')
def health():
    return jsonify({'ok': True})


@app.get('/api/stock')
def api_stock():
    symbol = request.args.get('symbol', '').strip().upper()
    if not symbol:
        return jsonify({'error': 'Masukkan kode emiten, misalnya BBCA.'}), 400
    if len(symbol) > 10 or not symbol.replace('.', '').isalnum():
        return jsonify({'error': 'Kode emiten tidak valid.'}), 400
    try:
        data = get_stock(symbol)
        data['sharia_notes'] = sharia_note(data)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': f'Data {symbol} belum dapat diambil. Coba lagi beberapa saat. Detail: {str(e)[:180]}'}), 502


@app.post('/api/clear-cache')
def clear_cache():
    get_stock.cache_clear()
    return jsonify({'ok': True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
