from datetime import datetime

from database import (
    decisions_collection,
    purchase_orders_collection,
    inventory_collection,
    suppliers_collection,
)


def execute_purchase(decision_id: str):
    decision = decisions_collection.find_one(
        {"decision_id": decision_id}
    )

    if not decision:
        return {
            "success": False,
            "status": "NOT_FOUND",
            "message": "Decision not found.",
            "decision_id": decision_id,
        }

    challenge = decision.get("challenge", {})
    final_decision = decision.get("final_decision", {})
    human_approval = decision.get("human_approval", {})

    # Execution is allowed only when the challenge passes.
    if not challenge.get("can_proceed", False):
        return {
            "success": False,
            "status": "BLOCKED",
            "message": (
                "Execution blocked because the Challenge "
                "Engine did not allow the decision to proceed."
            ),
            "decision_id": decision_id,
        }

    # Only a purchase order can reach the execution stage.
    if final_decision.get("final_action") != "CREATE_PURCHASE_ORDER":
        return {
            "success": False,
            "status": "NOT_PURCHASABLE",
            "message": (
                "The final decision does not request "
                "a purchase order."
            ),
            "decision_id": decision_id,
        }

    # Human approval is mandatory before making the purchase.
    if human_approval.get("status") != "APPROVED":
        return {
            "success": False,
            "status": "APPROVAL_REQUIRED",
            "message": (
                "Human approval is required before execution."
            ),
            "decision_id": decision_id,
        }

    store_id = decision.get("store_id")
    product_id = decision.get("product_id")
    supplier_id = final_decision.get("supplier_id")
    quantity = final_decision.get("final_quantity", 0)

    supplier = suppliers_collection.find_one(
        {"supplier_id": supplier_id}
    )

    inventory = inventory_collection.find_one(
        {
            "store_id": store_id,
            "product_id": product_id,
        }
    )

    if not supplier:
        return {
            "success": False,
            "status": "SUPPLIER_NOT_FOUND",
            "message": "Supplier not found.",
            "decision_id": decision_id,
        }

    if not inventory:
        return {
            "success": False,
            "status": "INVENTORY_NOT_FOUND",
            "message": "Store inventory not found.",
            "decision_id": decision_id,
        }

    if quantity <= 0:
        return {
            "success": False,
            "status": "INVALID_QUANTITY",
            "message": "Purchase quantity must be greater than zero.",
            "decision_id": decision_id,
        }

    supplier_available = supplier.get(
        "available_quantity",
        0,
    )

    if supplier_available < quantity:
        return {
            "success": False,
            "status": "SUPPLIER_SHORTAGE",
            "message": (
                "Supplier does not have enough inventory "
                "for this purchase."
            ),
            "decision_id": decision_id,
            "requested_quantity": quantity,
            "supplier_available_quantity": supplier_available,
        }

    # Prevent the same decision from creating multiple POs.
    existing_order = purchase_orders_collection.find_one(
        {"decision_id": decision_id}
    )

    if existing_order:
        return {
            "success": False,
            "status": "ALREADY_EXECUTED",
            "message": (
                "A purchase order has already been created "
                "for this decision."
            ),
            "decision_id": decision_id,
            "purchase_order_id": existing_order.get(
                "purchase_order_id"
            ),
        }

    inventory_before = {
        "current_quantity": inventory.get(
            "current_quantity",
            0,
        ),
        "available_quantity": inventory.get(
            "available_quantity",
            0,
        ),
    }

    supplier_before = {
        "available_quantity": supplier.get(
            "available_quantity",
            0,
        ),
    }

    unit_price = supplier.get("unit_price", 0)
    total_cost = quantity * unit_price

    purchase_order_id = (
        "PO-"
        + datetime.now().strftime("%Y%m%d%H%M%S%f")
    )

    executed_at = datetime.now().isoformat()

    purchase_order = {
        "purchase_order_id": purchase_order_id,
        "decision_id": decision_id,
        "store_id": store_id,
        "product_id": product_id,
        "supplier_id": supplier_id,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_cost_inr": total_cost,
        "status": "CREATED",
        "created_at": executed_at,
        "execution": {
            "approved_by_human": True,
            "executed_by": "PROP",
            "executed_at": executed_at,
        },
    }

    purchase_orders_collection.insert_one(purchase_order)

    suppliers_collection.update_one(
        {"supplier_id": supplier_id},
        {
            "$inc": {
                "available_quantity": -quantity,
            }
        },
    )

    inventory_collection.update_one(
        {
            "store_id": store_id,
            "product_id": product_id,
        },
        {
            "$inc": {
                "current_quantity": quantity,
                "available_quantity": quantity,
            }
        },
    )

    decisions_collection.update_one(
        {"decision_id": decision_id},
        {
            "$set": {
                "execution": {
                    "status": "EXECUTED",
                    "purchase_order_id": purchase_order_id,
                    "quantity": quantity,
                    "total_cost_inr": total_cost,
                    "executed_at": executed_at,
                    "inventory_before": inventory_before,
                    "supplier_before": supplier_before,
                }
            }
        },
    )

    return {
        "success": True,
        "status": "EXECUTED",
        "message": (
            "Purchase order created successfully "
            "and inventory records were updated."
        ),
        "decision_id": decision_id,
        "purchase_order": {
            "purchase_order_id": purchase_order_id,
            "store_id": store_id,
            "product_id": product_id,
            "supplier_id": supplier_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_cost_inr": total_cost,
            "status": "CREATED",
        },
        "execution": {
            "executed_by": "PROP",
            "executed_at": executed_at,
        },
    }