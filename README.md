# AlgoTrader

An algorithmic trading platform utilizing the Alpaca Markets API for implementing and backtesting trading strategies.

## Features

- Fully integrated with Alpaca Markets Trading and Market Data APIs
- Strategy implementation framework with simple extension pattern
- Backtesting engine with performance metrics
- Ready-to-use momentum trading strategy
- Support for both live and paper trading
- Configurable with command-line arguments

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables (create a `.env` file based on `.env.example`):
   ```
   ALPACA_API_KEY=your_alpaca_api_key
   ALPACA_API_SECRET=your_alpaca_api_secret
   ```

## Usage

### Live Trading

Run the AlgoTrader with the simple momentum strategy on default symbols in paper trading mode:

```bash
python main.py --paper
```

Specify your own symbols:

```bash
python main.py --paper --symbols "AAPL,MSFT,GOOGL,AMZN,NFLX"
```

### Creating Custom Strategies

To create a custom strategy, extend the base `Strategy` class:

1. Create a new file in the `src/strategy` directory
2. Implement the required methods: `setup()`, `generate_signals()`, and `execute()`
3. Update `main.py` to include your strategy

Example:

```python
from .base import Strategy

class MyCustomStrategy(Strategy):
    # Implement required methods
    # ...
```

## Project Structure

- `src/api/`: Alpaca API client implementations
  - `trading.py`: Trading API client
  - `market_data.py`: Market Data API client
- `src/strategy/`: Trading strategy implementations
  - `base.py`: Abstract base strategy class
  - `simple_momentum.py`: Momentum strategy implementation
- `src/backtest/`: Backtesting framework
  - `engine.py`: Backtesting engine
- `api/`: API specifications
  - `alpaca_openapi.json`: Alpaca Trading API spec
  - `alpaca_market_data_openapi.json`: Alpaca Market Data API spec
- `main.py`: Main entry point

## License

MIT# AlgoTrader
