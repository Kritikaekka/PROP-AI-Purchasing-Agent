from datetime import datetime, timedelta

from database import (
    stores_collection,
    inventory_collection,
    sales_collection,
    forecasts_collection,
    purchase_orders_collection,
    suppliers_collection,
    decisions_collection,
)


DEMO_STORE_ID = "DEMO-DEL-01"
PRODUCT_ID = "HIR-SHELTER-BB"
SUPPLIER_ID = "SUP-001"

ORIGINAL_SUPPLIER_QUANTITY = 36
DEMO_SUPPLIER_QUANTITY = 100

ORIGINAL_RECOMMENDATION = 800
DEMO_BUDGET = 100000
DEMO_STORAGE_CAPACITY = 100
DEMO_CURRENT_STORAGE = 10


def setup_demo():
    print("\n========================================")
    print("PROP PURCHASING OPERATIONS DEMO SETUP")
    print("========================================\n")

    # ---------------------------------------------------------
    # 1. CREATE / RESET DEMO STORE
    # ---------------------------------------------------------

    stores_collection.update_one(
        {"store_id": DEMO_STORE_ID},
        {
            "$set": {
                "store_id": DEMO_STORE_ID,
                "name": "PROP Demo Delhi Store",
                "city": "Delhi",
                "region": "Delhi NCR",
                "status": "active",

                # Purchasing constraints
                "purchasing_budget_inr": DEMO_BUDGET,
                "storage_capacity": DEMO_STORAGE_CAPACITY,
                "current_storage": DEMO_CURRENT_STORAGE,
            }
        },
        upsert=True,
    )

    print("Demo store ready:", DEMO_STORE_ID)

    # ---------------------------------------------------------
    # 2. RESET INVENTORY
    # ---------------------------------------------------------

    inventory_collection.update_one(
        {
            "store_id": DEMO_STORE_ID,
            "product_id": PRODUCT_ID,
        },
        {
            "$set": {
                "store_id": DEMO_STORE_ID,
                "product_id": PRODUCT_ID,

                "quantity": 10,
                "current_quantity": 10,
                "reserved_quantity": 0,
                "available_quantity": 10,

                # Original purchasing-system recommendation
                "recommended_purchase_quantity": (
                    ORIGINAL_RECOMMENDATION
                ),
            }
        },
        upsert=True,
    )

    print("Demo inventory ready: 10 units")

    print(
        "Original purchasing recommendation:",
        ORIGINAL_RECOMMENDATION,
        "units",
    )

    # ---------------------------------------------------------
    # 3. RESET SALES HISTORY
    # ---------------------------------------------------------

    sales_collection.delete_many(
        {
            "store_id": DEMO_STORE_ID,
            "product_id": PRODUCT_ID,
        }
    )

    today = datetime.now()

    # Seven days of sales at 10 units per day.
    for i in range(7):
        sale_date = (
            today - timedelta(days=6 - i)
        ).strftime("%Y-%m-%d")

        sales_collection.insert_one(
            {
                "store_id": DEMO_STORE_ID,
                "product_id": PRODUCT_ID,
                "date": sale_date,
                "units_sold": 10,
            }
        )

    print("Demo sales history ready: 7 days / 70 units")

    # ---------------------------------------------------------
    # 4. RESET FORECAST
    # ---------------------------------------------------------

    forecasts_collection.update_one(
        {
            "store_id": DEMO_STORE_ID,
            "product_id": PRODUCT_ID,
        },
        {
            "$set": {
                "store_id": DEMO_STORE_ID,
                "product_id": PRODUCT_ID,

                "forecast_7_day": 60,
                "trend_adjusted_forecast": 60,

                "status": "current",
                "generated_at": today.isoformat(),
            }
        },
        upsert=True,
    )

    print("Demo forecast ready: 60 units / current")

    # ---------------------------------------------------------
    # 5. CLEAR OLD PURCHASE ORDERS
    # ---------------------------------------------------------

    purchase_orders_collection.delete_many(
        {
            "store_id": DEMO_STORE_ID,
            "product_id": PRODUCT_ID,
        }
    )

    print("Old demo purchase orders cleared")

    # ---------------------------------------------------------
    # 6. CLEAR OLD DEMO DECISIONS
    # ---------------------------------------------------------

    decisions_collection.delete_many(
        {
            "store_id": DEMO_STORE_ID,
            "product_id": PRODUCT_ID,
        }
    )

    print("Old demo decisions cleared")

    # ---------------------------------------------------------
    # 7. CREATE / RESET DEMO SUPPLIER
    # ---------------------------------------------------------

    # The decision engine searches for a supplier using:
    #
    #     {"products": product_id}
    #
    # Therefore the supplier MUST contain the product ID.
    # upsert=True also ensures the supplier is created if
    # it does not already exist in MongoDB.

    suppliers_collection.update_one(
        {"supplier_id": SUPPLIER_ID},
        {
            "$set": {
                "supplier_id": SUPPLIER_ID,
                "supplier_name": "Hirono Demo Supplier",

                # Important: this allows the investigation
                # engine to find this supplier for the product.
                "products": [PRODUCT_ID],

                "available_quantity": DEMO_SUPPLIER_QUANTITY,
                "lead_time_days": 4,
                "minimum_order_quantity": 12,
                "unit_price": 1800,
            }
        },
        upsert=True,
    )

    print(
        "Demo supplier stock set to:",
        DEMO_SUPPLIER_QUANTITY,
    )

    # ---------------------------------------------------------
    # 8. DISPLAY EXPECTED SCENARIO
    # ---------------------------------------------------------

    original_cost = (
        ORIGINAL_RECOMMENDATION * 1800
    )

    prop_quantity = 50

    prop_cost = prop_quantity * 1800

    print("\n========================================")
    print("DEMO SCENARIO READY")
    print("========================================")

    print("Store:                  ", DEMO_STORE_ID)
    print("Product:                ", PRODUCT_ID)

    print("\nDemand / inventory:")
    print("Inventory:              ", 10)
    print("7-day sales:            ", 70)
    print("Daily average:          ", 10)
    print("Forecast:               ", 60)
    print("Forecast status:        ", "current")
    print("Expected demand gap:    ", 50)

    print("\nSupplier:")
    print(
        "Supplier ID:            ",
        SUPPLIER_ID,
    )
    print(
        "Supplier stock:         ",
        DEMO_SUPPLIER_QUANTITY,
    )
    print("MOQ:                    ", 12)
    print("Lead time:              ", "4 days")
    print("Unit price:             ", "₹1,800")

    print("\nStore constraints:")
    print(
        "Purchasing budget:      ",
        f"₹{DEMO_BUDGET:,}",
    )
    print(
        "Storage capacity:       ",
        DEMO_STORAGE_CAPACITY,
    )
    print(
        "Current storage:        ",
        DEMO_CURRENT_STORAGE,
    )
    print(
        "Available storage:      ",
        DEMO_STORAGE_CAPACITY
        - DEMO_CURRENT_STORAGE,
    )

    print("\nOriginal recommendation:")
    print(
        "Quantity:               ",
        ORIGINAL_RECOMMENDATION,
    )
    print(
        "Estimated cost:         ",
        f"₹{original_cost:,}",
    )

    print("\nExpected PROP decision:")
    print(
        "Business decision:      ",
        "MODIFY",
    )

    print(
        "Original quantity:      ",
        ORIGINAL_RECOMMENDATION,
    )

    print(
        "PROP quantity:          ",
        prop_quantity,
    )

    print(
        "PROP estimated cost:    ",
        f"₹{prop_cost:,}",
    )

    print(
        "Final action:           ",
        "CREATE_PURCHASE_ORDER",
    )

    print(
        "Human approval:         ",
        "REQUIRED",
    )

    print("\n========================================")
    print("Expected flow:")
    print("800 units")
    print("    ↓")
    print("PROP reviews constraints")
    print("    ↓")
    print("MODIFY")
    print("    ↓")
    print("50 units")
    print("    ↓")
    print("Human approval")
    print("    ↓")
    print("Purchase order")
    print("    ↓")
    print("Validation")
    print("========================================\n")


def restore_original_supplier():
    suppliers_collection.update_one(
        {"supplier_id": SUPPLIER_ID},
        {
            "$set": {
                "available_quantity": (
                    ORIGINAL_SUPPLIER_QUANTITY
                ),
            }
        },
    )

    print(
        "Supplier stock restored to",
        ORIGINAL_SUPPLIER_QUANTITY,
    )


if __name__ == "__main__":
    setup_demo()