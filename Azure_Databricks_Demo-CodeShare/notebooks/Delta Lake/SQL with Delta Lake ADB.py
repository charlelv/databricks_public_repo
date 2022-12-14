# Databricks notebook source
# MAGIC %md <a href='$../Azure Integrations Start Here'>Home</a>

# COMMAND ----------

# MAGIC %md 
# MAGIC ## ![Delta Lake Tiny Logo](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Building a Reliable and Performant Data lake with Delta

# COMMAND ----------

# MAGIC %md
# MAGIC ### Delta Lake is an open-source storage layer that brings ACID transactions to Apache Spark™ and big data workloads.
# MAGIC <img src="https://databricks.com/wp-content/uploads/2019/08/Delta-Lake-Multi-Hop-Architecture-Overview.png"/>

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC # Ensuring Consistency with ACID Transactions with Delta Lake (Loan Risk Data)
# MAGIC 
# MAGIC <img src="https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-logo-whitebackground.png" width=200/>
# MAGIC 
# MAGIC This is a companion notebook to provide a Delta Lake example against the Lending Club data.
# MAGIC * This notebook has been tested with *DBR 5.4 ML Beta, Python 3*

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## The Data
# MAGIC 
# MAGIC The data used is public data from Lending Club. It includes all funded loans from 2012 to 2017. Each loan includes applicant information provided by the applicant as well as the current loan status (Current, Late, Fully Paid, etc.) and latest payment information. For a full view of the data please view the data dictionary available [here](https://resources.lendingclub.com/LCDataDictionary.xlsx).
# MAGIC 
# MAGIC 
# MAGIC ![Loan_Data](https://preview.ibb.co/d3tQ4R/Screen_Shot_2018_02_02_at_11_21_51_PM.png)
# MAGIC 
# MAGIC https://www.kaggle.com/wendykan/lending-club-loan-data

# COMMAND ----------

# MAGIC %md
# MAGIC ## ![Delta Lake Tiny Logo](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Delta Lake
# MAGIC 
# MAGIC Optimization Layer a top blob storage for Reliability (i.e. ACID compliance) and Low Latency of Streaming + Batch data pipelines.

# COMMAND ----------

# MAGIC %md ## Import Data and create pre-Delta Lake Table
# MAGIC * This will create a lot of small Parquet files emulating the typical small file problem that occurs with streaming or highly transactional data

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ### Mounting an Azure Blob storage container to DBFS
# MAGIC <pre>
# MAGIC dbutils.fs.mount(
# MAGIC   source = "wasbs://datasets@gsethistorageaccount.blob.core.windows.net/",
# MAGIC   mount_point = "/mnt/datasets",
# MAGIC   extra_configs = {"fs.azure.account.key.gsethistorageaccount.blob.core.windows.net": dbutils.secrets.get("gsethi-kv-scope","gsethi-storage-secret")})
# MAGIC </pre>

# COMMAND ----------

dbutils.fs.mount(
  source = "wasbs://datasets@gsethistorageaccount.blob.core.windows.net/",
  mount_point = "/mnt/datasets",
  extra_configs = {"fs.azure.account.key.gsethistorageaccount.blob.core.windows.net": dbutils.secrets.get("gsethi-kv-scope","gsethi-storage-secret")})

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ### Mounting an ADLSg2 storage container to DBFS
# MAGIC 
# MAGIC <pre>
# MAGIC configs = {
# MAGIC   "fs.azure.account.auth.type": "CustomAccessToken",
# MAGIC   "fs.azure.account.custom.token.provider.class":   spark.conf.get("spark.databricks.passthrough.adls.gen2.tokenProviderClassName")
# MAGIC }
# MAGIC dbutils.fs.mount(
# MAGIC   source = "abfss://deltalake@gsethistorageaccount.dfs.core.windows.net/",
# MAGIC   mount_point = "/mnt/deltalake",
# MAGIC   extra_configs = configs)
# MAGIC </pre>

