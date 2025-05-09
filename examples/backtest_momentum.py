"""
Example script demonstrating how to use the backtesting engine with the momentum strategy
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.market_data import AlpacaMarketDataClient
from src.backtest.engine import BacktestEngine

def fetch_historical_data(api_key, api_secret, symbols, start_date, end_date):
    """Fetch historical data from Alpaca and convert to pandas DataFrames
    
    Args:
        api_key: Alpaca API key
        api_secret: Alpaca API secret
        symbols: List of symbols to fetch data for
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        Dictionary mapping symbols to DataFrames with historical data
    """
    client = AlpacaMarketDataClient(api_key, api_secret)
    
    # Fetch data
    bars_data = client.get_stock_bars(
        symbols=symbols,
        timeframe="1Day",
        start=start_date,
        end=end_date,
        adjustment="all"  # Apply split and dividend adjustments
    )
    
    data = {}
    for symbol in symbols:
        if symbol not in bars_data.get("bars", {}):
            print(f"No data found for {symbol}")
            continue
            
        bars = bars_data["bars"][symbol]
        
        # Convert to DataFrame
        df = pd.DataFrame(bars)
        df.rename(columns={"t": "timestamp", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"}, inplace=True)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        
        data[symbol] = df
    
    return data

def momentum_strategy(data, positions, current_date):
    """Simple momentum strategy for backtesting
    
    Args:
        data: Dictionary mapping symbols to DataFrames with historical data
        positions: Current positions
        current_date: Current date in the backtest
        
    Returns:
        Dictionary mapping symbols to signal dictionaries
    """
    signals = {}
    lookback_days = 20
    momentum_threshold = 0.05
    
    for symbol, df in data.items():
        # Get data up to current date
        df_subset = df[:current_date]
        if len(df_subset) < lookback_days:
            continue
            
        # Get closing prices for the lookback period
        closes = df_subset["close"].values[-lookback_days:]
        
        # Calculate momentum
        start_price = closes[0]
        end_price = closes[-1]
        momentum = (end_price - start_price) / start_price
        
        # Generate signal based on momentum
        if momentum > momentum_threshold and symbol not in positions:
            # Strong positive momentum and no position -> buy
            signals[symbol] = {"action": "buy", "qty": 10}  # Buy 10 shares
        elif momentum < -momentum_threshold and symbol in positions:
            # Strong negative momentum and have position -> sell
            signals[symbol] = {"action": "sell"}  # Sell all shares
    
    return signals

def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ALPACA_API_KEY")
    api_secret = os.getenv("ALPACA_API_SECRET")
    
    if not api_key or not api_secret:
        raise ValueError("ALPACA_API_KEY and ALPACA_API_SECRET must be set in environment variables or .env file")
    
    # Set up backtest parameters
    symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")  # 1 year of data
    
    # Fetch historical data
    print(f"Fetching historical data for {', '.join(symbols)} from {start_date} to {end_date}...")
    data = fetch_historical_data(api_key, api_secret, symbols, start_date, end_date)
    
    # Initialize backtest engine
    engine = BacktestEngine(
        initial_capital=100000.0,  # $100,000 initial capital
        commission=0.001,          # 0.1% commission
        slippage=0.001             # 0.1% slippage
    )
    
    # Run backtest
    print("Running backtest...")
    results = engine.run(data, momentum_strategy)
    
    # Calculate and print statistics
    stats = engine.get_stats(results)
    print("\nBacktest Results:")
    print(f"Total Return: {stats['total_return']:.2%}")
    print(f"Annual Return: {stats['annual_return']:.2%}")
    print(f"Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {stats['max_drawdown']:.2%}")
    print(f"Final Portfolio Value: ${stats['final_portfolio_value']:.2f}")
    print(f"Number of Trades: {stats['number_of_trades']}")
    
    # Get trade history
    trades = engine.get_trade_history()
    print("\nTrade History:")
    print(trades)
    
    # Plot results
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(12, 6))
        plt.plot(results.index, results["portfolio_value"])
        plt.title("Portfolio Value Over Time")
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value ($)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("backtest_results.png")
        print("\nBacktest results plot saved to backtest_results.png")
    except ImportError:
        print("\nMatplotlib not available. Skipping plot generation.")

if __name__ == "__main__":
    main()