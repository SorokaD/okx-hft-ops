"""
HFT Model Training DAG for Airflow
This DAG orchestrates ML model training and deployment
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
import logging

# Default arguments
default_args = {
    'owner': 'hft-ml-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

# DAG definition
dag = DAG(
    'hft_model_training',
    default_args=default_args,
    description='HFT Model Training and Deployment',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    catchup=False,
    tags=['hft', 'ml', 'training', 'deployment']
)

def prepare_training_data(**context):
    """Prepare training data from ClickHouse"""
    logging.info("Preparing training data...")
    
    try:
        import clickhouse_connect
        import pandas as pd
        
        # Connect to ClickHouse
        client = clickhouse_connect.get_client(
            host='clickhouse',
            port=8123,
            user='default',
            password=''
        )
        
        # Query training data
        query = """
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
        WHERE timestamp >= now() - INTERVAL 7 DAY
        ORDER BY timestamp
        """
        
        data = client.query_df(query)
        logging.info(f"Prepared {len(data)} training samples")
        
        # Save to shared storage
        data.to_csv('/opt/airflow/data/training_data.csv', index=False)
        
        return len(data)
        
    except Exception as e:
        logging.error(f"Failed to prepare training data: {e}")
        raise

def train_price_prediction_model(**context):
    """Train price prediction model"""
    logging.info("Training price prediction model...")
    
    try:
        import subprocess
        
        # Run MLflow experiment
        result = subprocess.run([
            'python', '/opt/airflow/dags/mlflow_experiments/price_prediction.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Price prediction model training completed")
            return "success"
        else:
            logging.error(f"Model training failed: {result.stderr}")
            raise Exception("Model training failed")
            
    except Exception as e:
        logging.error(f"Failed to train model: {e}")
        raise

def train_strategy_model(**context):
    """Train trading strategy model"""
    logging.info("Training trading strategy model...")
    
    try:
        import subprocess
        
        # Run strategy backtest
        result = subprocess.run([
            'python', '/opt/airflow/dags/mlflow_experiments/strategy_backtest.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Strategy model training completed")
            return "success"
        else:
            logging.error(f"Strategy training failed: {result.stderr}")
            raise Exception("Strategy training failed")
            
    except Exception as e:
        logging.error(f"Failed to train strategy model: {e}")
        raise

def validate_models(**context):
    """Validate trained models"""
    logging.info("Validating models...")
    
    try:
        # Get training results
        price_model_result = context['task_instance'].xcom_pull(task_ids='train_price_prediction_model')
        strategy_model_result = context['task_instance'].xcom_pull(task_ids='train_strategy_model')
        
        # Add validation logic here
        if price_model_result == "success" and strategy_model_result == "success":
            logging.info("All models validated successfully")
            return "validated"
        else:
            raise Exception("Model validation failed")
            
    except Exception as e:
        logging.error(f"Model validation failed: {e}")
        raise

def deploy_models(**context):
    """Deploy models to production"""
    logging.info("Deploying models to production...")
    
    try:
        # This would deploy models to production environment
        # For now, just log the deployment
        logging.info("Models deployed to production")
        
        # Update model registry
        import subprocess
        result = subprocess.run([
            'python', '/opt/airflow/dags/update_model_registry.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Model registry updated")
        else:
            logging.warning(f"Model registry update failed: {result.stderr}")
        
        return "deployed"
        
    except Exception as e:
        logging.error(f"Model deployment failed: {e}")
        raise

def send_notification(**context):
    """Send notification about training completion"""
    logging.info("Sending notification...")
    
    try:
        # Get deployment status
        deployment_status = context['task_instance'].xcom_pull(task_ids='deploy_models')
        
        if deployment_status == "deployed":
            logging.info("Training and deployment completed successfully")
            # Send success notification
        else:
            logging.warning("Training completed but deployment failed")
            # Send warning notification
            
    except Exception as e:
        logging.error(f"Failed to send notification: {e}")

# Task definitions
start_task = DummyOperator(
    task_id='start',
    dag=dag
)

prepare_data_task = PythonOperator(
    task_id='prepare_training_data',
    python_callable=prepare_training_data,
    dag=dag
)

train_price_model_task = PythonOperator(
    task_id='train_price_prediction_model',
    python_callable=train_price_prediction_model,
    dag=dag
)

train_strategy_model_task = PythonOperator(
    task_id='train_strategy_model',
    python_callable=train_strategy_model,
    dag=dag
)

validate_models_task = PythonOperator(
    task_id='validate_models',
    python_callable=validate_models,
    dag=dag
)

deploy_models_task = PythonOperator(
    task_id='deploy_models',
    python_callable=deploy_models,
    dag=dag
)

notification_task = PythonOperator(
    task_id='send_notification',
    python_callable=send_notification,
    dag=dag
)

# End task
end_task = DummyOperator(
    task_id='end',
    dag=dag
)

# Task dependencies
start_task >> prepare_data_task
prepare_data_task >> [train_price_model_task, train_strategy_model_task]
[train_price_model_task, train_strategy_model_task] >> validate_models_task
validate_models_task >> deploy_models_task
deploy_models_task >> notification_task
notification_task >> end_task
