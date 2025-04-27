from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import expr, when, from_json, col, to_timestamp, date_format
import time
from contextlib import contextmanager

@contextmanager
def spark_connect(app_name: str = "SparkApp", master: str = None, config: dict = None):
    builder = SparkSession.builder.appName(app_name).master(master)
    # Apply all Spark configs
    if config:
        for key, value in config.items():
            builder = builder.config(key, value)
    try:
        spark = builder.getOrCreate()
        print(f"Spark Application {app_name} was created")
        yield spark
    finally:
        if spark:
            print(f"Spark Application disconnected")
            spark.stop()

# Schema 
schema = StructType([
    StructField("symbol", StringType(), True),
    StructField("open_time", LongType(), True),
    StructField("close_time", LongType(), True),
    StructField("interval", StringType(), True),
    StructField("open_price", DoubleType(), True),
    StructField("close_price", DoubleType(), True),
    StructField("high_price", DoubleType(), True),
    StructField("low_price", DoubleType(), True),
    StructField("volume", DoubleType(), True),
    StructField("quote_volume", DoubleType(), True),
    StructField("number_of_trades", IntegerType(), True),
    StructField("is_closed", BooleanType(), True),
])

config = {
    "spark.jars": "/opt/airflow/jars/spark-sql-kafka-0-10_2.12-3.5.0.jar,"
                  "/opt/airflow/jars/kafka-clients-3.5.0.jar,"
                  "/opt/airflow/jars/delta-storage-3.1.0.jar,"
                  "/opt/airflow/jars/delta-spark_2.12-3.1.0.jar,"
                  "/opt/airflow/jars/spark-token-provider-kafka-0-10_2.12-3.5.0.jar,"
                  "/opt/airflow/jars/spark-streaming-kafka-0-10_2.13-3.5.0.jar,"
                  "/opt/airflow/jars/commons-pool2-2.12.0.jar,",
    
    # HDFS and Delta Lake configurations
    "spark.hadoop.fs.defaultFS":"hdfs://namenode:8020",
    "spark.sql.extensions":"io.delta.sql.DeltaSparkSessionExtension",
    "spark.sql.catalog.spark_catalog":"org.apache.spark.sql.delta.catalog.DeltaCatalog",
    "spark.hadoop.dfs.permissions.enabled": "false",
    "spark.hadoop.hadoop.http.staticuser.user": "root",

    
    # Resource optimizations
    "spark.executor.cores": "2",
    "spark.cores.max": "2",
    "spark.task.cpus": "1",
    "spark.executor.memory": "2G",
    "spark.driver.memory": "2G",
    "spark.scheduler.mode": "FAIR",
    
    # Timezone settings
    "spark.sql.session.timeZone": "Asia/Ho_Chi_Minh",
    "spark.executorEnv.TZ": "Asia/Ho_Chi_Minh",

    # Parallelism and performance
    "spark.default.parallelism": "8",
    "spark.sql.shuffle.partitions": "8",
    "spark.streaming.backpressure.enabled": "true",
    "spark.streaming.kafka.maxRatePerPartition": "1000",
}

with spark_connect(app_name="Crypto Trades Processor", 
                  master="spark://spark-master:7077",
                  config=config) as spark:
    
    # Read from Kafka topic with optimized settings
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "crypto-trades") \
        .option("startingOffsets", "latest") \
        .option("maxOffsetsPerTrigger", "5000") \
        .option("failOnDataLoss", "false") \
        .load()

    # Parse JSON → Bronze Layer (Raw) with timestamp conversion
    bronze = df.select(
            from_json(col("value").cast("string"), schema).alias("data"),
            col("timestamp").alias("processing_time")
        ).select(
                "data.*",
                "processing_time",
                expr("CAST(open_time/1000 AS TIMESTAMP)").alias("open_timestamp"),
                expr("CAST(close_time/1000 AS TIMESTAMP)").alias("close_timestamp")
            )

    # Silver Layer - Data cleaning and deduplication
    silver = bronze.fillna({
        "symbol": "UNKNOWN",
        "interval": "1m",
        "open_price": 0.0,
        "close_price": 0.0,
        "is_closed": False,
        "high_price": 0.0,
        "low_price": 0.0,
        "quote_volume": 0.0,
        "number_of_trades": 0
    }).filter("volume > 0") \
      .dropDuplicates(["symbol", "open_time", "close_time"]) \
      .withColumn("date", date_format(col("open_timestamp"), "yyyy-MM-dd"))

    # Gold Layer - Aggregations and business metrics
    gold = silver.withColumn("volatility", col("high_price") - col("low_price")) \
        .withColumn("price_change_pct", expr("((close_price - open_price)/open_price)*100")) \
        .withColumn("trend", when(col("close_price") > col("open_price"), "up")
                          .when(col("close_price") < col("open_price"), "down")
                          .otherwise("neutral")) \

    # Optimized write to HDFS with partitioning and compaction
    bronze_query = bronze.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("path", "hdfs://namenode:8020/ticker_data/bronze") \
        .option("checkpointLocation", "hdfs://namenode:8020/checkpoints/bronze") \
        .option("mergeSchema", "true") \
        .trigger(processingTime="60 seconds") \
        .start()

    silver_query = silver.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("path", "hdfs://namenode:8020/ticker_data/silver") \
        .option("checkpointLocation", "hdfs://namenode:8020/checkpoints/silver") \
        .option("mergeSchema", "true") \
        .trigger(processingTime="60 seconds") \
        .partitionBy("symbol") \
        .start()

    gold_query = gold.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("path", "hdfs://namenode:8020/ticker_data/gold") \
        .option("checkpointLocation", "hdfs://namenode:8020/checkpoints/gold") \
        .option("mergeSchema", "true") \
        .trigger(processingTime="60 seconds") \
        .partitionBy("symbol", "date") \
        .start()
    
    # Improved stream management
    queries = [bronze_query, silver_query, gold_query]
    
    # Wait for all streams to be active
    for query in queries:
        while query.status['message'] != 'Streaming query has started':
            time.sleep(1)
    print("All streaming queries are active")
    

    spark.streams.awaitAnyTermination()
    # Monitor streams with better error handling
    while True:
        for query in queries:
            status = query.status
            if status['isTriggerActive'] == False or status['isDataAvailable'] == False:
                print(f"Query {query.id} has issues: {status}")
                # Handle errors or restart if needed
        
        time.sleep(10)  # Check status every 10 seconds
    