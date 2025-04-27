from pyspark.sql import SparkSession
from pyspark.sql import DataFrame
from contextlib import contextmanager
from pyspark.sql.functions import col, date_trunc, to_date, lit

@contextmanager
def spark_connect(app_name: str = "SparkApp", master :str = None, config: dict = None):
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
            print(f"Spark Application disconected")
            spark.stop()    

config = {
    "spark.jars":
                "/opt/airflow/jars/postgresql-42.7.5.jar,"
                "/opt/airflow/jars/delta-storage-3.1.0.jar,"
                "/opt/airflow/jars/delta-spark_2.12-3.1.0.jar,"
                "/opt/airflow/jars/commons-pool2-2.12.0.jar,",
    "spark.hadoop.fs.defaultFS":"hdfs://namenode:8020",
    "spark.sql.extensions":"io.delta.sql.DeltaSparkSessionExtension",
    "spark.sql.catalog.spark_catalog":"org.apache.spark.sql.delta.catalog.DeltaCatalog",
    "spark.hadoop.dfs.permissions.enabled": "false",
    "spark.hadoop.hadoop.http.staticuser.user": "root",

    # Resource optimizations
    "spark.executor.cores": "2",
    "spark.cores.max": "2",
    "spark.task.cpus": "1",
    "spark.executor.memory": "1G",
    "spark.driver.memory": "1G",
    "spark.scheduler.mode": "FAIR",

    "spark.sql.session.timeZone": "Asia/Ho_Chi_Minh",  # GMT+7
    "spark.executorEnv.TZ": "Asia/Ho_Chi_Minh",

    "spark.sql.execution.arrow.pyspark.enabled": "true",
    "spark.sql.execution.arrow.pyspark.fallback.enabled": "false",
    "spark.sql.adaptive.enabled": "true",
}
def loading_daily_data(**kwargs):
    date_str = kwargs['data_interval_end'].strftime('%Y-%m-%d')
    
    with spark_connect(app_name="Loading Process", master = "spark://spark-master:7077",config = config) as spark:
        try:
            # Debug: Log connection info
            print(f"Loading data for date: {date_str}")
            
            # Read data
            df = spark.read.format("delta").load("hdfs://namenode:8020/ticker_data/gold") \
                            .filter(col("date") == lit(date_str)) 
            df = df.withColumn("date", to_date(col("date"), "yyyy-MM-dd"))
            # Debug: Check data
            print(f"Data count: {df.count()}")
            df.show(5, truncate=False)
                        
            # Write to Postgres
            df.write \
                .format("jdbc") \
                .option("url", "jdbc:postgresql://postgres:5432/ticker") \
                .option("driver", "org.postgresql.Driver") \
                .option("dbtable", "kline_data") \
                .option("user", "ndtienpostgres") \
                .option("password", "ndtienpostgres") \
                .option("batchsize", 10000) \
                .mode("append") \
                .option("truncate", "false") \
                .option("isolationLevel", "READ_COMMITTED") \
                .option("logAbandoned", "true") \
                .option("maxRows", "100000") \
                .save()
                
            print("Successfully loaded data to Postgres")
            
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            raise