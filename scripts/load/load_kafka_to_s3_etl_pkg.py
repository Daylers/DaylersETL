import os
from pyspark.sql import SparkSession
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--kafka-topic', required=True)
parser.add_argument('--kafka-bootstrap', required=True)
parser.add_argument('--s3-path', required=True)

args = parser.parse_args()



spark = SparkSession.builder \
    .appName("Load_Kafka_to_S3") \
    .getOrCreate()


from pyspark.sql.types import StructType, StructField, StringType, LongType, IntegerType, DataType
from pyspark.sql.functions import from_json, col
from pyspark.sql.functions import expr
from pyspark.sql import functions as F

kafka_topic = args.kafka_topic
kafka_bootstrap = args.kafka_bootstrap


# Чтение из Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap) \
    .option("subscribe", kafka_topic) \
    .option("startingOffsets", "latest") \
    .load()


# Описание схемы JSON сообщения
schema = StructType([
    StructField("before", StructType([
        StructField("pkg_sqn", IntegerType(), True),
        StructField('data_domain_id', StringType(), True),
        StructField("pkg_nm", StringType(), True),
        StructField("change_dttm", IntegerType(), True)
    ]), True),
    StructField("after", StructType([
        StructField("pkg_sqn", IntegerType(), True),
        StructField('data_domain_id', StringType(), True),
        StructField("pkg_nm", StringType(), True),
        StructField("change_dttm", IntegerType(), True)
    ]), True),
    StructField("source", StructType([]), True),  # если не используешь, можно пустым
    StructField("op", StringType(), True),
    StructField("ts_ms", LongType(), True)
])

# Распарсенные данные
json_df = df.selectExpr("CAST(value AS STRING) as json_str") \
    .select(from_json("json_str", schema).alias("data")) \
    .where("data.after IS NOT NULL") \
    .select("data.after.*") \
    .withColumn('change_dttm2', expr("date_add('1970-01-01', change_dttm)"))

# Запись в S3 с партиционированием
json_df.writeStream \
    .format("parquet") \
    .queryName("etl_pkg") \
    .option("path", args.s3_path) \
    .option("checkpointLocation", args.s3_path + "/_checkpoint/") \
    .partitionBy("change_dttm2") \
    .outputMode("append") \
    .start() \
    .awaitTermination()




