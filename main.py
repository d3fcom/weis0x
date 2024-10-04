import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
from ta.trend import MACD, EMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange

st.set_page_config(
    page_title="weiscreener",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stButton>button {
        width: 100%;
    }
    .reportview-container .main .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    body {
        background-color: #f9f9f9;
    }
</style>
""", unsafe_allow_html=True)

logo_svg = base64.b64encode(open("assets/logo2.svg", "rb").read()).decode()

st.markdown(f'''
<div style="display: flex; justify-content: center; margin-bottom: 2rem;">
    <img src="data:image/svg+xml;base64,{logo_svg}" style="width: 100px; height: auto;">
</div>
''', unsafe_allow_html=True)

st.title("MEME Coin Analyzer")

coin_input = st.text_input("Enter MEME coin contract address or symbol:")

def fetch_coin_data(coin_input):
    base_url = "https://api.dexscreener.com/latest/dex"
    
    if coin_input.startswith("0x"):
        endpoint = f"/tokens/{coin_input}"
    else:
        endpoint = f"/search?q={coin_input}"
    
    response = requests.get(base_url + endpoint)
    
    if response.status_code == 200:
        data = response.json()
        if "pairs" in data and len(data["pairs"]) > 0:
            return data["pairs"][0]
    
    return None

def fetch_historical_data(pair_address, days=30):
    base_url = "https://api.dexscreener.com/latest/dex"
    endpoint = f"/chart/{pair_address}"
    params = {"from": int((datetime.now() - timedelta(days=days)).timestamp())}
    
    response = requests.get(base_url + endpoint, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if "data" in data and "candles" in data["data"]:
            return data["data"]["candles"]
    
    return None

def create_price_chart(price_data_list, coin_names):
    fig = go.Figure()
    for price_data, coin_name in zip(price_data_list, coin_names):
        df = pd.DataFrame(price_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.sort_values('timestamp')
        
        macd = MACD(close=df['close'])
        rsi = RSIIndicator(close=df['close'])
        bollinger = BollingerBands(close=df['close'])
        ema = EMAIndicator(close=df['close'], window=20)
        stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'])
        atr = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'])
        
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['rsi'] = rsi.rsi()
        df['bollinger_high'] = bollinger.bollinger_hband()
        df['bollinger_low'] = bollinger.bollinger_lband()
        df['ema'] = ema.ema_indicator()
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()
        df['atr'] = atr.average_true_range()
        
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'],
                                 mode='lines', name=f'{coin_name} Price'))
        
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ema'],
                                 mode='lines', name=f'{coin_name} EMA (20)', line=dict(dash='dot')))
        
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['bollinger_high'],
                                 mode='lines', name=f'{coin_name} Bollinger High', line=dict(dash='dash')))
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['bollinger_low'],
                                 mode='lines', name=f'{coin_name} Bollinger Low', line=dict(dash='dash')))
        
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['macd'],
                                 mode='lines', name=f'{coin_name} MACD', yaxis='y2'))
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['macd_signal'],
                                 mode='lines', name=f'{coin_name} MACD Signal', yaxis='y2'))
        
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['rsi'],
                                 mode='lines', name=f'{coin_name} RSI', yaxis='y3'))
        
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['stoch_k'],
                                 mode='lines', name=f'{coin_name} Stoch %K', yaxis='y4'))
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['stoch_d'],
                                 mode='lines', name=f'{coin_name} Stoch %D', yaxis='y4'))
        
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['atr'],
                                 mode='lines', name=f'{coin_name} ATR', yaxis='y5'))

    fig.update_layout(
        title='Price History and Technical Indicators',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        height=1200,
        yaxis2=dict(title='MACD', overlaying='y', side='right'),
        yaxis3=dict(title='RSI', overlaying='y', side='right', anchor='free', position=1.05),
        yaxis4=dict(title='Stochastic', overlaying='y', side='right', anchor='free', position=1.10),
        yaxis5=dict(title='ATR', overlaying='y', side='right', anchor='free', position=1.15)
    )
    return fig

def display_coin_chart(coin_input):
    if coin_input:
        with st.spinner("Fetching data..."):
            coin_data = fetch_coin_data(coin_input)
            if coin_data:
                historical_data = fetch_historical_data(coin_data['pairAddress'])
                if historical_data:
                    price_chart = create_price_chart([historical_data], [coin_data['baseToken']['symbol']])
                    st.plotly_chart(price_chart, use_container_width=True)
                else:
                    st.error("Unable to fetch historical data for the given coin.")
            else:
                st.error("Unable to fetch data for the given coin. Please check the input and try again.")

chart_placeholder = st.empty()

if coin_input:
    with chart_placeholder:
        display_coin_chart(coin_input)

st.markdown("---")
st.markdown("Created with ❤️ by Weis")
