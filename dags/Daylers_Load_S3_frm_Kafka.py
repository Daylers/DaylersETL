import os
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.dates import days_ago


default_args = {
    'onwer': 'Daylers',
    'start_date': days_ago(1),
    'retries': 0
}

dag = DAG(
    dag_id='Daylers_Load_S3_frm_Kafka',
    default_args=default_args,
    schedule_interval='@once', #запуск
    catchup=False,
    tags=['technical', 'etl_pkg']
)

stream_kafka_to_s3 = SparkSubmitOperator(
    task_id='spark_stream_kafka_to_s3',
    application='/opt/airflow/scripts/load/load_kafka_to_s3_etl_pkg.py',  # путь до spark-скрипта
    conn_id='spark_default',
    application_args=[
        '--kafka-topic', 'khd.dev_cbrspb_tmd.etl_pkg',
        '--kafka-bootstrap', 'kafka:29093',
        '--s3-path', f's3a://{os.getenv("MINIO_PROD_BUCKET_NAME")}/stream/etl_pkg/'
    ],
    conf={
        "spark.executor.instances": "1",
        "spark.executor.memory": "2g",
        "spark.executor.cores": "1",
        "spark.driver.memory": "1g",
        "spark.hadoop.fs.s3a.endpoint": "http://minio:9000",
        "spark.hadoop.fs.s3a.access.key": os.getenv("MINIO_ROOT_USER"),
        "spark.hadoop.fs.s3a.secret.key": os.getenv("MINIO_ROOT_PASSWORD"),
        "spark.hadoop.fs.s3a.path.style.access": "true",
        "spark.hadoop.fs.s3a.connection.ssl.enabled": "false",

        # Таймауты в миллисекундах (без 's')
        "spark.hadoop.fs.s3a.connection.timeout": "60000",
        "spark.hadoop.fs.s3a.connection.establish.timeout": "5000",
        "spark.hadoop.fs.s3a.connection.ttl": "60000",

        # Дополнительные параметры для стабильности
        "spark.hadoop.fs.s3a.threads.max": "10",
        "spark.hadoop.fs.s3a.multipart.size": "104857600",  # 100MB
        "spark.hadoop.fs.s3a.fast.upload": "true"
    },
    packages=(
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0,"
        "org.apache.hadoop:hadoop-aws:3.3.4,"
        "com.amazonaws:aws-java-sdk-bundle:1.11.1026"
    ),
    dag=dag
)

stream_kafka_to_s3
