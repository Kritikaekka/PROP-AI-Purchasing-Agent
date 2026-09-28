from datetime import datetime

from database import (
    stores_collection,
    inventory_collection,
    sales_collection,
    forecasts_collection,
    suppliers_collection,
    purchase_orders_collection,
    decisions_collection,
)


def investigate_purchase(store_id: str, product_id: str):
    """
    Investigate a purchasing recommendation using current
    inventory, demand, supplier and store constraints.
    """

    store = stores_collection.find_one(
        {"store_id": store_id},
        {"_id": 0},
    )

    if not store:
        return {
            "error": "Store information not found.",
            "store_id": store_id,
            "product_id": product_id,
        }

    inventory = inventory_collection.find_one(
        {
            "store_id": store_id,
            "product_id": product_id,
        },
        {"_id": 0},
    )

    if not inventory:
        return {
            "error": "Inventory information not found.",
            "store_id": store_id,
            "product_id": product_id,
        }

    current_inventory = inventory.get(
        "current_quantity",
        inventory.get("quantity", 0),
    )

    reserved_quantity = inventory.get(
        "reserved_quantity",
        0,
    )

    available_inventory = max(
        current_inventory - reserved_quantity,
        0,
    )

    original_recommendation = inventory.get(
        "recommended_purchase_quantity",
        0,
    )

    sales = list(
        sales_collection.find(
            {
                "store_id": store_id,
                "product_id": product_id,
            },
            {"_id": 0},
        ).sort("date", 1)
    )

    total_units_sold = sum(
        sale.get("units_sold", 0)
        for sale in sales
    )

    number_of_sales_days = len(sales)

    if number_of_sales_days > 0:
        average_daily_sales = round(
            total_units_sold / number_of_sales_days,
            2,
        )
    else:
        average_daily_sales = 0

    forecast = forecasts_collection.find_one(
        {
            "store_id": store_id,
            "product_id": product_id,
        },
        {"_id": 0},
    )

    if not forecast:
        return {
            "error": "Forecast information not found.",
            "store_id": store_id,
            "product_id": product_id,
        }

    base_forecast = forecast.get(
        "forecast_7_day",
        0,
    )

    trend_adjusted_forecast = forecast.get(
        "trend_adjusted_forecast",
        base_forecast,
    )

    forecast_status = forecast.get(
        "status",
        "unknown",
    )

    purchase_orders = list(
        purchase_orders_collection.find(
            {
                "store_id": store_id,
                "product_id": product_id,
                "status": {
                    "$in": ["open", "OPEN"],
                },
            },
            {"_id": 0},
        )
    )

    open_purchase_order_quantity = sum(
        purchase_order.get(
            "quantity",
            purchase_order.get("ordered_quantity", 0),
        )
        for purchase_order in purchase_orders
    )

    inventory_after_open_po = (
        available_inventory
        + open_purchase_order_quantity
    )

    forecast_gap = max(
        trend_adjusted_forecast
        - inventory_after_open_po,
        0,
    )

    supplier = suppliers_collection.find_one(
        {"products": product_id},
        {"_id": 0},
    )

    if not supplier:
        return {
            "error": "Supplier information not found.",
            "store_id": store_id,
            "product_id": product_id,
        }

    supplier_id = supplier.get("supplier_id")

    supplier_available_quantity = supplier.get(
        "available_quantity",
        0,
    )

    lead_time_days = supplier.get(
        "lead_time_days",
        0,
    )

    minimum_order_quantity = supplier.get(
        "minimum_order_quantity",
        1,
    )

    unit_price = supplier.get(
        "unit_price",
        0,
    )

    storage_capacity = store.get(
        "storage_capacity",
        0,
    )

    current_storage = store.get(
        "current_storage",
        available_inventory,
    )

    available_storage = max(
        storage_capacity - current_storage,
        0,
    )

    purchasing_budget = store.get(
        "purchasing_budget_inr",
        0,
    )

    if trend_adjusted_forecast > base_forecast:
        demand_signal = "INCREASING"
    elif trend_adjusted_forecast < base_forecast:
        demand_signal = "DECREASING"
    else:
        demand_signal = "STABLE"

    if inventory_after_open_po < base_forecast:
        inventory_risk = "HIGH"
    elif inventory_after_open_po < trend_adjusted_forecast:
        inventory_risk = "MEDIUM"
    else:
        inventory_risk = "LOW"

    # PROP calculates its own required quantity instead
    # of simply accepting the external recommendation.
    if forecast_gap > 0:
        agent_required_quantity = max(
            forecast_gap,
            minimum_order_quantity,
        )
    else:
        agent_required_quantity = 0

    agent_estimated_cost = (
        agent_required_quantity * unit_price
    )

    original_estimated_cost = (
        original_recommendation * unit_price
    )

    original_fits_budget = (
        original_estimated_cost <= purchasing_budget
    )

    original_fits_storage = (
        current_storage + original_recommendation
        <= storage_capacity
    )

    agent_fits_budget = (
        agent_estimated_cost <= purchasing_budget
    )

    agent_fits_storage = (
        current_storage + agent_required_quantity
        <= storage_capacity
    )

    agent_fits_supplier = (
        supplier_available_quantity
        >= agent_required_quantity
    )

    if forecast_status == "stale":
        action = "REVIEW_FORECAST"
        recommended_quantity = 0

        decision_reason = (
            "The demand forecast is stale, so PROP "
            "requires further investigation before "
            "recommending a purchase."
        )

    elif forecast_gap <= 0:
        action = "NO_PURCHASE"
        recommended_quantity = 0

        decision_reason = (
            "Current inventory and open purchase orders "
            "are sufficient to cover expected demand."
        )

    elif not agent_fits_supplier:
        action = "SUPPLIER_SHORTAGE"
        recommended_quantity = agent_required_quantity

        decision_reason = (
            "Additional inventory is required, but "
            "the supplier cannot fulfill PROP's "
            "calculated requirement."
        )

    else:
        action = "CREATE_PURCHASE_ORDER"
        recommended_quantity = agent_required_quantity

        decision_reason = (
            "PROP independently calculated the required "
            "quantity from expected demand and current "
            "inventory instead of accepting the original "
            "purchasing recommendation."
        )

    estimated_cost = (
        recommended_quantity * unit_price
    )

    timestamp = datetime.now()

    decision_id = (
        f"PROP-{timestamp.strftime('%Y%m%d%H%M%S%f')}"
    )

    decision = {
        "decision_id": decision_id,
        "timestamp": timestamp.isoformat(),
        "agent": {
            "name": "PROP",
            "version": "2.0",
        },
        "question": (
            f"Should {store_id} purchase more "
            f"of {product_id}, and is the existing "
            f"purchasing recommendation appropriate?"
        ),
        "store_id": store_id,
        "product_id": product_id,

        "evidence": {
            "inventory": {
                "current_quantity": current_inventory,
                "reserved_quantity": reserved_quantity,
                "available_quantity": available_inventory,
                "original_recommendation_quantity": (
                    original_recommendation
                ),
            },

            "sales": {
                "days_observed": number_of_sales_days,
                "total_units_sold": total_units_sold,
                "average_daily_sales": average_daily_sales,
            },

            "forecast": {
                "base_7_day_forecast": base_forecast,
                "trend_adjusted_forecast": (
                    trend_adjusted_forecast
                ),
                "status": forecast_status,
            },

            "purchase_orders": {
                "open_orders": len(purchase_orders),
                "open_order_quantity": (
                    open_purchase_order_quantity
                ),
                "inventory_after_open_po": (
                    inventory_after_open_po
                ),
            },

            "supplier": {
                "supplier_id": supplier_id,
                "available_quantity": (
                    supplier_available_quantity
                ),
                "lead_time_days": lead_time_days,
                "minimum_order_quantity": (
                    minimum_order_quantity
                ),
                "unit_price": unit_price,
            },

            "store_constraints": {
                "purchasing_budget_inr": purchasing_budget,
                "storage_capacity": storage_capacity,
                "current_storage": current_storage,
                "available_storage": available_storage,
            },
        },

        "analysis": {
            "forecast_gap": forecast_gap,
            "demand_signal": demand_signal,
            "inventory_risk": inventory_risk,

            "original_recommendation": {
                "quantity": original_recommendation,
                "estimated_cost_inr": (
                    original_estimated_cost
                ),
                "fits_budget": original_fits_budget,
                "fits_storage": original_fits_storage,
            },

            "agent_recommendation": {
                "quantity": agent_required_quantity,
                "estimated_cost_inr": (
                    agent_estimated_cost
                ),
                "fits_budget": agent_fits_budget,
                "fits_storage": agent_fits_storage,
                "fits_supplier_capacity": (
                    agent_fits_supplier
                ),
            },

            "supplier_can_fulfill": (
                supplier_available_quantity
                >= agent_required_quantity
            ),

            "decision_reason": decision_reason,
        },

        "recommendation": {
            "action": action,
            "quantity": recommended_quantity,
            "estimated_cost_inr": estimated_cost,
            "supplier_id": supplier_id,

            "original_quantity": (
                original_recommendation
            ),

            "agent_calculated_quantity": (
                agent_required_quantity
            ),
        },

        "human_approval": {
            "required": True,
            "status": "PENDING",
        },
    }

    try:
        decisions_collection.insert_one(
            decision.copy()
        )
    except Exception as error:
        decision["audit_warning"] = str(error)

    return decision