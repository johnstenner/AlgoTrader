"""
Alpaca Market Data API client implementation.
Uses the OpenAPI specification from /api/alpaca_market_data_openapi.json
"""

import os
import requests
import json
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, date

class AlpacaMarketDataClient:
    """Client for the Alpaca Market Data API"""
    
    def __init__(self, api_key: str, api_secret: str, sandbox: bool = False):
        """Initialize the Alpaca Market Data API client
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            sandbox: Whether to use the sandbox API (default: False)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://data.sandbox.alpaca.markets" if sandbox else "https://data.alpaca.markets"
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret
        }
    
    def get_stock_bars(self, 
                    symbols: List[str], 
                    timeframe: str = "1Day",
                    start: Optional[str] = None,
                    end: Optional[str] = None,
                    limit: int = 1000,
                    adjustment: str = "raw") -> Dict[str, Any]:
        """Get historical stock bars
        
        Args:
            symbols: List of symbols
            timeframe: Time frame for the bars (e.g., 1Min, 5Min, 15Min, 1Hour, 1Day)
            start: Start date/time in RFC-3339 format
            end: End date/time in RFC-3339 format
            limit: Maximum number of bars to return
            adjustment: Adjustment type (raw, split, dividend, all)
            
        Returns:
            Dictionary containing bar data for each symbol
        """
        url = f"{self.base_url}/v1/stocks/bars"
        params = {
            "symbols": ",".join(symbols),
            "timeframe": timeframe,
            "limit": limit,
            "adjustment": adjustment
        }
        
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
            
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_stock_latest_trade(self, symbols: List[str]) -> Dict[str, Any]:
        """Get latest trade for each symbol
        
        Args:
            symbols: List of symbols
            
        Returns:
            Dictionary containing latest trade data for each symbol
        """
        url = f"{self.base_url}/v1/stocks/trades/latest"
        params = {
            "symbols": ",".join(symbols)
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_stock_latest_quote(self, symbols: List[str]) -> Dict[str, Any]:
        """Get latest quote for each symbol
        
        Args:
            symbols: List of symbols
            
        Returns:
            Dictionary containing latest quote data for each symbol
        """
        url = f"{self.base_url}/v1/stocks/quotes/latest"
        params = {
            "symbols": ",".join(symbols)
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_news(self, 
              symbols: Optional[List[str]] = None,
              start: Optional[str] = None,
              end: Optional[str] = None,
              limit: int = 10,
              include_content: bool = False) -> Dict[str, Any]:
        """Get news articles
        
        Args:
            symbols: Optional list of symbols to get news for
            start: Start date/time in RFC-3339 format
            end: End date/time in RFC-3339 format
            limit: Maximum number of news articles to return
            include_content: Whether to include the content of news articles
            
        Returns:
            Dictionary containing news data
        """
        url = f"{self.base_url}/v1beta1/news"
        params = {
            "limit": limit,
            "include_content": include_content
        }
        
        if symbols is not None:
            params["symbols"] = ",".join(symbols)
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
            
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_market_movers(self, market_type: str = "stocks") -> Dict[str, Any]:
        """Get market movers (gainers and losers)
        
        Args:
            market_type: Market type (stocks or crypto)
            
        Returns:
            Dictionary containing market movers data
        """
        url = f"{self.base_url}/v1beta1/screener/{market_type}/movers"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_most_actives(self, market_type: str = "stocks") -> Dict[str, Any]:
        """Get most active symbols
        
        Args:
            market_type: Market type (stocks or crypto)
            
        Returns:
            Dictionary containing most active symbols data
        """
        url = f"{self.base_url}/v1beta1/screener/{market_type}/movers/most_actives"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
