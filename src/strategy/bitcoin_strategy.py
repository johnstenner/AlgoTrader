"""
Bitcoin trading strategy implementation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
import time

from .base import Strategy
from ..api.trading import AlpacaTradingClient
from ..api.market_data import AlpacaMarketDataClient

class BitcoinStrategy(Strategy):
    """Bitcoin trading strategy based on moving average crossovers and volatility"""
    
    def setup(self, 
             symbol: str = "BTC/USD", 
             fast_ma: int = 9, 
             slow_ma: int = 21,
             volume_window: int = 14,
             volatility_window: int = 20,
             volatility_threshold: float = 0.03,
             position_size: float = 0.1,
             market_symbol: Optional[str] = None):  # Add market_symbol
        """Set up the Bitcoin trading strategy
        
        Args:
            symbol: Crypto trading pair (default: BTC/USD)
            fast_ma: Fast moving average period
            slow_ma: Slow moving average period
            volume_window: Window for volume moving average
            volatility_threshold: Volatility threshold for risk management
            position_size: Size of position as fraction of available cash
            market_symbol: Optional market symbol to use for market data calls
        """
        self.symbols = [symbol]
        self.symbol = symbol
        self.market_symbol = market_symbol if market_symbol else symbol.replace("/", "")
        self.fast_ma = fast_ma
        self.slow_ma = slow_ma
        self.volume_window = volume_window
        self.volatility_window = volatility_window
        self.volatility_threshold = volatility_threshold
        self.position_size = position_size
        
        print(f"Bitcoin strategy initialized with {symbol}")
        print(f"Using {fast_ma}/{slow_ma} moving average crossover")
        
    def generate_signals(self) -> Dict[str, str]:
        """Generate trading signals based on moving average crossover
        and volume/volatility indicators
        
        Returns:
            Dictionary mapping symbols to signals ('buy', 'sell', 'hold')
        """
        signals = {}
        current_time = int(time.time())
        
        # Get historical data for the past 30 days with 1-hour bars
        one_month_ago = current_time - (30 * 24 * 60 * 60)  # 30 days in seconds
        
        try:
            # Format timestamps for API
            start_time = pd.Timestamp(one_month_ago, unit='s').isoformat()
            end_time = pd.Timestamp(current_time, unit='s').isoformat()
            
            # Fetch bars data (crypto)
            bars_data = self.market_data_client.get_crypto_bars(
                symbols=[self.market_symbol],
                timeframe="1Hour",
                limit=500  # Get enough data for calculations
            )
            
            # Check if we got data
            if self.market_symbol not in bars_data.get("bars", {}):
                print(f"No data available for {self.market_symbol}")
                signals[self.symbol] = "hold"
                return signals
                
            # Process data
            bars = bars_data["bars"][self.market_symbol]
            if len(bars) < self.slow_ma + 5:  # Need enough data for MA calculation
                print(f"Not enough data for {self.market_symbol} (got {len(bars)} bars)")
                signals[self.symbol] = "hold"
                return signals
                
            # Convert to pandas DataFrame for easier analysis
            df = pd.DataFrame(bars)
            
            # Calculate moving averages
            df['fast_ma'] = df['c'].rolling(window=self.fast_ma).mean()
            df['slow_ma'] = df['c'].rolling(window=self.slow_ma).mean()
            
            # Calculate volume indicators
            df['volume_ma'] = df['v'].rolling(window=self.volume_window).mean()
            df['volume_ratio'] = df['v'] / df['volume_ma']
            
            # Calculate volatility (using rolling standard deviation)
            df['volatility'] = df['c'].pct_change().rolling(window=self.volatility_window).std()
            
            # Signal generation
            # 1. Check if fast MA crosses above slow MA
            current_fast_ma = df['fast_ma'].iloc[-1]
            current_slow_ma = df['slow_ma'].iloc[-1]
            prev_fast_ma = df['fast_ma'].iloc[-2]
            prev_slow_ma = df['slow_ma'].iloc[-2]
            
            bullish_crossover = prev_fast_ma < prev_slow_ma and current_fast_ma > current_slow_ma
            bearish_crossover = prev_fast_ma > prev_slow_ma and current_fast_ma < current_slow_ma
            
            # 2. Check volume confirmation
            high_volume = df['volume_ratio'].iloc[-1] > 1.2  # Volume 20% above average
            
            # 3. Check volatility (avoid trading during extreme volatility)
            current_volatility = df['volatility'].iloc[-1]
            excessive_volatility = current_volatility > self.volatility_threshold
            
            # Generate signal
            if bullish_crossover and high_volume and not excessive_volatility:
                signals[self.symbol] = "buy"
                print(f"BUY signal for {self.symbol}: MA crossover with high volume confirmation")
            elif bearish_crossover or excessive_volatility:
                signals[self.symbol] = "sell"
                print(f"SELL signal for {self.symbol}: {'MA crossover' if bearish_crossover else 'High volatility'}")
            else:
                signals[self.symbol] = "hold"
                
        except Exception as e:
            print(f"Error generating signals for {self.symbol}: {str(e)}")
            signals[self.symbol] = "hold"
        
        return signals
    
    def execute(self, signals: Dict[str, str]) -> None:
        """Execute trades based on signals
        
        Args:
            signals: Dictionary mapping symbols to signals
        """
        try:
            # Get account information
            account = self.trading_client.get_account()
            available_cash = float(account["cash"])
            
            # Get current positions
            positions = {p["symbol"]: p for p in self.trading_client.get_positions()}
            
            # Get current price (crypto)
            latest_quote = self.market_data_client.get_crypto_latest_quote([self.market_symbol])
            if self.market_symbol not in latest_quote.get("quotes", {}):
                print(f"Could not get latest quote for {self.market_symbol}")
                return
                
            current_price = float(latest_quote["quotes"][self.market_symbol]["ap"])  # Ask price
            
            # Process signal
            signal = signals.get(self.symbol, "hold")
            
            if signal == "buy" and self.symbol not in positions:
                # Calculate position size
                position_cash = available_cash * self.position_size
                qty = position_cash / current_price
                
                # Format quantity with appropriate precision
                qty_str = f"{qty:.8f}"  # 8 decimal places for crypto
                
                # Place buy order
                self.trading_client.submit_order(
                    symbol=self.symbol,
                    qty=qty_str,
                    side="buy",
                    type="market",
                    time_in_force="gtc"  # Good till canceled
                )
                print(f"Buying {qty_str} {self.symbol} at approximately ${current_price}")
                
            elif signal == "sell" and self.symbol in positions:
                # Get position details
                pos = positions[self.symbol]
                qty = pos["qty"]
                
                # Place sell order
                self.trading_client.submit_order(
                    symbol=self.symbol,
                    qty=qty,
                    side="sell",
                    type="market",
                    time_in_force="gtc"
                )
                print(f"Selling {qty} {self.symbol} at approximately ${current_price}")
                
        except Exception as e:
            print(f"Error executing trades: {str(e)}")