"""
Bitcoin trading script for AlgoTrader
"""

import os
import argparse
import time
from datetime import datetime
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import requests

from src.api.trading import AlpacaTradingClient
from src.strategy.rsi_strategy import RSIStrategy

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="AlgoTrader - Bitcoin Trading")
    parser.add_argument("--paper", action="store_true", default=True, help="Use paper trading API (default: True)")
    parser.add_argument("--live", action="store_true", help="Use live trading API instead of paper")
    parser.add_argument("--symbol", type=str, default="BTC/USD", help="Crypto trading pair (default: BTC/USD)")
    parser.add_argument("--interval", type=int, default=1, help="Trading interval in seconds (default: 1 = high-speed)")
    parser.add_argument("--position-size", type=float, default=0.1, help="Position size as fraction of portfolio (default: 0.1)")
    
    args = parser.parse_args()
    
    # Use live trading if --live flag is provided
    paper_trading = not args.live
    
    # Get API credentials from environment variables
    api_key = os.getenv("ALPACA_API_KEY")
    api_secret = os.getenv("ALPACA_API_SECRET")
    
    if not api_key or not api_secret:
        raise ValueError("ALPACA_API_KEY and ALPACA_API_SECRET must be set in environment variables or .env file")
    
    # Initialize API clients
    trading_client = AlpacaTradingClient(api_key, api_secret, paper=paper_trading)
    
    # Get account information
    account = trading_client.get_account()
    print(f"\n{'PAPER' if paper_trading else 'LIVE'} TRADING ACCOUNT")
    print(f"Account ID: {account['id']}")
    print(f"Cash: ${float(account['cash']):.2f}")
    print(f"Portfolio Value: ${float(account['portfolio_value']):.2f}")
    print(f"Trading Status: {'Enabled' if not account['trading_blocked'] else 'Blocked'}")
    print(f"Crypto Status: {account.get('crypto_status', 'Unknown')}")
    
    # Check if crypto trading is enabled
    if account.get('crypto_status') != 'ACTIVE':
        print("\nWARNING: Crypto trading may not be active on this account.")
        print("If you encounter errors, please verify your account settings on Alpaca.")
    
    # Determine trading and market data symbols
    trading_symbol = args.symbol  # e.g., 'BTC/USD'
    
    # Helper to fetch real historical BTC/USD closes from CoinGecko for RSI
    def fetch_btc_usd_closes(symbol=None, n=30):
        try:
            # Use 1-minute interval for the last 30 closes (about 30 minutes)
            url = 'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart'
            params = {'vs_currency': 'usd', 'days': '1', 'interval': 'minutely'}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            prices = resp.json()['prices']
            closes = [price[1] for price in prices][-n:]
            if len(closes) < n:
                closes = [closes[0]] * (n - len(closes)) + closes  # pad if needed
            return closes
        except Exception as e:
            print(f"Error fetching BTC closes from CoinGecko: {e}")
            return [0] * n

    # Initialize RSI strategy
    strategy = RSIStrategy(
        trading_client=trading_client,
        fetch_closes_func=fetch_btc_usd_closes,
        symbol=trading_symbol,
        rsi_period=14,
        overbought=69,
        oversold=30
    )

    print(f"\nStarting Bitcoin trading bot for {trading_symbol}")
    print(f"Trading interval: 2 seconds")
    print(f"Position size: 10.0% of available cash")
    print(f"{'PAPER' if paper_trading else 'LIVE'} TRADING MODE")
    print("\nPress Ctrl+C to stop the trading bot...\n")

    trade_log = []

    try:
        while True:
            print(f"\n{'-' * 50}")
            now = datetime.now()
            print(f"Running strategy check at {now.strftime('%Y-%m-%d %H:%M:%S')}")

            # Fetch real BTC/USD price
            btc_price = fetch_btc_usd_closes(trading_symbol)[-1]
            if btc_price == 0:
                print("Could not fetch BTC price. Skipping this iteration.")
                time.sleep(2)
                continue
            print(f"Current BTC price: ${btc_price:.2f}")

            # Fetch account and BTC position from Alpaca
            account = trading_client.get_account()
            account_value = float(account['portfolio_value'])
            positions = trading_client.get_positions()
            btc_position = next((p for p in positions if p['symbol'] == trading_symbol), None)
            btc_qty = float(btc_position['qty']) if btc_position else 0.0
            btc_value = float(btc_position['market_value']) if btc_position else 0.0
            btc_pct = btc_value / account_value if account_value > 0 else 0.0

            signal, rsi_value = strategy.run()
            print(f"Strategy signal: {signal.upper()} (RSI={rsi_value:.2f})")
            print(f"Current BTC position: {btc_qty:.8f} BTC, ${btc_value:.2f} ({btc_pct*100:.2f}% of account)")

            action = 'hold'
            qty_str = None
            max_position_pct = 0.10
            max_position_value = account_value * max_position_pct

            if signal == 'buy' and btc_qty == 0.0:
                to_buy_value = max_position_value
                qty = to_buy_value / btc_price
                qty_str = f"{qty:.8f}"
                print(f"Placing market buy order for ${to_buy_value:.2f} of {trading_symbol} (qty: {qty_str})...")
                try:
                    buy_order = trading_client.submit_order(
                        symbol=trading_symbol,
                        qty=qty_str,
                        side="buy",
                        type="market",
                        time_in_force="gtc"
                    )
                    print(f"Buy order submitted: {buy_order.get('id', buy_order)}")
                    action = 'buy'
                except Exception as e:
                    print(f"Error submitting buy order: {e}")
            elif signal == 'sell' and btc_qty > 0.0:
                qty_str = f"{btc_qty:.8f}"
                print(f"Placing market sell order for all {trading_symbol} (qty: {qty_str})...")
                try:
                    sell_order = trading_client.submit_order(
                        symbol=trading_symbol,
                        qty=qty_str,
                        side="sell",
                        type="market",
                        time_in_force="gtc"
                    )
                    print(f"Sell order submitted: {sell_order.get('id', sell_order)}")
                    action = 'sell'
                except Exception as e:
                    print(f"Error submitting sell order: {e}")
            else:
                print("No trade action taken.")

            # Log the action
            trade_log.append({
                'timestamp': now,
                'action': action,
                'rsi': rsi_value,
                'btc_qty': btc_qty,
                'btc_value': btc_value,
                'btc_price': btc_price,
                'account_value': account_value
            })

            # Wait for next interval
            next_check = now.strftime('%Y-%m-%d %H:%M:%S')
            print(f"\nNext check at: {next_check}")
            print(f"Waiting for 2 seconds...")
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nTrading bot stopped by user")
    except Exception as e:
        print(f"\nError in trading loop: {str(e)}")
    finally:
        print("\nTrading bot shutdown complete")
        # Save log to Excel
        try:
            df = pd.DataFrame(trade_log)
            df.to_excel('btc_trading_log.xlsx', index=False)
            print("Trade log saved to btc_trading_log.xlsx")
        except ImportError:
            print("openpyxl is required to save Excel files. Please install it with 'pip install openpyxl'.")
        except Exception as e:
            print(f"Error saving trade log: {e}")

if __name__ == "__main__":
    main()