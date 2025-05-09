"""
Alpaca Trading API client implementation.
Uses the OpenAPI specification from /api/alpaca_openapi.json
"""

import os
import requests
import json
from typing import Dict, List, Optional, Union, Any

class AlpacaTradingClient:
    """Client for the Alpaca Trading API"""
    
    def __init__(self, api_key: str, api_secret: str, paper: bool = True):
        """Initialize the Alpaca Trading API client
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            paper: Whether to use the paper trading API (default: True)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
            "Content-Type": "application/json"
        }
    
    def get_account(self) -> Dict[str, Any]:
        """Get account information
        
        Returns:
            Account information
        """
        url = f"{self.base_url}/v2/account"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions
        
        Returns:
            List of positions
        """
        url = f"{self.base_url}/v2/positions"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_orders(self, status: str = "open", limit: int = 50) -> List[Dict[str, Any]]:
        """Get orders
        
        Args:
            status: Order status to be queried. Can be 'open', 'closed' or 'all'. Default is 'open'.
            limit: Maximum number of orders to return. Default is 50.
            
        Returns:
            List of orders
        """
        url = f"{self.base_url}/v2/orders"
        params = {
            "status": status,
            "limit": limit
        }
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def submit_order(self, 
                   symbol: str, 
                   qty: Optional[str] = None,
                   notional: Optional[str] = None,
                   side: str = "buy", 
                   type: str = "market",
                   time_in_force: str = "day",
                   limit_price: Optional[str] = None,
                   stop_price: Optional[str] = None,
                   extended_hours: bool = False,
                   client_order_id: Optional[str] = None,
                   order_class: Optional[str] = None,
                   take_profit: Optional[Dict[str, Any]] = None,
                   stop_loss: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Submit a new order
        
        Args:
            symbol: Symbol or asset ID to identify the asset to trade
            qty: Number of shares to trade
            notional: Dollar amount to trade. Cannot be used with qty.
            side: buy or sell
            type: market, limit, stop, stop_limit, trailing_stop
            time_in_force: day, gtc, opg, cls, ioc, fok
            limit_price: Required if type is limit or stop_limit
            stop_price: Required if type is stop or stop_limit
            extended_hours: If true, order will be eligible to execute in premarket/afterhours
            client_order_id: A unique identifier for the order
            order_class: simple, bracket, oco, oto
            take_profit: Additional parameters for take-profit leg of advanced orders
            stop_loss: Additional parameters for stop-loss leg of advanced orders
            
        Returns:
            Order information
        """
        url = f"{self.base_url}/v2/orders"
        
        # Build order data
        order_data = {
            "symbol": symbol,
            "side": side,
            "type": type,
            "time_in_force": time_in_force,
            "extended_hours": extended_hours
        }
        
        # Add quantity or notional
        if qty is not None:
            order_data["qty"] = qty
        elif notional is not None:
            order_data["notional"] = notional
        else:
            raise ValueError("Either qty or notional must be provided")
        
        # Add optional parameters
        if limit_price is not None:
            order_data["limit_price"] = limit_price
        if stop_price is not None:
            order_data["stop_price"] = stop_price
        if client_order_id is not None:
            order_data["client_order_id"] = client_order_id
        if order_class is not None:
            order_data["order_class"] = order_class
        if take_profit is not None:
            order_data["take_profit"] = take_profit
        if stop_loss is not None:
            order_data["stop_loss"] = stop_loss
            
        response = requests.post(url, headers=self.headers, json=order_data)
        response.raise_for_status()
        return response.json()
    
    def cancel_order(self, order_id: str) -> None:
        """Cancel an order
        
        Args:
            order_id: ID of the order to cancel
        """
        url = f"{self.base_url}/v2/orders/{order_id}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        
    def cancel_all_orders(self) -> List[Dict[str, Any]]:
        """Cancel all open orders
        
        Returns:
            List of canceled orders
        """
        url = f"{self.base_url}/v2/orders"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
