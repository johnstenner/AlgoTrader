"""
Main entry point for AlgoTrader
"""

import os
import argparse
from dotenv import load_dotenv

from src.api.trading import AlpacaTradingClient
from src.api.market_data import AlpacaMarketDataClient
from src.strategy.simple_momentum import SimpleMomentum

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="AlgoTrader - Algorithmic Trading Platform")
    parser.add_argument("--symbols", type=str, help="Comma-separated list of symbols to trade")
    parser.add_argument("--backtest", action="store_true", help="Run in backtest mode")
    parser.add_argument("--paper", action="store_true", help="Use paper trading API")
    parser.add_argument("--strategy", type=str, default="momentum", help="Trading strategy to use")
    
    args = parser.parse_args()
    
    # Get API credentials from environment variables
    api_key = os.getenv("ALPACA_API_KEY")
    api_secret = os.getenv("ALPACA_API_SECRET")
    
    if not api_key or not api_secret:
        raise ValueError("ALPACA_API_KEY and ALPACA_API_SECRET must be set in environment variables or .env file")
    
    # Parse symbols
    symbols = [s.strip() for s in args.symbols.split(",")] if args.symbols else ["SPY", "AAPL", "MSFT", "GOOGL", "AMZN"]
    
    # Initialize API clients
    trading_client = AlpacaTradingClient(api_key, api_secret, paper=args.paper)
    market_data_client = AlpacaMarketDataClient(api_key, api_secret)
    
    # Get account information
    account = trading_client.get_account()
    print(f"Account ID: {account['id']}")
    print(f"Cash: ${float(account['cash']):.2f}")
    print(f"Portfolio Value: ${float(account['portfolio_value']):.2f}")
    
    if args.backtest:
        # Run in backtest mode
        print("Running in backtest mode...")
        # TODO: Implement backtest runner
    else:
        # Run in live trading mode
        print(f"Running {args.strategy} strategy on {', '.join(symbols)} in {'paper' if args.paper else 'live'} mode...")
        
        # Initialize and run the selected strategy
        if args.strategy.lower() == "momentum":
            strategy = SimpleMomentum(trading_client, market_data_client)
            strategy.setup(symbols=symbols)
            strategy.run()
        else:
            print(f"Strategy '{args.strategy}' not implemented")

if __name__ == "__main__":
    main()
