"""
Backtesting engine for testing trading strategies
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Callable

class BacktestEngine:
    """Engine for backtesting trading strategies"""
    
    def __init__(self, 
                initial_capital: float = 100000.0,
                commission: float = 0.0,
                slippage: float = 0.0):
        """Initialize the backtest engine
        
        Args:
            initial_capital: Initial capital for the backtest
            commission: Commission rate (percentage)
            slippage: Slippage rate (percentage)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        self.portfolio_history = []
    
    def run(self, 
          data: Dict[str, pd.DataFrame],
          strategy_func: Callable[[Dict[str, pd.DataFrame], dict, datetime], Dict[str, Dict[str, Any]]]) -> pd.DataFrame:
        """Run a backtest
        
        Args:
            data: Dictionary mapping symbols to DataFrames with historical data
            strategy_func: Function that generates signals for each date
                Args: 
                    data: The same data dictionary passed to run()
                    positions: Current positions
                    date: Current date in the backtest
                Returns: 
                    Dictionary mapping symbols to dictionaries containing 'action' and optional params
            
        Returns:
            DataFrame with backtest results
        """
        # Get sorted list of all dates in the data
        all_dates = set()
        for symbol, df in data.items():
            all_dates.update(df.index)
        dates = sorted(list(all_dates))
        
        # Run the backtest for each date
        for date in dates:
            # Get current prices for all symbols
            current_prices = {}
            for symbol, df in data.items():
                if date in df.index:
                    current_prices[symbol] = df.loc[date, "close"]
            
            # Update portfolio value
            portfolio_value = self.capital
            for symbol, position in self.positions.items():
                if symbol in current_prices:
                    portfolio_value += position["qty"] * current_prices[symbol]
            
            # Record portfolio history
            self.portfolio_history.append({
                "date": date,
                "portfolio_value": portfolio_value
            })
            
            # Generate signals
            signals = strategy_func(data, self.positions, date)
            
            # Execute signals
            for symbol, signal in signals.items():
                if symbol not in current_prices:
                    continue
                    
                price = current_prices[symbol]
                
                if signal["action"] == "buy":
                    # Calculate number of shares to buy
                    qty = signal.get("qty", 1)
                    cost = qty * price * (1 + self.slippage)
                    commission_cost = cost * self.commission
                    total_cost = cost + commission_cost
                    
                    if total_cost <= self.capital:
                        # Record the trade
                        self.trades.append({
                            "date": date,
                            "symbol": symbol,
                            "action": "buy",
                            "qty": qty,
                            "price": price,
                            "cost": total_cost
                        })
                        
                        # Update positions and capital
                        if symbol in self.positions:
                            # Average down
                            total_qty = self.positions[symbol]["qty"] + qty
                            total_cost = self.positions[symbol]["cost"] + total_cost
                            avg_price = total_cost / total_qty
                            self.positions[symbol] = {
                                "qty": total_qty,
                                "avg_price": avg_price,
                                "cost": total_cost
                            }
                        else:
                            # New position
                            self.positions[symbol] = {
                                "qty": qty,
                                "avg_price": price,
                                "cost": total_cost
                            }
                        
                        self.capital -= total_cost
                    
                elif signal["action"] == "sell" and symbol in self.positions:
                    # Calculate number of shares to sell
                    max_qty = self.positions[symbol]["qty"]
                    qty = min(signal.get("qty", max_qty), max_qty)
                    revenue = qty * price * (1 - self.slippage)
                    commission_cost = revenue * self.commission
                    total_revenue = revenue - commission_cost
                    
                    # Record the trade
                    self.trades.append({
                        "date": date,
                        "symbol": symbol,
                        "action": "sell",
                        "qty": qty,
                        "price": price,
                        "revenue": total_revenue
                    })
                    
                    # Update positions and capital
                    if qty == max_qty:
                        # Close position
                        del self.positions[symbol]
                    else:
                        # Partial sell
                        self.positions[symbol]["qty"] -= qty
                        self.positions[symbol]["cost"] -= (qty / max_qty) * self.positions[symbol]["cost"]
                    
                    self.capital += total_revenue
        
        # Calculate final portfolio value
        final_portfolio_value = self.capital
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                final_portfolio_value += position["qty"] * current_prices[symbol]
        
        # Create results DataFrame
        results = pd.DataFrame(self.portfolio_history)
        results.set_index("date", inplace=True)
        
        # Calculate returns
        results["daily_return"] = results["portfolio_value"].pct_change()
        results["cumulative_return"] = (results["portfolio_value"] / self.initial_capital) - 1
        
        return results
    
    def get_trade_history(self) -> pd.DataFrame:
        """Get trade history as a DataFrame
        
        Returns:
            DataFrame with trade history
        """
        return pd.DataFrame(self.trades)
    
    def get_stats(self, results: pd.DataFrame) -> Dict[str, float]:
        """Calculate performance statistics
        
        Args:
            results: DataFrame with backtest results
            
        Returns:
            Dictionary of performance statistics
        """
        stats = {}
        
        # Basic stats
        stats["total_return"] = results["cumulative_return"].iloc[-1]
        stats["annual_return"] = (1 + stats["total_return"]) ** (252 / len(results)) - 1
        stats["sharpe_ratio"] = results["daily_return"].mean() / results["daily_return"].std() * (252 ** 0.5)
        stats["max_drawdown"] = (results["portfolio_value"] / results["portfolio_value"].cummax() - 1).min()
        stats["final_portfolio_value"] = results["portfolio_value"].iloc[-1]
        
        # Trade stats
        trades_df = self.get_trade_history()
        stats["number_of_trades"] = len(trades_df)
        
        if not trades_df.empty:
            buy_trades = trades_df[trades_df["action"] == "buy"]
            sell_trades = trades_df[trades_df["action"] == "sell"]
            stats["average_trade_size"] = buy_trades["cost"].mean() if not buy_trades.empty else 0
            
            # Simple estimate of winning trades - need proper P&L calculation per trade for accurate stats
            if not sell_trades.empty:
                sell_trades["profit"] = sell_trades.apply(
                    lambda x: x["revenue"] - (x["qty"] * self.positions.get(x["symbol"], {}).get("avg_price", 0)), 
                    axis=1
                )
                stats["win_rate"] = (sell_trades["profit"] > 0).mean()
                stats["average_profit"] = sell_trades["profit"].mean()
            else:
                stats["win_rate"] = 0
                stats["average_profit"] = 0
        
        return stats
