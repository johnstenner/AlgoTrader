import pandas as pd

class RSIStrategy:
    def __init__(self, trading_client, fetch_closes_func, symbol, rsi_period=14, overbought=69, oversold=30):
        self.trading_client = trading_client
        self.fetch_closes_func = fetch_closes_func  # function to fetch historical closes
        self.symbol = symbol
        self.rsi_period = rsi_period
        self.overbought = overbought
        self.oversold = oversold

    def calculate_rsi(self, closes):
        # Calculate RSI using pandas
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signal(self):
        closes = self.fetch_closes_func(self.symbol)
        closes = pd.Series(closes)
        rsi = self.calculate_rsi(closes)
        latest_rsi = rsi.iloc[-1]
        print(f"Latest RSI({self.rsi_period}) for {self.symbol}: {latest_rsi:.2f}")
        if latest_rsi < self.oversold:
            return 'buy', latest_rsi
        elif latest_rsi > self.overbought:
            return 'sell', latest_rsi
        else:
            return 'hold', latest_rsi

    def run(self):
        signal, rsi_value = self.generate_signal()
        return signal, rsi_value 