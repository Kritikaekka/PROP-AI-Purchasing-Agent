from datetime import datetime


def make_final_decision(investigation: dict, challenge: dict):
    recommendation = investigation.get("recommendation", {})

    challenge_status = challenge.get(
        "challenge_status",
        "BLOCKED",
    )

    can_proceed = challenge.get(
        "can_proceed",
        False,
    )

    # Business-level decision made by the challenge stage.
    # Expected values:
    # ACCEPT
    # MODIFY
    # REJECT
    # INVESTIGATE_FURTHER
    business_decision = challenge.get(
        "business_decision",
        "INVESTIGATE_FURTHER",
    )

    original_action = recommendation.get(
        "action",
        "NO_PURCHASE",
    )

    # The original quantity comes from the purchasing system's
    # recommendation, while recommendation["quantity"] is
    # PROP's independently calculated quantity.
    original_quantity = recommendation.get(
        "original_quantity",
        recommendation.get("quantity", 0),
    )

    final_quantity = recommendation.get(
        "quantity",
        0,
    )

    supplier_id = recommendation.get(
        "supplier_id"
    )

    # First try to get the original cost from the investigation.
    # If it is not present there, use the value calculated by
    # the challenge engine.
    original_estimated_cost = recommendation.get(
        "original_estimated_cost_inr",
        challenge.get(
            "recommendation_review",
            {},
        ).get(
            "original_cost_inr",
            0,
        ),
    )

    estimated_cost = recommendation.get(
        "estimated_cost_inr",
        0,
    )

    decided_at = datetime.now().isoformat()

    # ---------------------------------------------------------
    # INVESTIGATE FURTHER
    # ---------------------------------------------------------

    if business_decision == "INVESTIGATE_FURTHER":
        return {
            "decision_stage": "DECIDE",
            "business_decision": "INVESTIGATE_FURTHER",
            "final_action": "REVIEW_FORECAST",
            "original_quantity": original_quantity,
            "final_quantity": 0,
            "original_estimated_cost_inr": (
                original_estimated_cost
            ),
            "estimated_cost_inr": 0,
            "supplier_id": supplier_id,
            "status": "WAITING_FOR_HUMAN_REVIEW",
            "can_execute": False,
            "reason": (
                "PROP found an issue that requires further "
                "investigation before a purchasing decision "
                "can safely be executed."
            ),
            "challenge_status": challenge_status,
            "decided_at": decided_at,
        }

    # ---------------------------------------------------------
    # REJECT
    # ---------------------------------------------------------

    if business_decision == "REJECT":
        return {
            "decision_stage": "DECIDE",
            "business_decision": "REJECT",
            "final_action": "NO_PURCHASE",
            "original_quantity": original_quantity,
            "final_quantity": 0,
            "original_estimated_cost_inr": (
                original_estimated_cost
            ),
            "estimated_cost_inr": 0,
            "supplier_id": supplier_id,
            "status": "NO_ACTION_REQUIRED",
            "can_execute": False,
            "reason": (
                "PROP rejected the purchasing recommendation "
                "because the investigated conditions do not "
                "justify creating a purchase order."
            ),
            "challenge_status": challenge_status,
            "decided_at": decided_at,
        }

    # ---------------------------------------------------------
    # ACCEPT
    # ---------------------------------------------------------

    if (
        business_decision == "ACCEPT"
        and original_action == "CREATE_PURCHASE_ORDER"
        and can_proceed
    ):
        return {
            "decision_stage": "DECIDE",
            "business_decision": "ACCEPT",
            "final_action": "CREATE_PURCHASE_ORDER",
            "original_quantity": original_quantity,
            "final_quantity": final_quantity,
            "original_estimated_cost_inr": (
                original_estimated_cost
            ),
            "estimated_cost_inr": estimated_cost,
            "supplier_id": supplier_id,
            "status": "PENDING_HUMAN_APPROVAL",
            "can_execute": False,
            "reason": (
                "PROP accepted the purchasing system's "
                "recommendation. The recommended purchase "
                "can proceed to human approval."
            ),
            "challenge_status": challenge_status,
            "decided_at": decided_at,
        }

    # ---------------------------------------------------------
    # MODIFY
    # ---------------------------------------------------------

    if (
        business_decision == "MODIFY"
        and original_action == "CREATE_PURCHASE_ORDER"
        and can_proceed
    ):
        return {
            "decision_stage": "DECIDE",
            "business_decision": "MODIFY",
            "final_action": "CREATE_PURCHASE_ORDER",
            "original_quantity": original_quantity,
            "final_quantity": final_quantity,
            "original_estimated_cost_inr": (
                original_estimated_cost
            ),
            "estimated_cost_inr": estimated_cost,
            "supplier_id": supplier_id,
            "status": "PENDING_HUMAN_APPROVAL",
            "can_execute": False,
            "reason": (
                f"PROP modified the purchasing system's "
                f"recommendation from {original_quantity} units "
                f"to {final_quantity} units after considering "
                f"demand, inventory, supplier constraints, "
                f"budget, and storage capacity. Human approval "
                f"is required before execution."
            ),
            "challenge_status": challenge_status,
            "decided_at": decided_at,
        }

    # ---------------------------------------------------------
    # NO PURCHASE FROM ORIGINAL RECOMMENDATION
    # ---------------------------------------------------------

    if original_action == "NO_PURCHASE":
        return {
            "decision_stage": "DECIDE",
            "business_decision": (
                business_decision
                if business_decision
                else "REJECT"
            ),
            "final_action": "NO_PURCHASE",
            "original_quantity": original_quantity,
            "final_quantity": 0,
            "original_estimated_cost_inr": (
                original_estimated_cost
            ),
            "estimated_cost_inr": 0,
            "supplier_id": supplier_id,
            "status": "NO_ACTION_REQUIRED",
            "can_execute": False,
            "reason": (
                "Current inventory and demand conditions "
                "do not require a purchase."
            ),
            "challenge_status": challenge_status,
            "decided_at": decided_at,
        }

    # ---------------------------------------------------------
    # ORIGINAL RECOMMENDATION REQUIRES FORECAST REVIEW
    # ---------------------------------------------------------

    if original_action == "REVIEW_FORECAST":
        return {
            "decision_stage": "DECIDE",
            "business_decision": "INVESTIGATE_FURTHER",
            "final_action": "REVIEW_FORECAST",
            "original_quantity": original_quantity,
            "final_quantity": 0,
            "original_estimated_cost_inr": (
                original_estimated_cost
            ),
            "estimated_cost_inr": 0,
            "supplier_id": supplier_id,
            "status": "WAITING_FOR_HUMAN_REVIEW",
            "can_execute": False,
            "reason": (
                "The demand forecast requires human review "
                "before a purchase can be created."
            ),
            "challenge_status": challenge_status,
            "decided_at": decided_at,
        }

    # ---------------------------------------------------------
    # SAFE FALLBACK
    # ---------------------------------------------------------

    return {
        "decision_stage": "DECIDE",
        "business_decision": "INVESTIGATE_FURTHER",
        "final_action": "REVIEW",
        "original_quantity": original_quantity,
        "final_quantity": 0,
        "original_estimated_cost_inr": (
            original_estimated_cost
        ),
        "estimated_cost_inr": 0,
        "supplier_id": supplier_id,
        "status": "WAITING_FOR_HUMAN_REVIEW",
        "can_execute": False,
        "reason": (
            "PROP could not safely determine an "
            "executable purchasing action."
        ),
        "challenge_status": challenge_status,
        "decided_at": decided_at,
    }