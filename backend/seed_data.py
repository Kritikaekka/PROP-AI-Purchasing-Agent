from datetime import datetime, timedelta

from database import (
    test_connection,
    products_collection,
    stores_collection,
    inventory_collection,
    sales_collection,
    forecasts_collection,
    suppliers_collection,
    purchase_orders_collection,
)


product = {
    "product_id": "HIR-SHELTER-BB",
    "name": "Hirono Shelter Series Blind Box",
    "category": "collectible",
    "unit": "box",
    "randomized": True,
    "regular_designs": 12,
    "has_secret": True,
}


stores = [
    {
        "store_id": "DEL-04",
        "name": "Delhi Store 4",
        "city": "Delhi",
        "storage_capacity": 100,
        "current_storage": 10,
        "purchasing_budget_inr": 100000,
        "currency": "INR",
    },
    {
        "store_id": "DEL-07",
        "name": "Delhi Store 7",
        "city": "Delhi",
        "storage_capacity": 120,
        "current_storage": 68,
        "purchasing_budget_inr": 150000,
        "currency": "INR",
    },
]


inventory = [
    {
        "product_id": "HIR-SHELTER-BB",
        "store_id": "DEL-04",
        "quantity": 10,
        "current_quantity": 10,
        "reserved_quantity": 0,
        "available_quantity": 10,
        "recommended_purchase_quantity": 800,
        "last_updated": datetime.utcnow(),
    },
    {
        "product_id": "HIR-SHELTER-BB",
        "store_id": "DEL-07",
        "quantity": 68,
        "current_quantity": 68,
        "reserved_quantity": 0,
        "available_quantity": 68,
        "recommended_purchase_quantity": 800,
        "last_updated": datetime.utcnow(),
    },
]


sales = []

sales_values = [4, 5, 3, 4, 5, 6, 5, 7, 8, 9, 10, 11, 13, 15]

start_date = datetime.utcnow() - timedelta(days=14)

for index, units in enumerate(sales_values):
    sales.append(
        {
            "product_id": "HIR-SHELTER-BB",
            "store_id": "DEL-04",
            "date": start_date + timedelta(days=index),
            "units_sold": units,
        }
    )


forecast = {
    "product_id": "HIR-SHELTER-BB",
    "store_id": "DEL-04",
    "forecast_7_day": 52,
    "trend_adjusted_forecast": 78,
    "model": "7-day moving average",
    "generated_at": datetime.utcnow() - timedelta(hours=24),
    "status": "stale",
}


supplier = {
    "supplier_id": "SUP-001",
    "name": "Supplier A",
    "city": "Delhi",
    "products": [
        "HIR-SHELTER-BB",
    ],
    "unit_price": 1800,
    "minimum_order_quantity": 12,
    "available_quantity": 36,
    "lead_time_days": 4,
}


purchase_order = {
    "po_id": "PO-1001",
    "product_id": "HIR-SHELTER-BB",
    "store_id": "DEL-04",
    "supplier_id": "SUP-001",
    "quantity": 24,
    "status": "OPEN",
    "created_at": datetime.utcnow() - timedelta(days=1),
}


def seed_database():
    print("\nStarting PROP database setup...\n")

    if not test_connection():
        return

    products_collection.update_one(
        {"product_id": product["product_id"]},
        {"$set": product},
        upsert=True,
    )

    print("Product ready")

    for store in stores:
        stores_collection.update_one(
            {"store_id": store["store_id"]},
            {"$set": store},
            upsert=True,
        )

    print("Stores ready")

    for item in inventory:
        inventory_collection.update_one(
            {
                "product_id": item["product_id"],
                "store_id": item["store_id"],
            },
            {"$set": item},
            upsert=True,
        )

    print("Inventory ready")

    for sale in sales:
        sales_collection.update_one(
            {
                "product_id": sale["product_id"],
                "store_id": sale["store_id"],
                "date": sale["date"],
            },
            {"$set": sale},
            upsert=True,
        )

    print("Sales history ready")

    forecasts_collection.update_one(
        {
            "product_id": forecast["product_id"],
            "store_id": forecast["store_id"],
        },
        {"$set": forecast},
        upsert=True,
    )

    print("Forecast ready")

    suppliers_collection.update_one(
        {"supplier_id": supplier["supplier_id"]},
        {"$set": supplier},
        upsert=True,
    )

    print("Supplier ready")

    purchase_orders_collection.update_one(
        {"po_id": purchase_order["po_id"]},
        {"$set": purchase_order},
        upsert=True,
    )

    print("Open purchase order ready")

    print("\PROP database setup complete!")
    print("Database: prop_db")


if __name__ == "__main__":
    seed_database()