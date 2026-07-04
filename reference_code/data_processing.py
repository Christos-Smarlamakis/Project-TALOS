from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
from datetime import datetime
from pandas.tseries.offsets import BDay

class stock_reader():
    def __init__(self, stock, train_start, train_days, trade_days, timeframes=[1, 2, 5, 10, 20, 40]):
        self.timeframes = timeframes
        self.stock_path = rf'\{stock}.csv' #The path to the file with the data within ''
        self.data = None
        self.scaler = StandardScaler()
        self.train_start = datetime.strptime(train_start, '%m/%d/%Y %H:%M')
        self.train_start = pd.to_datetime(self.train_start)
        self.train_end = (self.train_start + BDay(train_days - 1)).replace(hour=16, minute=0)
        self.trade_start = (self.train_end + BDay(1)).replace(hour=9, minute=30)
        self.trade_end = (self.trade_start + BDay(trade_days - 1)).replace(hour=16, minute=0)

    def read_csv_file(self):
        self.data = pd.read_csv(self.stock_path)
        self.data['DateTime'] = pd.to_datetime(self.data['timestamp'], errors='coerce')
        self.data.set_index('DateTime', inplace=True)

        self.data = self.data.loc[self.train_start:self.trade_end]

        # Explicitly cast columns to float
        self.data = self.data.astype({'volume': 'float64', 'close': 'float64'})

        # Check for NaN values
        nan_rows = self.data[self.data.isnull().any(axis=1)]
        if not nan_rows.empty:
            print("Γραμμές με NaN τιμές μετά την εφαρμογή του φίλτρου:")
            print(nan_rows)

        # Calculate pct_change
        for i in self.timeframes:
            if len(self.data) >= i:
                self.data[f"v-{i}"] = self.data['volume'].pct_change(i)
                self.data[f"r-{i}"] = self.data['close'].pct_change(i)
            else:
                self.data[f"v-{i}"] = np.nan
                self.data[f"r-{i}"] = np.nan

        # Calculate rolling volatility
        for i in [2, 5, 10, 20, 40]:
            if len(self.data) >= i:
                self.data[f'sig-{i}'] = np.log(1 + self.data["r-1"]).rolling(i).std()
            else:
                self.data[f'sig-{i}'] = np.nan

        # Calculate Bollinger Bands
        self.bollinger_lback = 10
        if len(self.data) >= self.bollinger_lback:
            self.data["bollinger"] = self.data["r-1"].ewm(self.bollinger_lback).mean()
            self.data["low_bollinger"] = self.data["bollinger"] - 2 * self.data["r-1"].rolling(self.bollinger_lback).std()
            self.data["high_bollinger"] = self.data["bollinger"] + 2 * self.data["r-1"].rolling(self.bollinger_lback).std()
        else:
            self.data["bollinger"] = np.nan
            self.data["low_bollinger"] = np.nan
            self.data["high_bollinger"] = np.nan

        # Calculate RSI
        self.rsi_lb = 5
        if len(self.data) >= self.rsi_lb:
            self.pos_gain = self.data["r-1"].where(self.data["r-1"] > 0, 0).ewm(self.rsi_lb).mean()
            self.neg_gain = self.data["r-1"].where(self.data["r-1"] < 0, 0).ewm(self.rsi_lb).mean()
            self.rs = np.abs(self.pos_gain / self.neg_gain)
            self.data["rsi"] = 100 * self.rs / (1 + self.rs)
        else:
            self.data["rsi"] = np.nan

        # Calculate MACD
        self.data["macd_lmw"] = self.data["r-1"].ewm(span=20, adjust=False).mean()
        self.data["macd_smw"] = self.data["r-1"].ewm(span=12, adjust=False).mean()
        self.data["macd_bl"] = self.data["r-1"].ewm(span=9, adjust=False).mean()
        self.data["macd"] = self.data["macd_smw"] - self.data["macd_lmw"]
        self.data["macd_signal"] = self.data["macd"].ewm(span=9, adjust=False).mean()
        self.data["macd_histogram"] = self.data["macd"] - self.data["macd_signal"]

        # Calculate STC
        if len(self.data) >= 9:
            macd_range = self.data["macd"].rolling(window=9).max() - self.data["macd"].rolling(window=9).min()
            self.data["stc"] = 100 * (self.data["macd"] - self.data["macd"].rolling(window=9).min()) / macd_range
            self.data["stc_smoothed"] = self.data["stc"].rolling(window=3).mean()
        else:
            self.data["stc"] = np.nan
            self.data["stc_smoothed"] = np.nan

        # Calculate TR
        if len(self.data) > 1:
            self.data['HL'] = self.data['high'] - self.data['low']
            self.data['HC'] = abs(self.data['high'] - self.data['close'].shift(-1))
            self.data['LC'] = abs(self.data['high'] - self.data['close'].shift(-1))
            self.data['TR'] = self.data[['HL', 'HC', 'LC']].max(axis=1)
            self.data.drop(['HL', 'HC', 'LC'], axis=1, inplace=True)
        else:
            self.data['TR'] = np.nan

        # Calculate Stochastic Oscillator
        if len(self.data) >= 14:
            self.data['Lowest_Low'] = self.data['low'].rolling(window=14).min()
            self.data['Highest_High'] = self.data['high'].rolling(window=14).max()
            self.data['%K'] = ((self.data['close'] - self.data['Lowest_Low']) / (
                        self.data['Highest_High'] - self.data['Lowest_Low'])) * 100
            self.data['%D'] = self.data['%K'].rolling(window=3).mean()
        else:
            self.data['Lowest_Low'] = np.nan
            self.data['Highest_High'] = np.nan
            self.data['%K'] = np.nan
            self.data['%D'] = np.nan

        # Calculate ATR
        self.atr_period = 11
        if len(self.data) >= self.atr_period:
            self.data['ATR'] = self.data['TR'].rolling(window=self.atr_period).mean()
        else:
            self.data['ATR'] = np.nan

        # Calculate next_state_return
        if len(self.data) > 1:
            self.data['next_state_return'] = self.data['close'].pct_change().shift(-1)
        else:
            self.data['next_state_return'] = np.nan

        # Exclude non-numeric columns from normalization
        columns_to_normalize = self.data.select_dtypes(include=[np.float64, np.int64]).columns.difference(['close'])

        # columns_to_normalize = self.data.select_dtypes(include=[np.float64, np.int64]).columns
        self.data[columns_to_normalize] = self.scaler.fit_transform(self.data[columns_to_normalize])

        # Fill NaN values with zeros
        self.data.fillna(0, inplace=True)

        self.train_days = self.data.loc[self.train_start:self.train_end].copy()
        self.trade_days = self.data.loc[self.trade_start:self.trade_end].copy()

        # Exclude non-numeric columns from mean and std calculations
        numeric_columns = self.train_days.select_dtypes(include=[np.float64, np.int64]).columns

        self.train_mean = self.train_days[numeric_columns].mean()
        self.train_std = self.train_days[numeric_columns].std()

        for column in numeric_columns:
            self.train_days[f"{column}_norm"] = (self.train_days[column] - self.train_mean[column]) / self.train_std[
                column]
            self.trade_days[f"{column}_norm"] = (self.trade_days[column] - self.train_mean[column]) / self.train_std[
                column]
            self.data[f"{column}_norm"] = (self.data[column] - self.train_mean[column]) / self.train_std[column]
