from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

import random
import logging
import datetime

from airflow.utils.dates import days_ago


default_args = {
    'owner': 'Daylers',
    'start_date': days_ago(1),
    'retries': 0
}

dag = DAG(
    dag_id='Daylers_Generate_Postgresql_etl_data_flow',
    default_args=default_args,
    schedule_interval='*/10 * * * *', #запуск каждую минуту
    catchup=False,
    tags=['technical', 'etl_data_flow']
)

def _generate_data_etl_data_flow():
    postgres_hook = PostgresHook(postgres_conn_id="khd")
    pkg_sqn = postgres_hook.get_records("SELECT max(pkg_sqn) FROM dev_cbrspb_tmd.etl_pkg WHERE src_layer_id = 129;")

    logging.info(type(pkg_sqn))
    logging.info((pkg_sqn))
    logging.info('-------------ЭТО СООБЩЕНИЕ ОТ LOGGING-------------')

    if pkg_sqn[0][0] is None:
        pkg_sqn = 0
    else:
        pkg_sqn = pkg_sqn[0][0]

    logging.info(type(pkg_sqn))
    logging.info((pkg_sqn))
    logging.info('-------------ЭТО СООБЩЕНИЕ ОТ LOGGING-------------')

    etl_pkgs = []
    for i in range(0, 10):
        pkg_sqn = pkg_sqn + 1
        etl_pkg = {
            'pkg_sqn': pkg_sqn,
            'data_domain_id': 'http://www.it.ru/Schemas/Avior/some_schema' + str(pkg_sqn),
            'pkg_nm': 'pkg_nm' + str(pkg_sqn),
            'tax_cd': 'tax_cd' + str(pkg_sqn),
            'change_dttm': datetime.datetime.now().date(),
            'period_report_sqn': pkg_sqn,
            'src_ready_dttm': datetime.datetime.now().date(),
            'src_layer_id': 129
        }
        etl_pkgs.append(etl_pkg)
        postgres_hook.run(f"""
            INSERT INTO dev_cbrspb_tmd.etl_pkg(pkg_sqn, data_domain_id, pkg_nm, tax_cd, change_dttm, 
                                                period_report_sqn, src_ready_dttm, src_layer_id)
            VALUES ({etl_pkg["pkg_sqn"]}, '{etl_pkg["data_domain_id"]}', '{etl_pkg["pkg_nm"]}', '{etl_pkg["tax_cd"]}', '{etl_pkg["change_dttm"]}', 
                        {etl_pkg["period_report_sqn"]}, '{etl_pkg["src_ready_dttm"]}', {etl_pkg["src_layer_id"]});
        """)

generate_data_etl_data_flow = PythonOperator(
    task_id="generate_data_etl_data_flow",
    python_callable=_generate_data_etl_data_flow,
    dag=dag,
)

generate_data_etl_data_flow

