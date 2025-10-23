#!/usr/bin/env python3
"""
MLflow experiment for HFT price prediction
This script demonstrates how to use MLflow for tracking HFT machine learning experiments
"""

import mlflow
import mlflow.sklearn
import mlflow.clickhouse
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import clickhouse_connect
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HFTPricePredictor:
    def __init__(self, mlflow_tracking_uri="http://localhost:5000"):
        """
        Initialize HFT Price Predictor with MLflow tracking
        
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
    
    def load_hft_data(self, symbol="BTC-USDT", days_back=7):
        """
        Load HFT data from ClickHouse
        
        Args:
            symbol: Trading symbol
            days_back: Number of days to look back
            
        Returns:
            pandas.DataFrame: HFT data
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
            trade_price,
            trade_size,
            trade_side,
            bid_price,
            ask_price,
            spread
        FROM hft_data.raw_ticks
        WHERE symbol = '{symbol}'
        AND timestamp >= '{start_time}'
        AND timestamp <= '{end_time}'
        AND trade_price > 0
        ORDER BY timestamp
        """
        
        try:
            data = self.client.query_df(query)
            logger.info(f"Loaded {len(data)} records for {symbol}")
            return data
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise
    
    def prepare_features(self, data):
        """
        Prepare features for ML model
        
        Args:
            data: Raw HFT data
            
        Returns:
            tuple: (X, y) features and target
        """
        # Create time-based features
        data['hour'] = pd.to_datetime(data['timestamp']).dt.hour
        data['minute'] = pd.to_datetime(data['timestamp']).dt.minute
        data['second'] = pd.to_datetime(data['timestamp']).dt.second
        
        # Create price-based features
        data['price_change'] = data['trade_price'].pct_change()
        data['volume_weighted_price'] = (data['trade_price'] * data['trade_size']).rolling(window=10).sum() / data['trade_size'].rolling(window=10).sum()
        data['price_volatility'] = data['trade_price'].rolling(window=20).std()
        data['bid_ask_spread'] = data['ask_price'] - data['bid_price']
        
        # Create lag features
        for lag in [1, 2, 3, 5, 10]:
            data[f'price_lag_{lag}'] = data['trade_price'].shift(lag)
            data[f'volume_lag_{lag}'] = data['trade_size'].shift(lag)
        
        # Create rolling features
        for window in [5, 10, 20]:
            data[f'price_ma_{window}'] = data['trade_price'].rolling(window=window).mean()
            data[f'volume_ma_{window}'] = data['trade_size'].rolling(window=window).mean()
            data[f'spread_ma_{window}'] = data['bid_ask_spread'].rolling(window=window).mean()
        
        # Drop rows with NaN values
        data = data.dropna()
        
        # Select features
        feature_columns = [
            'hour', 'minute', 'second',
            'trade_size', 'bid_price', 'ask_price', 'spread',
            'price_change', 'volume_weighted_price', 'price_volatility',
            'price_lag_1', 'price_lag_2', 'price_lag_3', 'price_lag_5', 'price_lag_10',
            'volume_lag_1', 'volume_lag_2', 'volume_lag_3', 'volume_lag_5', 'volume_lag_10',
            'price_ma_5', 'price_ma_10', 'price_ma_20',
            'volume_ma_5', 'volume_ma_10', 'volume_ma_20',
            'spread_ma_5', 'spread_ma_10', 'spread_ma_20'
        ]
        
        # Create target (next price)
        data['next_price'] = data['trade_price'].shift(-1)
        
        # Remove last row (no next price)
        data = data[:-1]
        
        X = data[feature_columns]
        y = data['next_price']
        
        return X, y
    
    def train_model(self, X, y, test_size=0.2, random_state=42):
        """
        Train ML model with MLflow tracking
        
        Args:
            X: Features
            y: Target
            test_size: Test set size
            random_state: Random state
            
        Returns:
            tuple: (model, X_test, y_test)
        """
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, shuffle=False
        )
        
        # Set MLflow tracking URI
        mlflow.set_tracking_uri(self.mlflow_tracking_uri)
        
        # Start MLflow run
        with mlflow.start_run(run_name="HFT_Price_Prediction") as run:
            # Log parameters
            mlflow.log_param("test_size", test_size)
            mlflow.log_param("random_state", random_state)
            mlflow.log_param("n_features", X.shape[1])
            mlflow.log_param("n_samples", len(X))
            
            # Train model
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=random_state,
                n_jobs=-1
            )
            
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Log metrics
            mlflow.log_metric("mse", mse)
            mlflow.log_metric("mae", mae)
            mlflow.log_metric("r2", r2)
            mlflow.log_metric("rmse", np.sqrt(mse))
            
            # Log model
            mlflow.sklearn.log_model(
                model, 
                "model",
                registered_model_name="HFT_Price_Predictor"
            )
            
            # Log feature importance
            feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            mlflow.log_text(
                feature_importance.to_string(),
                "feature_importance.txt"
            )
            
            logger.info(f"Model trained and logged to MLflow. Run ID: {run.info.run_id}")
            logger.info(f"Metrics - MSE: {mse:.4f}, MAE: {mae:.4f}, R2: {r2:.4f}")
            
            return model, X_test, y_test
    
    def run_experiment(self, symbol="BTC-USDT", days_back=7):
        """
        Run complete MLflow experiment
        
        Args:
            symbol: Trading symbol
            days_back: Number of days to look back
        """
        try:
            # Connect to ClickHouse
            self.connect_to_clickhouse()
            
            # Load data
            data = self.load_hft_data(symbol, days_back)
            
            if len(data) < 100:
                logger.warning(f"Not enough data for {symbol}. Found {len(data)} records.")
                return
            
            # Prepare features
            X, y = self.prepare_features(data)
            
            # Train model
            model, X_test, y_test = self.train_model(X, y)
            
            logger.info("Experiment completed successfully!")
            
        except Exception as e:
            logger.error(f"Experiment failed: {e}")
            raise

def main():
    """Main function to run HFT MLflow experiment"""
    predictor = HFTPricePredictor()
    
    # Run experiment for different symbols
    symbols = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
    
    for symbol in symbols:
        logger.info(f"Running experiment for {symbol}")
        try:
            predictor.run_experiment(symbol=symbol, days_back=7)
        except Exception as e:
            logger.error(f"Failed to run experiment for {symbol}: {e}")
            continue

if __name__ == "__main__":
    main()