# COMMAND ----------

configs = {
  "fs.azure.account.auth.type": "CustomAccessToken",
  "fs.azure.account.custom.token.provider.class":   spark.conf.get("spark.databricks.passthrough.adls.gen2.tokenProviderClassName")
}
dbutils.fs.mount(
  source = "abfss://deltalake@gsethistorageaccount.dfs.core.windows.net/",
  mount_point = "/mnt/deltalake",
  extra_configs = configs)

# COMMAND ----------

# DBTITLE 0,Import Data and create pre-Databricks Delta Table
# -----------------------------------------------
# Uncomment and run if this folder does not exist
# -----------------------------------------------
# Configure location of loanstats_2012_2017.parquet
lspq_path = "/mnt/datasets/lending_club/parquet/"
# Read loanstats_2012_2017.parquet
data = spark.read.parquet(lspq_path)

# Reduce the amount of data (to run on DBCE)
(loan_stats, loan_stats_rest) = data.randomSplit([0.01, 0.99], seed=123)

# Select only the columns needed
loan_stats = loan_stats.select("addr_state", "loan_status")

# Create loan by state
loan_by_state = loan_stats.groupBy("addr_state").count()

# Create table
loan_by_state.createOrReplaceTempView("loan_by_state")

# Display loans by state
display(loan_by_state)

# COMMAND ----------

# MAGIC %md ## ![Delta Lake Tiny Logo](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Easily Convert Parquet to Delta Lake format
# MAGIC With Delta Lake, you can easily transform your Parquet data into Delta Lake format. 

# COMMAND ----------

# Configure Delta Lake Silver & Gold Paths
DELTALAKE_SILVER_PATH = "/ml/loan_by_state_delta"
DELTALAKE_GOLD_PATH = "/ml/loan_by_state_gold"
# Remove folders if they exists
dbutils.fs.rm(DELTALAKE_SILVER_PATH, recurse=True)
dbutils.fs.rm(DELTALAKE_GOLD_PATH, recurse=True)

# COMMAND ----------

# MAGIC %sql 
# MAGIC -- Current example is creating a new table instead of in-place import so will need to change this code
# MAGIC DROP TABLE IF EXISTS loan_by_state_delta;
# MAGIC 
# MAGIC CREATE TABLE loan_by_state_delta
# MAGIC USING delta
# MAGIC LOCATION '/ml/loan_by_state_delta'
# MAGIC AS SELECT * FROM loan_by_state;
# MAGIC 
# MAGIC -- View Delta Lake table
# MAGIC SELECT * FROM loan_by_state_delta

# COMMAND ----------

# MAGIC %sql 
# MAGIC DESCRIBE DETAIL loan_by_state_delta

# COMMAND ----------

