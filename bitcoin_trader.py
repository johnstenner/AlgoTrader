"""
Bitcoin trading script for AlgoTrader
"""

import os
import argparse
import time
from datetime import datetime
from dotenv import load_dotenv

from src.api.trading import AlpacaTradingClient
from src.api.market_data import AlpacaMarketDataClient
from src.strategy.bitcoin_strategy import BitcoinStrategy

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="AlgoTrader - Bitcoin Trading")
    parser.add_argument("--paper", action="store_true", default=True, help="Use paper trading API (default: True)")
    parser.add_argument("--live", action="store_true", help="Use live trading API instead of paper")
    parser.add_argument("--symbol", type=str, default="BTC/USD", help="Crypto trading pair (default: BTC/USD)")
    parser.add_argument("--interval", type=int, default=3600, help="Trading interval in seconds (default: 3600 = 1 hour)")
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
    market_data_client = AlpacaMarketDataClient(api_key, api_secret)
    
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
    
    # Initialize Bitcoin strategy
    strategy = BitcoinStrategy(trading_client, market_data_client)
    strategy.setup(
        symbol=args.symbol,
        position_size=args.position_size
    )
    
    print(f"\nStarting Bitcoin trading bot for {args.symbol}")
    print(f"Trading interval: {args.interval} seconds")
    print(f"Position size: {args.position_size * 100}% of available cash")
    print(f"{'PAPER' if paper_trading else 'LIVE'} TRADING MODE")
    print("\nPress Ctrl+C to stop the trading bot...\n")
    
    # Trading loop
    try:
        while True:
            print(f"\n{'-' * 50}")
            print(f"Running strategy check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Run strategy
            strategy.run()
            
            # Get positions after running strategy
            positions = trading_client.get_positions()
            
            # Print current positions
            if positions:
                print("\nCurrent positions:")
                for position in positions:
                    market_value = float(position['market_value'])
                    entry_price = float(position['avg_entry_price'])
                    current_price = market_value / float(position['qty'])
                    profit_loss = (current_price - entry_price) / entry_price
                    
                    print(f"  {position['symbol']}: {position['qty']} shares at avg price ${entry_price:.2f}")
                    print(f"    Current value: ${market_value:.2f} ({profit_loss:.2%} {'profit' if profit_loss >= 0 else 'loss'})")
            else:
                print("\nNo open positions")
            
            # Wait for next interval
            next_check = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\nNext check at: {next_check}")
            print(f"Waiting for {args.interval} seconds...")
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\nTrading bot stopped by user")
    except Exception as e:
        print(f"\nError in trading loop: {str(e)}")
    finally:
        print("\nTrading bot shutdown complete")

if __name__ == "__main__":
    main()