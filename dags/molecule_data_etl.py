from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import pandas as pd
import boto3
from rdkit import Chem
from rdkit.Chem import Descriptors

# Default DAG arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Instantiate a DAG
with DAG(
    'molecule_data_etl',
    default_args=default_args,
    description='ETL DAG for molecule data',
    schedule_interval='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False,
) as dag:

    def extract_data(**kwargs):
        # Connect to the database and extract data for the current day
        execution_date = kwargs['execution_date'].strftime('%Y-%m-%d')
        engine = create_engine('postgresql+psycopg2://username:password@localhost/dbname')
        query = f"SELECT identifier, smiles FROM molecules WHERE date = '{execution_date}'"
        df = pd.read_sql(query, engine)
        return df.to_dict(orient='records')

    def transform_data(**kwargs):
        # Fetch extracted data from XCom
        data = kwargs['ti'].xcom_pull(task_ids='extract_data')
        transformed_data = []

        # Calculate molecular properties using RDKit
        for entry in data:
            mol = Chem.MolFromSmiles(entry['smiles'])
            if mol:
                entry.update({
                    'MolecularWeight': Descriptors.MolWt(mol),
                    'LogP': Descriptors.MolLogP(mol),
                    'TPSA': Descriptors.TPSA(mol),
                    'HDonors': Descriptors.NumHDonors(mol),
                    'HAcceptors': Descriptors.NumHAcceptors(mol),
                    'LipinskiPass': Descriptors.MolWt(mol) < 500 and Descriptors.NumHDonors(mol) <= 5 and Descriptors.NumHAcceptors(mol) <= 10
                })
                transformed_data.append(entry)
        return transformed_data

    def load_data(**kwargs):
        # Fetch transformed data from XCom
        data = kwargs['ti'].xcom_pull(task_ids='transform_data')
        df = pd.DataFrame(data)

        # Save the DataFrame to an Excel file
        file_path = '/tmp/molecule_data.xlsx'
        df.to_excel(file_path, index=False)

        # Upload the file to MinIO (or S3)
        s3 = boto3.client(
            's3',
            endpoint_url='http://localhost:9000',  # Replace with your MinIO URL
            aws_access_key_id='minioadmin',
            aws_secret_access_key='minioadmin',
        )
        s3.upload_file(file_path, 'your-bucket-name', 'molecule_data.xlsx')

    # Define tasks
    extract_task = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data,
        provide_context=True,
    )

    transform_task = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data,
        provide_context=True,
    )

    load_task = PythonOperator(
        task_id='load_data',
        python_callable=load_data,
        provide_context=True,
    )

    # Set task dependencies
    extract_task >> transform_task >> load_task

