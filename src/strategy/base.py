"""
Base strategy classes for implementing trading strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
import pandas as pd

from ..api.trading import AlpacaTradingClient
from ..api.market_data import AlpacaMarketDataClient

class Strategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, 
                trading_client: AlpacaTradingClient,
                market_data_client: AlpacaMarketDataClient):
        """Initialize the strategy
        
        Args:
            trading_client: Alpaca Trading API client
            market_data_client: Alpaca Market Data API client
        """
        self.trading_client = trading_client
        self.market_data_client = market_data_client
        self.symbols = []
    
    @abstractmethod
    def setup(self, **kwargs) -> None:
        """Set up the strategy with any required parameters"""
        pass
    
    @abstractmethod
    def generate_signals(self) -> Dict[str, str]:
        """Generate trading signals
        
        Returns:
            Dictionary mapping symbols to signals (e.g., 'buy', 'sell', 'hold')
        """
        pass
    
    @abstractmethod
    def execute(self, signals: Dict[str, str]) -> None:
        """Execute trades based on signals
        
        Args:
            signals: Dictionary mapping symbols to signals
        """
        pass
    
    def run(self) -> None:
        """Run one iteration of the strategy"""
        signals = self.generate_signals()
        self.execute(signals)