display(dbutils.fs.ls(DELTALAKE_SILVER_PATH + "/_delta_log/"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stop the notebook before the streaming cell, in case of a "run all" 

# COMMAND ----------

dbutils.notebook.exit("stop") 

# COMMAND ----------

# MAGIC %md ## ![Delta Lake Tiny Logo](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Unified Batch and Streaming Source and Sink
# MAGIC 
# MAGIC These cells showcase streaming and batch concurrent queries (inserts and reads)
# MAGIC * This notebook will run an `INSERT` every 10s against our `loan_stats_delta` table
# MAGIC * We will run two streaming queries concurrently against this data
# MAGIC * Note, you can also use `writeStream` but this version is easier to run in DBCE

# COMMAND ----------

# Read the insertion of data
loan_by_state_readStream = spark.readStream.format("delta").load(DELTALAKE_SILVER_PATH)
loan_by_state_readStream.createOrReplaceTempView("loan_by_state_readStream")

# COMMAND ----------

# MAGIC %sql
# MAGIC select addr_state, sum(`count`) as loans from loan_by_state_readStream group by addr_state

# COMMAND ----------

dbutils.notebook.exit("stop") 

# COMMAND ----------

# MAGIC %md **Wait** until the stream is up and running before executing the code below

# COMMAND ----------

import time
i = 1
while i <= 6:
  # Execute Insert statement
  insert_sql = "INSERT INTO loan_by_state_delta VALUES ('IA', 450)"
  spark.sql(insert_sql)
  print('loan_by_state_delta: inserted new row of data, loop: [%s]' % i)
    
  # Loop through
  i = i + 1
  time.sleep(5)

# COMMAND ----------

display(dbutils.fs.ls(DELTALAKE_SILVER_PATH + "/_delta_log/"))

# COMMAND ----------

display(spark.sql(f"DESCRIBE history delta.`{DELTALAKE_SILVER_PATH}`"))

# COMMAND ----------

# MAGIC %sql DESCRIBE HISTORY loan_by_state_delta

# COMMAND ----------

# MAGIC %md 
# MAGIC **Note**: Once the previous cell is finished and the state of Iowa is fully populated in the map (in cell 14), click *Cancel* in Cell 14 to stop the `readStream`.

# COMMAND ----------

# MAGIC %md
# MAGIC Let's review our current set of loans using our map visualization.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Review current loans within the `loan_by_state_delta` Delta Lake table
# MAGIC select addr_state, sum(`count`) as loans from loan_by_state_delta group by addr_state

# COMMAND ----------

# MAGIC %md Observe that the Iowa (middle state) has the largest number of loans due to the recent stream of data.  Note that the original `loan_by_state_delta` table is updated as we're reading `loan_by_state_readStream`.

# COMMAND ----------

# MAGIC %md
# MAGIC ##![Delta Lake Logo Tiny](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Full DML Support
# MAGIC 
# MAGIC **Note**: Full DML Support is a feature that will be coming soon to Delta Lake; the preview is currently available in Databricks.
# MAGIC 
# MAGIC Delta Lake supports standard DML including UPDATE, DELETE and MERGE INTO providing developers more controls to manage their big datasets.

# COMMAND ----------

# MAGIC %md Let's start by creating a traditional Parquet table

# COMMAND ----------

# Load new DataFrame based on current Delta table
lbs_df = sql("select * from loan_by_state_delta")

# Save DataFrame to Parquet
lbs_df.write.mode("overwrite").parquet("/ml/loan_by_state.parquet")

# Reload Parquet Data
lbs_pq = spark.read.parquet("/ml/loan_by_state.parquet")

# Create new table on this parquet data
#lbs_pq.createOrReplaceTempView("loan_by_state_pq")

# Review data
#display(sql("select * from loan_by_state_pq"))

# COMMAND ----------

# MAGIC %sql 
# MAGIC -- Current example is creating a new table instead of in-place import so will need to change this code
# MAGIC DROP TABLE IF EXISTS loan_by_state_pq;
# MAGIC 
# MAGIC CREATE TABLE loan_by_state_pq
# MAGIC USING parquet
# MAGIC LOCATION '/ml/loan_by_state.parquet';
# MAGIC 
# MAGIC SELECT * FROM loan_by_state_pq

# COMMAND ----------

# MAGIC %md ###![Delta Lake Logo Tiny](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) DELETE Support
# MAGIC 
# MAGIC The data was originally supposed to be assigned to `WA` state, so let's `DELETE` those values assigned to `IA`

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Attempting to run `DELETE` on the Parquet table
# MAGIC DELETE FROM loan_by_state_pq WHERE addr_state = 'IA'

# COMMAND ----------

# MAGIC %md **Note**: This command fails because the `DELETE` statements are not supported in Parquet, but are supported in Delta Lake.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Running `DELETE` on the Delta Lake table
# MAGIC DELETE FROM loan_by_state_delta WHERE addr_state = 'IA'

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Review current loans within the `loan_by_state_delta` Delta Lake table
# MAGIC select addr_state, sum(`count`) as loans from loan_by_state_delta group by addr_state

# COMMAND ----------

# MAGIC %md ###![Delta Lake Logo Tiny](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) UPDATE Support
# MAGIC The data was originally supposed to be assigned to `WA` state, so let's `UPDATE` those values

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Attempting to run `UPDATE` on the Parquet table
# MAGIC UPDATE loan_by_state_pq SET `count` = 2700 WHERE addr_state = 'WA'

# COMMAND ----------

# MAGIC %md **Note**: This command fails because the `UPDATE` statements are not supported in Parquet, but are supported in Delta Lake.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Running `UPDATE` on the Delta Lake table
# MAGIC UPDATE loan_by_state_delta SET `count` = 2700 WHERE addr_state = 'WA'

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Review current loans within the `loan_by_state_delta` Delta Lake table
# MAGIC select addr_state, sum(`count`) as loans from loan_by_state_delta group by addr_state

# COMMAND ----------

# MAGIC %md ###![Delta Lake Logo Tiny](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) MERGE INTO Support
# MAGIC 
# MAGIC #### INSERT or UPDATE parquet: 7-step process
# MAGIC 
# MAGIC With a legacy data pipeline, to insert or update a table, you must:
# MAGIC 1. Identify the new rows to be inserted
# MAGIC 2. Identify the rows that will be replaced (i.e. updated)
# MAGIC 3. Identify all of the rows that are not impacted by the insert or update
# MAGIC 4. Create a new temp based on all three insert statements
# MAGIC 5. Delete the original table (and all of those associated files)
# MAGIC 6. "Rename" the temp table back to the original table name
# MAGIC 7. Drop the temp table
# MAGIC 
# MAGIC ![](https://pages.databricks.com/rs/094-YMS-629/images/merge-into-legacy.gif)
# MAGIC 
# MAGIC 
# MAGIC #### INSERT or UPDATE with Delta Lake
# MAGIC 
# MAGIC 2-step process: 
# MAGIC 1. Identify rows to insert or update
# MAGIC 2. Use `MERGE`

# COMMAND ----------

# Let's create a simple table to merge
items = [('IA', 0), ('CA', 2500), ('OR', 0)]
cols = ['addr_state', 'count']
merge_table = spark.createDataFrame(items, cols)
merge_table.createOrReplaceTempView("merge_table")
display(merge_table)

# COMMAND ----------

# MAGIC %md Instead of writing separate `INSERT` and `UPDATE` statements, we can use a `MERGE` statement. 

# COMMAND ----------

# MAGIC %sql
# MAGIC MERGE INTO loan_by_state_delta as d
# MAGIC USING merge_table as m
# MAGIC on d.addr_state = m.addr_state
# MAGIC WHEN MATCHED THEN 
# MAGIC   UPDATE SET *
# MAGIC WHEN NOT MATCHED 
# MAGIC   THEN INSERT *

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Review current loans within the `loan_by_state_delta` Delta Lake table
# MAGIC select addr_state, sum(`count`) as loans from loan_by_state_delta group by addr_state

# COMMAND ----------

# MAGIC %md
# MAGIC ##![Delta Lake Logo Tiny](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Schema Evolution
# MAGIC With the `mergeSchema` option, you can evolve your Delta Lake table schema

# COMMAND ----------

# Generate new loans with dollar amounts 
loans = sql("select addr_state, cast(rand(10)*count as bigint) as count, cast(rand(10) * 10000 * count as double) as amount from loan_by_state_delta")
display(loans)

# COMMAND ----------

# Let's write this data out to our Delta table
loans.write.format("delta").mode("append").save(DELTALAKE_SILVER_PATH)

# COMMAND ----------

# MAGIC %md **Note**: This command fails because the schema of our new data does not match the schema of our original data

# COMMAND ----------

# Add the mergeSchema option
loans.write.option("mergeSchema","true").format("delta").mode("append").save(DELTALAKE_SILVER_PATH)

# COMMAND ----------

# MAGIC %md **Note**: With the `mergeSchema` option, we can merge these different schemas together.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Review current loans within the `loan_by_state_delta` Delta Lake table
# MAGIC select addr_state, sum(`amount`) as amount from loan_by_state_delta group by addr_state order by sum(`amount`) desc limit 10

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE IF EXISTS loans_gold;
# MAGIC 
# MAGIC CREATE TABLE loans_gold
# MAGIC USING delta
# MAGIC LOCATION '/ml/loan_by_state_gold'
# MAGIC AS
# MAGIC   SELECT addr_state, sum(`amount`) AS amount FROM loan_by_state_delta GROUP BY addr_state

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Review current loans within the loans_gold Delta Lake table
# MAGIC select * from loans_gold order by amount desc limit 10

# COMMAND ----------

# MAGIC %md ## ![Delta Lake Tiny Logo](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Let's Travel back in Time!
# MAGIC Databricks Delta’s time travel capabilities simplify building data pipelines for the following use cases. 
# MAGIC 
# MAGIC * Audit Data Changes
# MAGIC * Reproduce experiments & reports
# MAGIC * Rollbacks
# MAGIC 
# MAGIC As you write into a Delta table or directory, every operation is automatically versioned.
# MAGIC 
# MAGIC You can query by:
# MAGIC 1. Using a timestamp
# MAGIC 1. Using a version number
# MAGIC 
# MAGIC using Python, Scala, and/or Scala syntax; for these examples we will use the SQL syntax.  
# MAGIC 
# MAGIC For more information, refer to [Introducing Delta Time Travel for Large Scale Data Lakes](https://databricks.com/blog/2019/02/04/introducing-delta-time-travel-for-large-scale-data-lakes.html)

# COMMAND ----------

# MAGIC %md ### ![Delta Lake Tiny Logo](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Review Delta Lake Table History
# MAGIC All the transactions for this table are stored within this table including the initial set of insertions, update, delete, merge, and inserts with schema modification

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE HISTORY loan_by_state_delta

# COMMAND ----------

# MAGIC %md ### ![Delta Lake Tiny Logo](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Time Travel via Version Number
# MAGIC Below are SQL syntax examples of Delta Time Travel by using a Version Number

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM loan_by_state_delta VERSION AS OF 6

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM loan_by_state_delta timestamp AS OF '2022-09-05 01:28:55.0'

# COMMAND ----------

# MAGIC %fs
# MAGIC ls /ml/loan_by_state_delta/_delta_log

# COMMAND ----------

# MAGIC %sh
# MAGIC cat /dbfs/ml/loan_by_state_delta/_delta_log/00000000000000000000.json

# COMMAND ----------

# MAGIC %md ### ![Delta Lake Tiny Logo](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Delta Optimizations
# MAGIC How Databricks Delta optimizes for Performance

# COMMAND ----------

# MAGIC %md
# MAGIC ## VACUUM
# MAGIC 
# MAGIC To save on storage costs you should occasionally clean up invalid files using the `VACUUM` command. 
# MAGIC 
# MAGIC Invalid files are small files compacted into a larger file with the `OPTIMIZE` command.
# MAGIC 
# MAGIC The  syntax of the `VACUUM` command is 
# MAGIC >`VACUUM name-of-table RETAIN number-of HOURS;`
# MAGIC 
# MAGIC The `number-of` parameter is the <b>retention interval</b>, specified in hours.
# MAGIC 
# MAGIC <img alt="Caution" title="Caution" style="vertical-align: text-bottom; position: relative; height:1.3em; top:0.0em" src="https://files.training.databricks.com/static/images/icon-warning.svg"/> Databricks does not recommend you set a retention interval shorter than seven days because old snapshots and uncommitted files can still be in use by concurrent readers or writers to the table.
# MAGIC 
# MAGIC The scenario here is:
# MAGIC 0. User A starts a query off uncompacted files, then
# MAGIC 0. User B invokes a `VACUUM` command, which deletes the uncompacted files
# MAGIC 0. User A's query fails because the underlying files have disappeared
# MAGIC 
# MAGIC Invalid files can also result from updates/upserts/deletions.
# MAGIC 
# MAGIC More details are provided here: <a href="https://docs.databricks.com/delta/optimizations.html#garbage-collection" target="_blank"> Garbage Collection</a>.
# MAGIC 
# MAGIC Check the number of files before we vacuum.

# COMMAND ----------

display(dbutils.fs.ls(DELTALAKE_SILVER_PATH ))

# COMMAND ----------

spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", False)

# COMMAND ----------

display(spark.sql(f"VACUUM delta.`{DELTALAKE_SILVER_PATH}` RETAIN 0 HOURS"))

# COMMAND ----------

display(dbutils.fs.ls(DELTALAKE_SILVER_PATH ))

# COMMAND ----------

display(spark.sql(f"OPTIMIZE delta.`{DELTALAKE_SILVER_PATH}`"))

# COMMAND ----------

spark.sql(f"VACUUM delta.`{DELTALAKE_SILVER_PATH}` RETAIN 0 HOURS")

# COMMAND ----------

display(dbutils.fs.ls(DELTALAKE_SILVER_PATH ))

# COMMAND ----------

dbutils.notebook.exit("stop")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Other Optimizations 
# MAGIC ### Let's See How Databricks Delta Makes Spark Queries Faster!
# MAGIC 
# MAGIC In this example, we will see how Databricks Delta can optimize query performance. We create a standard table using Parquet format and run a quick query to observe its latency. We then run a second query over the Databricks Delta version of the same table to see the performance difference between standard tables versus Databricks Delta tables. 
# MAGIC 
# MAGIC Simply follow these 4 steps below:
# MAGIC * __Step 1__ : Create a standard Parquet based table using data from US based flights schedule data
# MAGIC * __Step 2__ : Run a query to to calculate number of flights per month, per originating airport over a year
# MAGIC * __Step 3__ : Create the flights table using Databricks Delta and optimize the table.
# MAGIC * __Step 4__ : Rerun the query in Step 2 and observe the latency. 
# MAGIC 
# MAGIC __Note:__ _Throughout the example we will be building few tables with a 10s of million rows. Some of the operations may take a few minutes depending on your cluster configuration._

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE IF EXISTS flights;
# MAGIC 
# MAGIC -- Create a standard table and import US based flights for year 2008
# MAGIC -- USING Clause: Specify parquet format for a standard table
# MAGIC -- PARTITIONED BY clause: Orginize data based on "Origin" column (Originating Airport code).
# MAGIC -- FROM Clause: Import data from a csv file. 
# MAGIC CREATE TABLE flights
# MAGIC USING parquet
# MAGIC PARTITIONED BY (Origin)
# MAGIC SELECT _c0 as Year, _c1 as Month, _c2 as DayofMonth, _c3 as DayOfWeek, _c4 as DepartureTime, _c5 as CRSDepartureTime, _c6 as ArrivalTime, 
# MAGIC   _c7 as CRSArrivalTime, _c8 as UniqueCarrier, _c9 as FlightNumber, _c10 as TailNumber, _c11 as ActualElapsedTime, _c12 as CRSElapsedTime, 
# MAGIC     _c13 as AirTime, _c14 as ArrivalDelay, _c15 as DepartureDelay, _c16 as Origin, _c17 as Destination, _c18 as Distance, 
# MAGIC     _c19 as TaxiIn, _c20 as TaxiOut, _c21 as Cancelled, _c22 as CancellationCode, _c23 as Diverted, _c24 as CarrierDelay, 
# MAGIC     _c25 as WeatherDelay, _c26 as NASDelay, _c27 as SecurityDelay, _c28 as LateAircraftDelay 
# MAGIC FROM csv.`dbfs:/databricks-datasets/asa/airlines/2008.csv`

# COMMAND ----------

# MAGIC %md
# MAGIC Once step 1 completes, the standard "flights" table contains details of US flights for a year. 
# MAGIC 
# MAGIC Next in Step 2, we run a query that get top 20 cities with highest monthly total flights on first day of week.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Get top 20 cities with highest monthly total flights on first day of week. & observe the latency! 
# MAGIC -- This query may take over a minute in certain cluster configurations. 
# MAGIC SELECT Month, Origin, count(*) as TotalFlights 
# MAGIC FROM flights
# MAGIC WHERE DayOfWeek = 1 
# MAGIC GROUP BY Month, Origin 
# MAGIC ORDER BY TotalFlights DESC
# MAGIC LIMIT 20;

# COMMAND ----------

# MAGIC %md
# MAGIC Once step 2 completes, you can observe the latency with the standard "flights" table. 
# MAGIC 
# MAGIC In step 3 and step 4, we do the same with a Databricks Delta table. This time, before running the query, we run the `OPTIMIZE` command with `ZORDER` to ensure data is optimized for faster retrieval. 

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE IF EXISTS flights;
# MAGIC 
# MAGIC -- Create a standard table and import US based flights for year 2008
# MAGIC -- USING Clause: Specify "delta" format instead of the standard parquet format
# MAGIC -- PARTITIONED BY clause: Orginize data based on "Origin" column (Originating Airport code).
# MAGIC -- FROM Clause: Import data from a csv file.
# MAGIC CREATE TABLE flights
# MAGIC USING delta
# MAGIC PARTITIONED BY (Origin)
# MAGIC SELECT _c0 as Year, _c1 as Month, _c2 as DayofMonth, _c3 as DayOfWeek, _c4 as DepartureTime, _c5 as CRSDepartureTime, _c6 as ArrivalTime, 
# MAGIC   _c7 as CRSArrivalTime, _c8 as UniqueCarrier, _c9 as FlightNumber, _c10 as TailNumber, _c11 as ActualElapsedTime, _c12 as CRSElapsedTime, 
# MAGIC     _c13 as AirTime, _c14 as ArrivalDelay, _c15 as DepartureDelay, _c16 as Origin, _c17 as Destination, _c18 as Distance, 
# MAGIC     _c19 as TaxiIn, _c20 as TaxiOut, _c21 as Cancelled, _c22 as CancellationCode, _c23 as Diverted, _c24 as CarrierDelay, 
# MAGIC     _c25 as WeatherDelay, _c26 as NASDelay, _c27 as SecurityDelay, _c28 as LateAircraftDelay 
# MAGIC FROM csv.`dbfs:/databricks-datasets/asa/airlines/2008.csv`;

# COMMAND ----------

# MAGIC %md
# MAGIC OPTIMIZE consolidates files and orders the Databricks Delta table data by DayofWeek under each partition for faster retrieval

# COMMAND ----------

# MAGIC %sql
# MAGIC OPTIMIZE flights ZORDER BY (DayofWeek);

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Get top 20 cities with highest monthly total flights on first day of week. & observe the latency! 
# MAGIC -- This query may take over a minute in certain cluster configurations. 
# MAGIC SELECT Month, Origin, count(*) as TotalFlights 
# MAGIC FROM flights
# MAGIC WHERE DayOfWeek = 1 
# MAGIC GROUP BY Month, Origin 
# MAGIC ORDER BY TotalFlights DESC
# MAGIC LIMIT 20;

# COMMAND ----------

# MAGIC %md
# MAGIC The query over the Databricks Delta table runs much faster after `OPTIMIZE` is run. How much faster the query runs can depend on the configuration of the cluster you are running on, however should be **5-10X** faster compared to the standard table. 

# COMMAND ----------


