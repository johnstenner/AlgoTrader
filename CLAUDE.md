# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AlgoTrader is an algorithmic trading platform built with Python that utilizes the Alpaca Markets API. It provides a framework for implementing and backtesting trading strategies.

## Command Reference

### Development Commands

- **Run in paper trading mode**: `python main.py --paper`
- **Run with specific symbols**: `python main.py --paper --symbols "AAPL,MSFT,GOOGL,AMZN,NFLX"`
- **Run with a specific strategy**: `python main.py --paper --strategy momentum`
- **Code formatting**: `black .`
- **Linting**: `pylint src/`

### Testing

- While testing is not yet implemented, the intention is to use pytest for unit testing.

## Architecture Notes

### Core Components

1. **API Clients**
   - `AlpacaTradingClient`: Handles authentication and requests to the Alpaca Trading API
   - `AlpacaMarketDataClient`: Handles authentication and requests to the Alpaca Market Data API

2. **Strategy Framework**
   - `Strategy` (abstract base class): Defines the interface for all trading strategies
   - Strategy implementations must implement:
     - `setup()`: Initialize the strategy with parameters
     - `generate_signals()`: Analyze market data and generate trading signals
     - `execute()`: Execute trades based on signals

3. **Backtesting Engine**
   - `BacktestEngine`: Simulates strategy execution on historical data
   - Tracks portfolio value, positions, and trades
   - Calculates performance metrics (returns, Sharpe ratio, drawdowns)

### Data Flow

1. Market data is fetched from Alpaca's API
2. Data is passed to the strategy for analysis
3. Strategy generates trading signals (buy, sell, hold)
4. Signals are executed as orders via the Trading API

### API Usage

The project uses two main Alpaca APIs:
- Trading API: For account data and order management
- Market Data API: For historical and real-time market data

API specifications are stored in:
- `/api/alpaca_openapi.json`
- `/api/alpaca_market_data_openapi.json`

### Key Implementation Details

- Authentication is handled via API keys stored in environment variables
- The project follows the Repository Pattern for API interactions
- Strategies follow the Strategy Pattern for easy extension
- The platform supports both paper trading (simulation) and live trading