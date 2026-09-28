from datetime import datetime

from database import (
    decisions_collection,
    purchase_orders_collection,
    inventory_collection,
    suppliers_collection,
)


def validate_execution(decision_id: str):
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

    purchase_order = purchase_orders_collection.find_one(
        {"decision_id": decision_id}
    )

    if not purchase_order:
        return {
            "success": False,
            "status": "NO_PURCHASE_ORDER",
            "message": (
                "No purchase order was found for this decision."
            ),
            "decision_id": decision_id,
            "validation_passed": False,
        }

    store_id = decision.get("store_id")
    product_id = decision.get("product_id")
    supplier_id = purchase_order.get("supplier_id")
    quantity = purchase_order.get("quantity", 0)
    purchase_order_id = purchase_order.get("purchase_order_id")

    execution = decision.get("execution", {})
    inventory_before = execution.get("inventory_before")
    supplier_before = execution.get("supplier_before")

    inventory = inventory_collection.find_one(
        {
            "store_id": store_id,
            "product_id": product_id,
        }
    )

    supplier = suppliers_collection.find_one(
        {"supplier_id": supplier_id}
    )

    checks = []

    # Check that the purchase order exists.
    checks.append({
        "check": "PURCHASE_ORDER_EXISTS",
        "passed": True,
        "message": "Purchase order exists in MongoDB.",
    })

    # Check that the purchase order was created correctly.
    po_status = purchase_order.get("status")
    po_status_passed = po_status == "CREATED"

    checks.append({
        "check": "PURCHASE_ORDER_STATUS",
        "passed": po_status_passed,
        "expected": "CREATED",
        "actual": po_status,
        "message": (
            "Purchase order status is valid."
            if po_status_passed
            else
            "Purchase order status is invalid."
        ),
    })

    # Check that execution was recorded.
    execution_passed = (
        execution.get("status") == "EXECUTED"
    )

    checks.append({
        "check": "EXECUTION_RECORD",
        "passed": execution_passed,
        "message": (
            "Execution record confirms the purchase."
            if execution_passed
            else
            "Execution record is missing or invalid."
        ),
    })

    # Verify the store inventory changed by the expected amount.
    if inventory is not None and inventory_before is not None:
        expected_current = (
            inventory_before.get("current_quantity", 0)
            + quantity
        )

        expected_available = (
            inventory_before.get("available_quantity", 0)
            + quantity
        )

        inventory_passed = (
            inventory.get("current_quantity")
            == expected_current
            and
            inventory.get("available_quantity")
            == expected_available
        )

        inventory_message = (
            "Store inventory increased by the purchased quantity."
            if inventory_passed
            else
            "Store inventory did not change as expected."
        )
    else:
        inventory_passed = False
        inventory_message = (
            "Store inventory or pre-execution inventory "
            "snapshot is missing."
        )

    checks.append({
        "check": "STORE_INVENTORY_UPDATED",
        "passed": inventory_passed,
        "message": inventory_message,
    })

    # Verify that supplier inventory decreased by the expected amount.
    if supplier is not None and supplier_before is not None:
        expected_supplier_stock = (
            supplier_before.get("available_quantity", 0)
            - quantity
        )

        supplier_passed = (
            supplier.get("available_quantity")
            == expected_supplier_stock
        )

        supplier_message = (
            "Supplier inventory decreased by the purchased quantity."
            if supplier_passed
            else
            "Supplier inventory did not change as expected."
        )
    else:
        supplier_passed = False
        supplier_message = (
            "Supplier or pre-execution supplier "
            "snapshot is missing."
        )

    checks.append({
        "check": "SUPPLIER_INVENTORY_UPDATED",
        "passed": supplier_passed,
        "message": supplier_message,
    })

    all_passed = all(
        check["passed"]
        for check in checks
    )

    validation_status = (
        "PASSED"
        if all_passed
        else
        "FAILED"
    )

    validated_at = datetime.now().isoformat()

    decisions_collection.update_one(
        {"decision_id": decision_id},
        {
            "$set": {
                "validation": {
                    "status": validation_status,
                    "validation_passed": all_passed,
                    "validated_at": validated_at,
                    "purchase_order_id": purchase_order_id,
                    "checks": checks,
                }
            }
        },
    )

    return {
        "success": all_passed,
        "status": validation_status,
        "decision_id": decision_id,
        "purchase_order_id": purchase_order_id,
        "validation_passed": all_passed,
        "checks": checks,
        "validated_at": validated_at,
        "message": (
            "All execution checks passed."
            if all_passed
            else
            "One or more execution checks failed."
        ),
    }