from datetime import datetime

from database import decisions_collection


def approve_decision(decision_id: str):
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

    final_decision = decision.get("final_decision", {})
    challenge = decision.get("challenge", {})

    if not challenge.get("can_proceed", False):
        return {
            "success": False,
            "status": "BLOCKED",
            "message": (
                "This decision cannot be approved because "
                "the Challenge Engine has blocked it."
            ),
            "decision_id": decision_id,
            "challenge_status": challenge.get("challenge_status"),
        }

    if final_decision.get("final_action") != "CREATE_PURCHASE_ORDER":
        return {
            "success": False,
            "status": "NOT_PURCHASABLE",
            "message": (
                "This decision does not contain an "
                "executable purchase recommendation."
            ),
            "decision_id": decision_id,
        }

    approved_at = datetime.now().isoformat()

    approval = {
        "required": True,
        "status": "APPROVED",
        "approved_at": approved_at,
    }

    decisions_collection.update_one(
        {"decision_id": decision_id},
        {"$set": {"human_approval": approval}},
    )

    return {
        "success": True,
        "status": "APPROVED",
        "message": (
            "Human approval recorded. "
            "The decision is ready for execution."
        ),
        "decision_id": decision_id,
        "approved_at": approved_at,
    }


def reject_decision(
    decision_id: str,
    reason: str = "Rejected by human reviewer.",
):
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

    rejected_at = datetime.now().isoformat()

    rejection = {
        "required": True,
        "status": "REJECTED",
        "rejected_at": rejected_at,
        "reason": reason,
    }

    decisions_collection.update_one(
        {"decision_id": decision_id},
        {"$set": {"human_approval": rejection}},
    )

    return {
        "success": True,
        "status": "REJECTED",
        "message": "Human rejection recorded.",
        "decision_id": decision_id,
        "rejected_at": rejected_at,
        "reason": reason,
    }