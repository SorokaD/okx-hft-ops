"""
HFT Data Pipeline DAG for Airflow
This DAG orchestrates the HFT data processing pipeline
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.sensors.filesystem import FileSensor
from airflow.utils.dates import days_ago
import clickhouse_connect
import pandas as pd
import logging

# Default arguments
default_args = {
    'owner': 'hft-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'hft_data_pipeline',
    default_args=default_args,
    description='HFT Data Processing Pipeline',
    schedule_interval=timedelta(minutes=5),
    catchup=False,
    tags=['hft', 'data', 'pipeline']
)

def extract_raw_data(**context):
    """Extract raw tick data from external source"""
    logging.info("Extracting raw tick data...")
    
    # Simulate data extraction
    # In real scenario, this would connect to OKX API
    import random
    import time
    
    # Simulate API call delay
    time.sleep(2)
    
    # Generate sample data
    data = {
        'timestamp': [datetime.now()],
        'symbol': ['BTC-USDT'],
        'exchange': ['OKX'],
        'trade_price': [50000 + random.uniform(-100, 100)],
        'trade_size': [random.uniform(0.001, 1.0)],
        'trade_side': [random.choice(['buy', 'sell'])],
        'bid_price': [50000 + random.uniform(-50, 0)],
        'ask_price': [50000 + random.uniform(0, 50)],
        'source': ['simulation']
    }
    
    logging.info(f"Extracted {len(data['timestamp'])} records")
    return data

def transform_data(**context):
    """Transform and clean the data"""
    logging.info("Transforming data...")
    
    # Get data from previous task
    data = context['task_instance'].xcom_pull(task_ids='extract_raw_data')
    
    # Add transformation logic here
    df = pd.DataFrame(data)
    df['spread'] = df['ask_price'] - df['bid_price']
    df['mid_price'] = (df['ask_price'] + df['bid_price']) / 2
    
    logging.info(f"Transformed {len(df)} records")
    return df.to_dict('records')

def load_to_clickhouse(**context):
    """Load data into ClickHouse"""
    logging.info("Loading data to ClickHouse...")
    
    try:
        # Connect to ClickHouse
        client = clickhouse_connect.get_client(
            host='clickhouse',
            port=8123,
            user='default',
            password=''
        )
        
        # Get data from previous task
        data = context['task_instance'].xcom_pull(task_ids='transform_data')
        
        if data:
            # Insert data
            client.insert('hft_data.raw_ticks', data)
            logging.info(f"Loaded {len(data)} records to ClickHouse")
        else:
            logging.warning("No data to load")
            
    except Exception as e:
        logging.error(f"Failed to load data to ClickHouse: {e}")
        raise

def run_aggregation(**context):
    """Run data aggregation"""
    logging.info("Running data aggregation...")
    
    try:
        # Connect to ClickHouse
        client = clickhouse_connect.get_client(
            host='clickhouse',
            port=8123,
            user='default',
            password=''
        )
        
        # Run aggregation query
        query = """
        INSERT INTO hft_analytics.agg_1s
        SELECT
            toStartOfSecond(timestamp) as timestamp,
            symbol,
            exchange,
            first_value(trade_price) as open_price,
            max(trade_price) as high_price,
            min(trade_price) as low_price,
            last_value(trade_price) as close_price,
            sum(trade_size) as volume,
            count() as trade_count,
            sumIf(trade_size, trade_side = 'buy') as bid_volume,
            sumIf(trade_size, trade_side = 'sell') as ask_volume,
            avg(ask_price - bid_price) as spread,
            now() as created_at
        FROM hft_data.raw_ticks
        WHERE timestamp >= now() - INTERVAL 1 MINUTE
        GROUP BY symbol, exchange, timestamp
        """
        
        client.command(query)
        logging.info("Aggregation completed")
        
    except Exception as e:
        logging.error(f"Failed to run aggregation: {e}")
        raise

def run_ml_experiment(**context):
    """Run ML experiment"""
    logging.info("Running ML experiment...")
    
    try:
        # This would trigger MLflow experiment
        import subprocess
        result = subprocess.run([
            'python', '/opt/airflow/dags/ml_experiment.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("ML experiment completed successfully")
        else:
            logging.error(f"ML experiment failed: {result.stderr}")
            raise Exception("ML experiment failed")
            
    except Exception as e:
        logging.error(f"Failed to run ML experiment: {e}")
        raise

# Task definitions
start_task = DummyOperator(
    task_id='start',
    dag=dag
)

extract_task = PythonOperator(
    task_id='extract_raw_data',
    python_callable=extract_raw_data,
    dag=dag
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag
)

load_task = PythonOperator(
    task_id='load_to_clickhouse',
    python_callable=load_to_clickhouse,
    dag=dag
)

aggregation_task = PythonOperator(
    task_id='run_aggregation',
    python_callable=run_aggregation,
    dag=dag
)

ml_experiment_task = PythonOperator(
    task_id='run_ml_experiment',
    python_callable=run_ml_experiment,
    dag=dag
)

# Data quality check
data_quality_check = BashOperator(
    task_id='data_quality_check',
    bash_command='''
    echo "Running data quality checks..."
    # Add data quality checks here
    echo "Data quality checks completed"
    ''',
    dag=dag
)

# End task
end_task = DummyOperator(
    task_id='end',
    dag=dag
)

# Task dependencies
start_task >> extract_task >> transform_task >> load_task
load_task >> aggregation_task
load_task >> data_quality_check
aggregation_task >> ml_experiment_task
data_quality_check >> ml_experiment_task
ml_experiment_task >> end_task
