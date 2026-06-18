# Fabric Notebook: Inventory KPI Calculations
# Description: Loads Orders, Inventory, and Order Items delta tables from the Fabric Lakehouse,
#              calculates key performance indicators, and writes results back as delta tables.
# Run this notebook manually or schedule it via a Fabric pipeline after the Dataverse sync completes.

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# ─────────────────────────────────────────────────────────────────────────────
# 1. Load source delta tables from the Lakehouse
#    The table paths follow the default Lakehouse Tables namespace.
# ─────────────────────────────────────────────────────────────────────────────

orders_df = spark.read.format("delta").load("Tables/orders")
inventory_df = spark.read.format("delta").load("Tables/inventory")
order_items_df = spark.read.format("delta").load("Tables/order_items")

# Join order_items with inventory to get plant names on order lines
# plant_id in order_items maps to inventory_id in the inventory delta table
order_items_enriched_df = order_items_df.join(
    inventory_df.select("plant_name", F.col("inventory_id").alias("plant_id")),
    on="plant_id",
    how="left"
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. KPI: Orders by Status
#    Groups all orders by their status value and counts them.
#    Output columns: status, order_count
# ─────────────────────────────────────────────────────────────────────────────

kpi_orders_by_status = (
    orders_df
    .groupBy("status")
    .agg(F.count("*").alias("order_count"))
    .orderBy("status")
)

print("=== KPI: Orders by Status ===")
kpi_orders_by_status.show()

# Write back to Lakehouse as a delta table
kpi_orders_by_status.write.format("delta").mode("overwrite").saveAsTable("kpi_orders_by_status")
print("Written: kpi_orders_by_status")

# ─────────────────────────────────────────────────────────────────────────────
# 3. KPI: Top 10 Most Ordered Plants
#    Sums quantity_requested per plant across all order items, returns top 10.
#    Output columns: plant_name, total_quantity_ordered
# ─────────────────────────────────────────────────────────────────────────────

kpi_top_plants = (
    order_items_enriched_df
    .groupBy("plant_name")
    .agg(F.sum("quantity_requested").alias("total_quantity_ordered"))
    .orderBy(F.col("total_quantity_ordered").desc())
    .limit(10)
)

print("=== KPI: Top 10 Most Ordered Plants ===")
kpi_top_plants.show()

# Write back to Lakehouse as a delta table
kpi_top_plants.write.format("delta").mode("overwrite").saveAsTable("kpi_top_plants")
print("Written: kpi_top_plants")

# ─────────────────────────────────────────────────────────────────────────────
# 4. KPI: Inventory Health
#    Counts items below reorder threshold vs total inventory items.
#    Output columns: total_items, low_stock_items, healthy_items, low_stock_pct
# ─────────────────────────────────────────────────────────────────────────────

total_items = inventory_df.count()
low_stock_items = inventory_df.filter(
    F.col("quantity_in_stock") < F.col("reorder_threshold")
).count()
healthy_items = total_items - low_stock_items
low_stock_pct = round((low_stock_items / total_items * 100), 2) if total_items > 0 else 0.0

# Build a single-row summary DataFrame
kpi_inventory_health = spark.createDataFrame(
    [(total_items, low_stock_items, healthy_items, low_stock_pct)],
    ["total_items", "low_stock_items", "healthy_items", "low_stock_pct"]
)

print("=== KPI: Inventory Health ===")
kpi_inventory_health.show()

# Write back to Lakehouse as a delta table
kpi_inventory_health.write.format("delta").mode("overwrite").saveAsTable("kpi_inventory_health")
print("Written: kpi_inventory_health")

# ─────────────────────────────────────────────────────────────────────────────
# 5. KPI: Order Trend by Week
#    Groups orders by ISO week (year + week number) to show volume over time.
#    Output columns: year, week_of_year, order_count
# ─────────────────────────────────────────────────────────────────────────────

kpi_order_trend = (
    orders_df
    # Extract the ISO year and week number from order_date
    .withColumn("year", F.year(F.col("order_date")))
    .withColumn("week_of_year", F.weekofyear(F.col("order_date")))
    .groupBy("year", "week_of_year")
    .agg(F.count("*").alias("order_count"))
    .orderBy("year", "week_of_year")
)

print("=== KPI: Order Trend by Week ===")
kpi_order_trend.show(50)

# Write back to Lakehouse as a delta table
kpi_order_trend.write.format("delta").mode("overwrite").saveAsTable("kpi_order_trend")
print("Written: kpi_order_trend")

# ─────────────────────────────────────────────────────────────────────────────
# Done — all KPI tables have been written to the Lakehouse.
# These tables can now be used as the source for Power BI semantic models.
# ─────────────────────────────────────────────────────────────────────────────
print("All KPI tables written successfully.")
