"""
Simple momentum strategy implementation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any

from .base import Strategy
from ..api.trading import AlpacaTradingClient
from ..api.market_data import AlpacaMarketDataClient

class SimpleMomentum(Strategy):
    """Simple momentum strategy that buys stocks with positive momentum
    and sells stocks with negative momentum"""
    
    def setup(self, symbols: List[str], lookback_days: int = 20, momentum_threshold: float = 0.05):
        """Set up the momentum strategy
        
        Args:
            symbols: List of symbols to trade
            lookback_days: Number of days to look back for calculating momentum
            momentum_threshold: Threshold for considering significant momentum
        """
        self.symbols = symbols
        self.lookback_days = lookback_days
        self.momentum_threshold = momentum_threshold
    
    def generate_signals(self) -> Dict[str, str]:
        """Generate trading signals based on momentum
        
        Returns:
            Dictionary mapping symbols to signals ('buy', 'sell', 'hold')
        """
        signals = {}
        
        # Get historical data for all symbols
        bars_data = self.market_data_client.get_stock_bars(
            symbols=self.symbols,
            timeframe="1Day",
            limit=self.lookback_days
        )
        
        # Calculate momentum for each symbol
        for symbol in self.symbols:
            if symbol not in bars_data.get("bars", {}):
                signals[symbol] = "hold"
                continue
                
            bars = bars_data["bars"][symbol]
            if len(bars) < self.lookback_days:
                signals[symbol] = "hold"
                continue
                
            # Extract closing prices
            closes = [bar["c"] for bar in bars]
            
            # Calculate momentum (percentage change over the lookback period)
            start_price = closes[0]
            end_price = closes[-1]
            momentum = (end_price - start_price) / start_price
            
            # Generate signal based on momentum
            if momentum > self.momentum_threshold:
                signals[symbol] = "buy"
            elif momentum < -self.momentum_threshold:
                signals[symbol] = "sell"
            else:
                signals[symbol] = "hold"
        
        return signals
    
    def execute(self, signals: Dict[str, str]) -> None:
        """Execute trades based on signals
        
        Args:
            signals: Dictionary mapping symbols to signals
        """
        # Get current positions
        positions = {p["symbol"]: p for p in self.trading_client.get_positions()}
        
        for symbol, signal in signals.items():
            if signal == "buy" and symbol not in positions:
                # Buy if we don't already have a position
                self.trading_client.submit_order(
                    symbol=symbol,
                    qty="1",  # Can be adjusted based on portfolio size/risk
                    side="buy",
                    type="market",
                    time_in_force="day"
                )
                print(f"Buying {symbol}")
                
            elif signal == "sell" and symbol in positions:
                # Sell if we have a position
                self.trading_client.submit_order(
                    symbol=symbol,
                    qty=positions[symbol]["qty"],
                    side="sell",
                    type="market",
                    time_in_force="day"
                )
                print(f"Selling {symbol}")
