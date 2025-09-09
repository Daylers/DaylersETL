import json
import requests
from datetime import datetime, timedelta
import pandas as pd
import os
import logging
import numpy as np
import io

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.models import Variable
from airflow.utils.db import create_session
from airflow.models import TaskInstance

logger = logging.getLogger("task_logger") 
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


default_args = {
    'owner': 'Nikitin',
    'start_date': days_ago(1),
    'retries': 2
}

dag = DAG(
    dag_id = 'Daylers_Nikitin_API_Predict_Weather_to_S3',
    default_args = default_args,
    schedule_interval = '0 4 * * mon,tue,wed,thu,fri', #At 04:00 utc airflow/7:00 moscow on Monday, Thursday, Wednesday, Thursday, and Friday.
    catchup = False,
    description="Выгрузка в будние дни в 7 утра данных о предсказании погоды на день запуска дага в Строгнино, Багратионовская. Отправка сообщений в тг для отслеживания погоды",
    tags = ['api', 'weather', 'predict', 's3']
)

def fetch_weather_and_upload_s3hook(**context):
    date_yest = context["ds"]
    execution_date = context["execution_date"] #2025-07-27 17:17:54.879662+00:00
    execution_date = execution_date.strftime('%Y-%m-%d')
    ti = context["ti"]

    api = 'https://api.open-meteo.com/v1/forecast'
    params = {
        "latitude": [55.80276, 55.74371],
        "longitude": [37.40557, 37.49809],
        "location_id": [1, 2],
        "hourly": ["temperature_2m", "rain", "wind_speed_10m"],
        "timezone": "Europe/Moscow",
        "forecast_days": 1
    }

    logger.info(f"Вчерашняя дата: {date_yest}")
    logger.info(f"Дата запуска дага: {execution_date}")
    logger.info(f"API_URL = {api}")
    logger.info(f"API_params= {params}")

    response = requests.get(api, params=params)
    rows = response.text
    json_data = json.loads(rows)
    df = pd.json_normalize(json_data)

    logger.info(f"Количество строк в выгружено из api: {len(df)}")

    df['location_name'] = ['Строгино', 'Багратионовская']

    # Колонки со списками
    list_cols = ['hourly.time', 'hourly.temperature_2m', 'hourly.rain', 'hourly.wind_speed_10m']

    # Колонки, которые нужно повторить
    repeat_cols = [col for col in df.columns if col not in list_cols]

    # Количество повторений — длина списков
    repeats = df[list_cols[0]].str.len()

    # Разворачиваем колонки со списками
    exploded_part = pd.DataFrame({col: df[col].explode().values for col in list_cols})

    # Повторяем остальные колонки (id, name и т.п.)
    repeated_part = pd.DataFrame({
        col: df[col].repeat(repeats).values for col in repeat_cols
    })

    # Объединяем
    df_expanded = pd.concat([repeated_part.reset_index(drop=True),
                            exploded_part.reset_index(drop=True)], axis=1)

    df_expanded['hourly.time'] = pd.to_datetime(df_expanded['hourly.time'])

    date = datetime.utcnow() + timedelta(hours=3)
    df_expanded['s3_load_dt'] = date.strftime('%Y-%m-%d %H:%M:%S')


    filename = f"api/nikitin/weather/predict/strg_bgrt_{execution_date}.parquet"
    # Сохранить в Parquet
    if len(df_expanded) > 0:
        buffer = io.BytesIO()
        df_expanded.to_parquet(buffer, index=False)
        buffer.seek(0)  # возвращаемся в начало буфера

        hook = S3Hook(aws_conn_id='minios3_conn')
        hook.load_bytes(
            bytes_data=buffer.read(),
            key=filename,
            bucket_name='dev',
            replace=True
        )

    total_rows = len(df_expanded)
    print(f"==== Данные по погоде загружены за {execution_date}")
    print(f"==== Кол-во строк {total_rows}")


    ti.xcom_push(key="load_date", value=execution_date)
    ti.xcom_push(key="total_rows", value=total_rows)

def telegram_message(**context):
    token = str(Variable.get("DAYLERS_AIRFLOW_BOT_KEY"))
    chat_id = str(Variable.get("DAYLERS_CHAT_ID"))
    # chat_id = '1249432887'
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    dag_run = context["dag_run"]
    # session = context["session"]

    # ti_load_to_s3 = dag_run.get_task_instance('load_to_s3', session=session)


    # logger.info(f"Статус задачи по загрузке в S3: {ti_load_to_s3.status}")

    # if ti_load_to_s3.status == 'Failed':
    #     raise Status_looad_to_s3('Ошибка загрузки в s3')

    #создание session для запроса в БД airflow, чтобы получить statе таски load_to_s3 в этом запуске
    with create_session() as session:
        ti_load_to_s3 = session.query(TaskInstance).filter(
            TaskInstance.dag_id == dag_run.dag_id,
            TaskInstance.task_id == 'load_to_s3',
            TaskInstance.run_id == dag_run.run_id
        ).first()

        if ti_load_to_s3:
            state = ti_load_to_s3.state
            print(f"Статус задачи 'load_to_s3': {state}")
        
            if state == 'failed':
                raise Exception('Ошибка загрузки в S3')
        else:
            raise Exception('TaskInstance load_to_s3 не найден')

    ti = context['ti']
    execution_date = ti.xcom_pull(task_ids='load_to_s3', key='load_date')
    total_rows = ti.xcom_pull(task_ids='load_to_s3', key='total_rows')

    filename = f"api/nikitin/weather/predict/strg_bgrt_{execution_date}.parquet"
    hook = S3Hook(aws_conn_id='minios3_conn')
    # Получаем объект из S3
    s3_obj = hook.get_key(key=filename, bucket_name='dev')
    # Читаем байты (аналогично buffer.read())
    file_bytes = s3_obj.get()['Body'].read()
    # Преобразуем в DataFrame
    df = pd.read_parquet(io.BytesIO(file_bytes))

    execution_date_8 = pd.to_datetime(execution_date + ' 08:00:00')

    temperature_strg = df[(df['location_name'] == 'Строгино') & (df['hourly.time'] == execution_date_8)]['hourly.temperature_2m'].iloc[0]
    rain_strg = df[(df['location_name'] == 'Строгино') & (df['hourly.time'] == execution_date_8)]['hourly.rain'].iloc[0]
    wind_speed_strg = df[(df['location_name'] == 'Строгино') & (df['hourly.time'] == execution_date_8)]['hourly.wind_speed_10m'].iloc[0]


    message = (
        f"*Airflow уведомление*\n"
        f"DAG: `Daylers_Nikitin_API_Predict_Weather_to_S3`\n"
        f"Статус задачи: `{ti_load_to_s3.state}`\n"
        f"Дата выполнения: `{execution_date}`\n"
        f"Загружено строк: `{total_rows}`\n"
        f"-----------------------------------------------\n"
        f"Погода в Строгино в `{execution_date_8}`\n:"
        f"температура: {temperature_strg}, осадки: {rain_strg}, ветер: {wind_speed_strg}"
    )

    payload = {
            "chat_id": chat_id,
            "text": message,
            # "parse_mode": "Markdown"
        }
    response = requests.post(url, json=payload)
    print(f"Response text: {response.text}")
    response.raise_for_status()

load_to_s3 = PythonOperator(
    task_id = 'load_to_s3',
    python_callable = fetch_weather_and_upload_s3hook,
    dag = dag 
)

telegram_message = PythonOperator(
    task_id = 'telegram_message',
    python_callable = telegram_message,
    dag = dag 
)

load_to_s3 >> telegram_message