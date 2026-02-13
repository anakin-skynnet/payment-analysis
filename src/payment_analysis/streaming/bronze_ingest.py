# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer - Payment Events Ingestion
# MAGIC 
# MAGIC Lakeflow for ingesting raw payment events into the Bronze layer.

# COMMAND ----------

import dlt  # type: ignore[import-untyped]
from pyspark.sql.functions import (  # type: ignore[import-untyped]
    array,
    col,
    concat,
    current_timestamp,
    lit,
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Table: Raw Payment Events

# COMMAND ----------

@dlt.table(
    name="payments_raw_bronze",
    comment="Raw payment events ingested from transaction simulator stream",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true",
    },
)
@dlt.expect_all_or_drop({
    "valid_transaction_id": "transaction_id IS NOT NULL AND transaction_id != ''",
    "valid_amount": "amount IS NOT NULL AND amount > 0",
    "valid_timestamp": "event_timestamp IS NOT NULL",
    "valid_merchant": "merchant_id IS NOT NULL",
})
def payments_raw_bronze():
    """
    Ingest raw payment events from the simulator output table via CDF.

    Data is generated exclusively by the transaction simulator
    (transaction_simulator.py) and written to ``payments_stream_input``.
    This table streams new records from that source — no data generation here.

    In production, replace with Auto Loader (cloudFiles) or Kafka source.
    """
    return (
        spark.readStream  # type: ignore[name-defined]
        .format("delta")
        .option("readChangeFeed", "true")
        .table("payments_stream_input")
        .filter(col("_change_type").isin(["insert", "update_postimage"]))
        .drop("_change_type", "_commit_version", "_commit_timestamp")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Table: Merchant Dimension

# COMMAND ----------

@dlt.table(
    name="merchants_dim_bronze",
    comment="Merchant dimension data",
    table_properties={
        "quality": "bronze"
    }
)
def merchants_dim_bronze():
    """Merchant dimension table for enrichment."""
    
    return (
        spark.range(50)  # type: ignore[name-defined]
        .withColumn("merchant_id", concat(lit("m_"), col("id").cast("string")))
        .withColumn("merchant_name", concat(lit("Merchant "), col("id").cast("string")))
        .withColumn("merchant_segment", array(lit("Travel"), lit("Retail"), lit("Gaming"), lit("Digital"), lit("Entertainment")).getItem((col("id") % 5).cast("int")))
        .withColumn("merchant_country", array(lit("US"), lit("GB"), lit("CA")).getItem((col("id") % 3).cast("int")))
        .withColumn("merchant_risk_tier", array(lit("low"), lit("medium"), lit("high")).getItem((col("id") % 3).cast("int")))
        .withColumn("created_at", current_timestamp())
        .drop("id")
    )
