#!/usr/bin/env python3
"""
MLflow experiment for HFT strategy backtesting
This script demonstrates how to use MLflow for tracking trading strategy performance
"""

import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import clickhouse_connect
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HFTStrategyBacktest:
    def __init__(self, mlflow_tracking_uri="http://localhost:5000"):
        """
        Initialize HFT Strategy Backtest with MLflow tracking
        
        Args:
            mlflow_tracking_uri: MLflow tracking server URI
        """
        self.mlflow_tracking_uri = mlflow_tracking_uri
        self.client = None
        
    def connect_to_clickhouse(self, host="localhost", port=8124):
        """Connect to ClickHouse database"""
        try:
            self.client = clickhouse_connect.get_client(
                host=host,
                port=port,
                user='default',
                password=''
            )
            logger.info("Connected to ClickHouse")
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            raise
    
    def load_aggregated_data(self, symbol="BTC-USDT", days_back=30):
        """
        Load aggregated HFT data from ClickHouse
        
        Args:
            symbol: Trading symbol
            days_back: Number of days to look back
            
        Returns:
            pandas.DataFrame: Aggregated data
        """
        if not self.client:
            raise Exception("ClickHouse client not initialized")
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        
        query = f"""
        SELECT 
            timestamp,
            symbol,
            open_price,
            high_price,
            low_price,
            close_price,
            volume,
            trade_count,
            spread
        FROM hft_analytics.agg_1s
        WHERE symbol = '{symbol}'
        AND timestamp >= '{start_time}'
        AND timestamp <= '{end_time}'
        ORDER BY timestamp
        """
        
        try:
            data = self.client.query_df(query)
            logger.info(f"Loaded {len(data)} aggregated records for {symbol}")
            return data
        except Exception as e:
            logger.error(f"Failed to load aggregated data: {e}")
            raise
    
    def calculate_technical_indicators(self, data):
        """
        Calculate technical indicators for strategy
        
        Args:
            data: Price data
            
        Returns:
            pandas.DataFrame: Data with technical indicators
        """
        # Moving averages
        data['sma_5'] = data['close_price'].rolling(window=5).mean()
        data['sma_20'] = data['close_price'].rolling(window=20).mean()
        data['ema_12'] = data['close_price'].ewm(span=12).mean()
        data['ema_26'] = data['close_price'].ewm(span=26).mean()
        
        # MACD
        data['macd'] = data['ema_12'] - data['ema_26']
        data['macd_signal'] = data['macd'].ewm(span=9).mean()
        data['macd_histogram'] = data['macd'] - data['macd_signal']
        
        # RSI
        delta = data['close_price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        data['bb_middle'] = data['close_price'].rolling(window=20).mean()
        bb_std = data['close_price'].rolling(window=20).std()
        data['bb_upper'] = data['bb_middle'] + (bb_std * 2)
        data['bb_lower'] = data['bb_middle'] - (bb_std * 2)
        data['bb_width'] = data['bb_upper'] - data['bb_lower']
        data['bb_position'] = (data['close_price'] - data['bb_lower']) / (data['bb_upper'] - data['bb_lower'])
        
        # Volume indicators
        data['volume_sma'] = data['volume'].rolling(window=20).mean()
        data['volume_ratio'] = data['volume'] / data['volume_sma']
        
        # Price momentum
        data['momentum_5'] = data['close_price'] / data['close_price'].shift(5) - 1
        data['momentum_10'] = data['close_price'] / data['close_price'].shift(10) - 1
        
        return data
    
    def generate_signals(self, data):
        """
        Generate trading signals based on technical indicators
        
        Args:
            data: Data with technical indicators
            
        Returns:
            pandas.DataFrame: Data with trading signals
        """
        # Initialize signals
        data['signal'] = 0
        data['position'] = 0
        
        # Buy signals
        buy_conditions = (
            (data['close_price'] > data['sma_20']) &  # Price above SMA
            (data['macd'] > data['macd_signal']) &   # MACD bullish
            (data['rsi'] < 70) &                      # RSI not overbought
            (data['bb_position'] < 0.8) &           # Not near upper BB
            (data['volume_ratio'] > 1.2)             # High volume
        )
        
        # Sell signals
        sell_conditions = (
            (data['close_price'] < data['sma_20']) |  # Price below SMA
            (data['macd'] < data['macd_signal']) |  # MACD bearish
            (data['rsi'] > 30) |                     # RSI not oversold
            (data['bb_position'] > 0.2) |            # Not near lower BB
            (data['volume_ratio'] < 0.8)             # Low volume
        )
        
        data.loc[buy_conditions, 'signal'] = 1
        data.loc[sell_conditions, 'signal'] = -1
        
        # Calculate positions (simple strategy: buy on signal=1, sell on signal=-1)
        data['position'] = data['signal'].shift(1).fillna(0)
        
        return data
    
    def calculate_returns(self, data, initial_capital=10000):
        """
        Calculate strategy returns
        
        Args:
            data: Data with signals and positions
            initial_capital: Starting capital
            
        Returns:
            pandas.DataFrame: Data with returns
        """
        # Calculate price returns
        data['price_return'] = data['close_price'].pct_change()
        
        # Calculate strategy returns
        data['strategy_return'] = data['position'] * data['price_return']
        
        # Calculate cumulative returns
        data['cumulative_return'] = (1 + data['strategy_return']).cumprod()
        data['cumulative_price_return'] = (1 + data['price_return']).cumprod()
        
        # Calculate portfolio value
        data['portfolio_value'] = initial_capital * data['cumulative_return']
        data['price_value'] = initial_capital * data['cumulative_price_return']
        
        return data
    
    def calculate_metrics(self, data):
        """
        Calculate performance metrics
        
        Args:
            data: Data with returns
            
        Returns:
            dict: Performance metrics
        """
        # Remove NaN values
        data_clean = data.dropna()
        
        if len(data_clean) == 0:
            return {}
        
        # Basic metrics
        total_return = data_clean['cumulative_return'].iloc[-1] - 1
        price_return = data_clean['cumulative_price_return'].iloc[-1] - 1
        
        # Risk metrics
        strategy_returns = data_clean['strategy_return']
        price_returns = data_clean['price_return']
        
        volatility = strategy_returns.std() * np.sqrt(252 * 24 * 3600)  # Annualized
        sharpe_ratio = (strategy_returns.mean() * 252 * 24 * 3600) / (strategy_returns.std() * np.sqrt(252 * 24 * 3600))
        
        # Drawdown
        cumulative = data_clean['cumulative_return']
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Win rate
        winning_trades = (strategy_returns > 0).sum()
        total_trades = (strategy_returns != 0).sum()
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Average trade
        avg_win = strategy_returns[strategy_returns > 0].mean() if winning_trades > 0 else 0
        avg_loss = strategy_returns[strategy_returns < 0].mean() if (total_trades - winning_trades) > 0 else 0
        
        return {
            'total_return': total_return,
            'price_return': price_return,
            'excess_return': total_return - price_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            'total_trades': total_trades
        }
    
    def run_backtest(self, symbol="BTC-USDT", days_back=30, initial_capital=10000):
        """
        Run complete strategy backtest with MLflow tracking
        
        Args:
            symbol: Trading symbol
            days_back: Number of days to look back
            initial_capital: Starting capital
        """
        try:
            # Connect to ClickHouse
            self.connect_to_clickhouse()
            
            # Load data
            data = self.load_aggregated_data(symbol, days_back)
            
            if len(data) < 100:
                logger.warning(f"Not enough data for {symbol}. Found {len(data)} records.")
                return
            
            # Calculate technical indicators
            data = self.calculate_technical_indicators(data)
            
            # Generate signals
            data = self.generate_signals(data)
            
            # Calculate returns
            data = self.calculate_returns(data, initial_capital)
            
            # Calculate metrics
            metrics = self.calculate_metrics(data)
            
            # Set MLflow tracking URI
            mlflow.set_tracking_uri(self.mlflow_tracking_uri)
            
            # Start MLflow run
            with mlflow.start_run(run_name=f"HFT_Strategy_{symbol}") as run:
                # Log parameters
                mlflow.log_param("symbol", symbol)
                mlflow.log_param("days_back", days_back)
                mlflow.log_param("initial_capital", initial_capital)
                mlflow.log_param("strategy", "Technical_Indicators")
                
                # Log metrics
                for metric_name, metric_value in metrics.items():
                    if not np.isnan(metric_value) and not np.isinf(metric_value):
                        mlflow.log_metric(metric_name, metric_value)
                
                # Log strategy performance
                mlflow.log_text(
                    f"Strategy Performance for {symbol}\n"
                    f"Total Return: {metrics.get('total_return', 0):.4f}\n"
                    f"Price Return: {metrics.get('price_return', 0):.4f}\n"
                    f"Excess Return: {metrics.get('excess_return', 0):.4f}\n"
                    f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.4f}\n"
                    f"Max Drawdown: {metrics.get('max_drawdown', 0):.4f}\n"
                    f"Win Rate: {metrics.get('win_rate', 0):.4f}\n"
                    f"Total Trades: {metrics.get('total_trades', 0)}\n",
                    "strategy_performance.txt"
                )
                
                # Log sample data
                sample_data = data[['timestamp', 'close_price', 'signal', 'position', 'strategy_return', 'cumulative_return']].head(100)
                mlflow.log_text(sample_data.to_string(), "sample_data.txt")
                
                logger.info(f"Backtest completed and logged to MLflow. Run ID: {run.info.run_id}")
                logger.info(f"Strategy Performance - Return: {metrics.get('total_return', 0):.4f}, Sharpe: {metrics.get('sharpe_ratio', 0):.4f}")
                
                return metrics
                
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            raise

def main():
    """Main function to run HFT strategy backtest"""
    backtest = HFTStrategyBacktest()
    
    # Run backtest for different symbols
    symbols = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
    
    for symbol in symbols:
        logger.info(f"Running backtest for {symbol}")
        try:
            metrics = backtest.run_backtest(symbol=symbol, days_back=30, initial_capital=10000)
            logger.info(f"Backtest completed for {symbol}: {metrics}")
        except Exception as e:
            logger.error(f"Failed to run backtest for {symbol}: {e}")
            continue

if __name__ == "__main__":
    main()
