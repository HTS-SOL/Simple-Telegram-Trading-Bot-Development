import tkinter as tk
from tkinter import messagebox
import requests
import threading
from telegram import Bot
import time
import logging
from binance.client import Client

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
DEXSCREENER_API_URL = 'https://api.dexscreener.com/latest/dex/pairs'

binance_client = None

def get_trading_data(pair):
    try:
        response = requests.get(f"{DEXSCREENER_API_URL}/{pair}")
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data: {e}")
        return None

def execute_trade(pair, trade_action, amount):
    try:
        base_currency, quote_currency = pair.split('-')
        binance_pair = base_currency + quote_currency
        market_price = float(binance_client.get_symbol_ticker(symbol=binance_pair)['price'])

        if trade_action == 'buy':
            order = binance_client.order_market_buy(
                symbol=binance_pair,
                quantity=amount / market_price  
            )
        elif trade_action == 'sell':
            order = binance_client.order_market_sell(
                symbol=binance_pair,
                quantity=amount / market_price
            )
        logger.info(f"Trade Executed: {trade_action} {amount} {pair} at {market_price} price")
        return order
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        return None

def send_trade_message(bot, chat_id, pair, data):
    message = f"Trading Data for {pair}:\n" \
              f"Price: ${data['priceUsd']}\n" \
              f"Volume: {data['volume']}\n" \
              f"24h Change: {data['priceChange']}%"
    
    bot.send_message(chat_id=chat_id, text=message)

# Function to fetch data and update the GUI and Telegram
def fetch_data():
    # Fetch user inputs
    api_token = api_token_entry.get()
    pair = trade_pair_entry.get().upper()
    chat_id = chat_id_entry.get()
    price_threshold = float(price_threshold_entry.get())
    volume_threshold = float(volume_threshold_entry.get())
    trade_amount = float(trade_amount_entry.get())
    binance_api_key = binance_api_key_entry.get()
    binance_api_secret = binance_api_secret_entry.get()

    if not api_token or not pair or not chat_id or not binance_api_key or not binance_api_secret:
        messagebox.showwarning("Input Error", "Please enter all fields (API Token, Trading Pair, Chat ID, Binance API).")
        return
    
    try:
        # Initialize Binance client with user input API credentials
        global binance_client
        binance_client = Client(binance_api_key, binance_api_secret)
        
        # Initialize Telegram bot
        bot = Bot(token=api_token)
    except Exception as e:
        messagebox.showerror("Error", f"Invalid API Credentials: {e}")
        return

    # Fetch trading data from Dexscreener
    trading_data = get_trading_data(pair)

    if trading_data:
        price = trading_data['data']['priceUsd']
        volume = trading_data['data']['volume']
        change = trading_data['data']['priceChange']
        
        result_label.config(
            text=f"Trading Data for {pair}:\n"
                 f"Price: ${price}\n"
                 f"Volume: {volume}\n"
                 f"24h Change: {change}%"
        )
        
        # Send message to Telegram chat
        send_trade_message(bot, chat_id, pair, trading_data['data'])

        # Auto-sniping logic: Execute a trade if certain conditions are met
        if float(change) > price_threshold and float(volume) > volume_threshold:
            execute_trade(pair, 'buy', trade_amount)  # Buy the specified amount of the pair
            send_trade_message(bot, chat_id, pair, {"priceUsd": price, "volume": volume, "priceChange": change})
    else:
        messagebox.showerror("Error", f"Could not retrieve data for {pair}. Please try again later.")

# Tkinter GUI Setup
def setup_gui():
    window = tk.Tk()
    window.title("Dynamic Telegram Trading Bot")

    # Set window size and layout
    window.geometry("600x600")
    window.resizable(False, False)

    # Label and entry for API token
    api_token_label = tk.Label(window, text="Enter Telegram API Token:")
    api_token_label.pack(pady=10)

    global api_token_entry
    api_token_entry = tk.Entry(window, width=40)
    api_token_entry.pack(pady=5)

    # Label and entry for trading pair
    pair_label = tk.Label(window, text="Enter Trading Pair (e.g., BTC-USDT):")
    pair_label.pack(pady=10)

    global trade_pair_entry
    trade_pair_entry = tk.Entry(window, width=30)
    trade_pair_entry.pack(pady=5)

    # Label and entry for Telegram chat ID
    chat_id_label = tk.Label(window, text="Enter Telegram Chat ID:")
    chat_id_label.pack(pady=10)

    global chat_id_entry
    chat_id_entry = tk.Entry(window, width=30)
    chat_id_entry.pack(pady=5)

    # Label and entry for Price Threshold
    price_threshold_label = tk.Label(window, text="Enter Price Change Threshold (%):")
    price_threshold_label.pack(pady=10)

    global price_threshold_entry
    price_threshold_entry = tk.Entry(window, width=20)
    price_threshold_entry.pack(pady=5)

    # Label and entry for Volume Threshold
    volume_threshold_label = tk.Label(window, text="Enter Volume Threshold:")
    volume_threshold_label.pack(pady=10)

    global volume_threshold_entry
    volume_threshold_entry = tk.Entry(window, width=20)
    volume_threshold_entry.pack(pady=5)

    # Label and entry for Trade Amount
    trade_amount_label = tk.Label(window, text="Enter Trade Amount ($):")
    trade_amount_label.pack(pady=10)

    global trade_amount_entry
    trade_amount_entry = tk.Entry(window, width=20)
    trade_amount_entry.pack(pady=5)

    # Label and entry for Binance API Key
    binance_api_key_label = tk.Label(window, text="Enter Binance API Key:")
    binance_api_key_label.pack(pady=10)

    global binance_api_key_entry
    binance_api_key_entry = tk.Entry(window, width=40)
    binance_api_key_entry.pack(pady=5)

    # Label and entry for Binance API Secret
    binance_api_secret_label = tk.Label(window, text="Enter Binance API Secret:")
    binance_api_secret_label.pack(pady=10)

    global binance_api_secret_entry
    binance_api_secret_entry = tk.Entry(window, width=40)
    binance_api_secret_entry.pack(pady=5)

    # Button to fetch data
    fetch_button = tk.Button(window, text="Get Trading Data", command=fetch_data)
    fetch_button.pack(pady=10)

    # Label to show result
    global result_label
    result_label = tk.Label(window, text="Trading data will appear here.", justify="left")
    result_label.pack(pady=10)

    # Start the Tkinter event loop
    window.mainloop()

# Thread to run the Tkinter GUI and the bot simultaneously
def run_gui():
    setup_gui()

# Main function to start the bot and GUI
def main():
    gui_thread = threading.Thread(target=run_gui)
    gui_thread.start()

    # Continuous data fetching every 5 seconds for updates
    while True:
        time.sleep(5)  # Fetch every 5 seconds
        pair = trade_pair_entry.get().upper()
        if pair:
            trading_data = get_trading_data(pair)
            if trading_data:
                price = trading_data['data']['priceUsd']
                volume = trading_data['data']['volume']
                change = trading_data['data']['priceChange']
                # Update GUI with the latest data
                result_label.config(
                    text=f"Trading Data for {pair}:\n"
                         f"Price: ${price}\n"
                         f"Volume: {volume}\n"
                         f"24h Change: {change}%"
                )

if __name__ == "__main__":
    main()
