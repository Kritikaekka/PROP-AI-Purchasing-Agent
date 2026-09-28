from datetime import datetime


def challenge_investigation(decision: dict):
    evidence = decision.get("evidence", {})
    analysis = decision.get("analysis", {})
    recommendation = decision.get("recommendation", {})

    inventory = evidence.get("inventory", {})
    sales = evidence.get("sales", {})
    forecast = evidence.get("forecast", {})
    purchase_orders = evidence.get("purchase_orders", {})
    supplier = evidence.get("supplier", {})
    store_constraints = evidence.get(
        "store_constraints",
        {},
    )

    challenges = []
    warnings = []
    passed_checks = []
    recommendation_issues = []

    current_quantity = inventory.get(
        "current_quantity",
        0,
    )

    reserved_quantity = inventory.get(
        "reserved_quantity",
        0,
    )

    original_quantity = inventory.get(
        "original_recommendation_quantity",
        recommendation.get("original_quantity", 0),
    )

    recommended_quantity = recommendation.get(
        "quantity",
        0,
    )

    average_daily_sales = sales.get(
        "average_daily_sales",
        0,
    )

    trend_adjusted_forecast = forecast.get(
        "trend_adjusted_forecast",
        0,
    )

    forecast_status = forecast.get(
        "status",
        "unknown",
    )

    open_orders = purchase_orders.get(
        "open_orders",
        0,
    )

    open_order_quantity = purchase_orders.get(
        "open_order_quantity",
        0,
    )

    supplier_available = supplier.get(
        "available_quantity",
        0,
    )

    minimum_order_quantity = supplier.get(
        "minimum_order_quantity",
        0,
    )

    lead_time_days = supplier.get(
        "lead_time_days",
        0,
    )

    unit_price = supplier.get(
        "unit_price",
        0,
    )

    forecast_gap = analysis.get(
        "forecast_gap",
        0,
    )

    demand_signal = analysis.get(
        "demand_signal",
        "UNKNOWN",
    )

    purchasing_budget = store_constraints.get(
        "purchasing_budget_inr",
        0,
    )

    storage_capacity = store_constraints.get(
        "storage_capacity",
        0,
    )

    current_storage = store_constraints.get(
        "current_storage",
        current_quantity,
    )

    available_storage = store_constraints.get(
        "available_storage",
        max(storage_capacity - current_storage, 0),
    )

    # =========================================================
    # 1. FORECAST CHECKS
    # =========================================================

    if forecast_status == "stale":
        challenges.append(
            {
                "type": "STALE_FORECAST",
                "severity": "HIGH",
                "message": (
                    "The demand forecast is stale. "
                    "Purchasing should not proceed using "
                    "an outdated forecast."
                ),
            }
        )
    else:
        passed_checks.append(
            "Forecast is current."
        )

    if (
        average_daily_sales > 0
        and trend_adjusted_forecast > 0
    ):
        expected_7_day_sales = (
            average_daily_sales * 7
        )

        difference_ratio = (
            abs(
                trend_adjusted_forecast
                - expected_7_day_sales
            )
            / expected_7_day_sales
        )

        if difference_ratio > 0.50:
            challenges.append(
                {
                    "type": "FORECAST_MISMATCH",
                    "severity": "MEDIUM",
                    "message": (
                        "The forecast differs significantly "
                        "from recent observed sales."
                    ),
                    "recent_7_day_equivalent": round(
                        expected_7_day_sales,
                        2,
                    ),
                    "forecast": trend_adjusted_forecast,
                }
            )
        else:
            passed_checks.append(
                "Forecast is reasonably consistent "
                "with observed sales."
            )

    # =========================================================
    # 2. INVENTORY CHECKS
    # =========================================================

    if current_quantity < 0:
        challenges.append(
            {
                "type": "INVALID_INVENTORY",
                "severity": "HIGH",
                "message": "Current inventory is negative.",
            }
        )
    else:
        passed_checks.append(
            "Available inventory is valid."
        )

    if reserved_quantity > current_quantity:
        challenges.append(
            {
                "type": "INVALID_RESERVED_STOCK",
                "severity": "HIGH",
                "message": (
                    "Reserved inventory exceeds current "
                    "inventory."
                ),
            }
        )
    else:
        passed_checks.append(
            "Reserved inventory is within current stock."
        )

    # =========================================================
    # 3. EXISTING PURCHASE ORDERS
    # =========================================================

    if open_orders > 0:
        warnings.append(
            {
                "type": "OPEN_PURCHASE_ORDER",
                "message": (
                    "There are already open purchase orders "
                    "for this product."
                ),
                "open_orders": open_orders,
                "open_order_quantity": open_order_quantity,
            }
        )
    else:
        passed_checks.append(
            "No open purchase orders were found."
        )

    # =========================================================
    # 4. ORIGINAL PURCHASING SYSTEM RECOMMENDATION
    #
    # These checks explain WHY PROP may need to modify
    # the original recommendation.
    #
    # They are deliberately NOT added to "challenges".
    # Otherwise an invalid original recommendation would
    # incorrectly block PROP's corrected recommendation.
    # =========================================================

    original_cost = (
        original_quantity * unit_price
    )

    original_fits_budget = (
        original_cost <= purchasing_budget
    )

    original_fits_storage = (
        current_storage + original_quantity
        <= storage_capacity
    )

    original_fits_supplier = (
        original_quantity <= supplier_available
    )

    if original_quantity > 0:

        if not original_fits_budget:
            recommendation_issues.append(
                {
                    "type": "BUDGET_CONSTRAINT",
                    "severity": "HIGH",
                    "message": (
                        "The original purchasing recommendation "
                        "exceeds the available purchasing budget."
                    ),
                    "recommended_quantity": original_quantity,
                    "estimated_cost_inr": original_cost,
                    "available_budget_inr": purchasing_budget,
                }
            )
        else:
            passed_checks.append(
                "Original recommendation fits the purchasing budget."
            )

        if not original_fits_storage:
            recommendation_issues.append(
                {
                    "type": "STORAGE_CONSTRAINT",
                    "severity": "HIGH",
                    "message": (
                        "The original purchasing recommendation "
                        "exceeds available storage capacity."
                    ),
                    "recommended_quantity": original_quantity,
                    "current_storage": current_storage,
                    "storage_capacity": storage_capacity,
                    "available_storage": available_storage,
                }
            )
        else:
            passed_checks.append(
                "Original recommendation fits available storage."
            )

        if not original_fits_supplier:
            recommendation_issues.append(
                {
                    "type": "SUPPLIER_CAPACITY",
                    "severity": "HIGH",
                    "message": (
                        "The supplier does not have enough "
                        "inventory to fulfill the original "
                        "purchasing recommendation."
                    ),
                    "recommended_quantity": original_quantity,
                    "supplier_available": supplier_available,
                }
            )
        else:
            passed_checks.append(
                "Supplier can fulfill the original recommendation."
            )

    # =========================================================
    # 5. PROP'S FINAL RECOMMENDATION
    # =========================================================

    recommended_cost = (
        recommended_quantity * unit_price
    )

    recommended_fits_budget = (
        recommended_cost <= purchasing_budget
    )

    recommended_fits_storage = (
        current_storage + recommended_quantity
        <= storage_capacity
    )

    recommended_fits_supplier = (
        recommended_quantity <= supplier_available
    )

    if recommended_quantity > 0:

        if recommended_fits_budget:
            passed_checks.append(
                "PROP's recommended quantity fits the purchasing budget."
            )
        else:
            challenges.append(
                {
                    "type": "FINAL_BUDGET_CONSTRAINT",
                    "severity": "HIGH",
                    "message": (
                        "PROP's final purchase quantity "
                        "exceeds the available purchasing budget."
                    ),
                    "recommended_quantity": recommended_quantity,
                    "estimated_cost_inr": recommended_cost,
                    "available_budget_inr": purchasing_budget,
                }
            )

        if recommended_fits_storage:
            passed_checks.append(
                "PROP's recommended quantity fits available storage."
            )
        else:
            challenges.append(
                {
                    "type": "FINAL_STORAGE_CONSTRAINT",
                    "severity": "HIGH",
                    "message": (
                        "PROP's final purchase quantity "
                        "exceeds available storage."
                    ),
                    "recommended_quantity": recommended_quantity,
                    "available_storage": available_storage,
                }
            )

        if recommended_fits_supplier:
            passed_checks.append(
                "Supplier can fulfill PROP's recommended quantity."
            )
        else:
            challenges.append(
                {
                    "type": "FINAL_SUPPLIER_CONSTRAINT",
                    "severity": "HIGH",
                    "message": (
                        "The supplier cannot fulfill PROP's "
                        "final purchase quantity."
                    ),
                    "recommended_quantity": recommended_quantity,
                    "supplier_available": supplier_available,
                }
            )

    # =========================================================
    # 6. MOQ CHECK
    # =========================================================

    if (
        recommended_quantity > 0
        and recommended_quantity < minimum_order_quantity
    ):
        challenges.append(
            {
                "type": "MOQ_CONSTRAINT",
                "severity": "HIGH",
                "message": (
                    "PROP's recommended quantity is below "
                    "the supplier minimum order quantity."
                ),
                "recommended_quantity": recommended_quantity,
                "minimum_order_quantity": minimum_order_quantity,
            }
        )

    elif recommended_quantity > 0:
        passed_checks.append(
            "Recommended quantity satisfies the supplier MOQ."
        )

    # =========================================================
    # 7. LEAD TIME CHECK
    # =========================================================

    if forecast_gap > 0 and lead_time_days > 7:
        warnings.append(
            {
                "type": "LEAD_TIME_RISK",
                "message": (
                    "Supplier lead time may create a "
                    "stock availability risk."
                ),
                "lead_time_days": lead_time_days,
            }
        )
    else:
        passed_checks.append(
            "Supplier lead time does not create a major risk."
        )

    # =========================================================
    # 8. DEMAND GAP
    # =========================================================

    if forecast_gap > 0:
        warnings.append(
            {
                "type": "FORECAST_GAP",
                "message": (
                    "Forecasted demand exceeds expected "
                    "inventory coverage."
                ),
                "forecast_gap": forecast_gap,
            }
        )

    if demand_signal == "INCREASING":
        warnings.append(
            {
                "type": "INCREASING_DEMAND",
                "message": (
                    "Demand is currently trending upward."
                ),
            }
        )

    # =========================================================
    # 9. DETERMINE BUSINESS DECISION
    # =========================================================

    original_recommendation_problem = (
        original_quantity > 0
        and (
            not original_fits_budget
            or not original_fits_storage
            or not original_fits_supplier
        )
    )

    final_quantity_feasible = (
        recommended_quantity > 0
        and recommended_fits_budget
        and recommended_fits_storage
        and recommended_fits_supplier
        and recommended_quantity >= minimum_order_quantity
    )

    if forecast_status == "stale":

        business_decision = "INVESTIGATE_FURTHER"

    elif recommended_quantity <= 0:

        business_decision = "REJECT"

    elif not final_quantity_feasible:

        business_decision = "INVESTIGATE_FURTHER"

    elif original_recommendation_problem:

        business_decision = "MODIFY"

    elif original_quantity == recommended_quantity:

        business_decision = "ACCEPT"

    else:

        business_decision = "MODIFY"

    # =========================================================
    # 10. CHALLENGE STATUS
    # =========================================================

    high_severity_count = sum(
        1
        for item in challenges
        if item["severity"] == "HIGH"
    )

    medium_severity_count = sum(
        1
        for item in challenges
        if item["severity"] == "MEDIUM"
    )

    if high_severity_count > 0:

        challenge_status = "BLOCKED"

    elif medium_severity_count > 0:

        challenge_status = "REVIEW"

    elif warnings or recommendation_issues:

        challenge_status = "CAUTION"

    else:

        challenge_status = "PASSED"

    # =========================================================
    # 11. CAN THE FINAL PROP RECOMMENDATION PROCEED?
    # =========================================================

    can_proceed = (
        business_decision
        in [
            "ACCEPT",
            "MODIFY",
        ]
        and final_quantity_feasible
        and challenge_status != "BLOCKED"
        and recommendation.get("action")
        == "CREATE_PURCHASE_ORDER"
    )

    # Human approval is still required for every executable
    # purchasing action.
    human_review_required = (
        can_proceed
        or business_decision == "INVESTIGATE_FURTHER"
    )

    # =========================================================
    # 12. CHALLENGE ID
    # =========================================================

    challenge_id = (
        "PROP-CHALLENGE-"
        + datetime.now().strftime(
            "%Y%m%d%H%M%S%f"
        )
    )

    # =========================================================
    # 13. RETURN COMPLETE CHALLENGE RESULT
    # =========================================================

    return {
        "challenge_id": challenge_id,

        "timestamp": datetime.now().isoformat(),

        "agent": {
            "name": "PROP Challenge Engine",
            "version": "3.0",
        },

        "decision_id": decision.get(
            "decision_id"
        ),

        "store_id": decision.get(
            "store_id"
        ),

        "product_id": decision.get(
            "product_id"
        ),

        "challenge_status": challenge_status,

        "can_proceed": can_proceed,

        "business_decision": business_decision,

        "summary": {
            "high_severity_issues": high_severity_count,

            "medium_severity_issues": medium_severity_count,

            "recommendation_issues": len(
                recommendation_issues
            ),

            "warnings": len(warnings),

            "passed_checks": len(passed_checks),
        },

        "challenges": challenges,

        "recommendation_issues": recommendation_issues,

        "warnings": warnings,

        "passed_checks": passed_checks,

        # -----------------------------------------------------
        # Keep the existing aura_* JSON keys for compatibility
        # with the current frontend and other backend services.
        # -----------------------------------------------------

        "recommendation_review": {
            "original_quantity": original_quantity,

            "original_cost_inr": original_cost,

            "original_fits_budget": (
                original_fits_budget
            ),

            "original_fits_storage": (
                original_fits_storage
            ),

            "original_fits_supplier": (
                original_fits_supplier
            ),

            "aura_quantity": recommended_quantity,

            "aura_cost_inr": recommended_cost,

            "aura_fits_budget": (
                recommended_fits_budget
            ),

            "aura_fits_storage": (
                recommended_fits_storage
            ),

            "aura_fits_supplier": (
                recommended_fits_supplier
            ),

            "modified": (
                original_quantity
                != recommended_quantity
            ),
        },

        "supplier_capacity_check": {
            "forecast_gap": forecast_gap,

            "supplier_available": (
                supplier_available
            ),

            "recommended_quantity": (
                recommended_quantity
            ),

            "supplier_can_cover_gap": (
                supplier_available
                >= forecast_gap
            ),

            "supplier_can_fulfill_recommendation": (
                recommended_fits_supplier
            ),
        },

        "constraint_check": {
            "budget": {
                "available_inr": (
                    purchasing_budget
                ),

                "original_cost_inr": (
                    original_cost
                ),

                "aura_cost_inr": (
                    recommended_cost
                ),

                "original_fits": (
                    original_fits_budget
                ),

                "aura_fits": (
                    recommended_fits_budget
                ),
            },

            "storage": {
                "capacity": (
                    storage_capacity
                ),

                "current_storage": (
                    current_storage
                ),

                "available_storage": (
                    available_storage
                ),

                "original_fits": (
                    original_fits_storage
                ),

                "aura_fits": (
                    recommended_fits_storage
                ),
            },
        },

        "challenge_decision": (
            f"PROP recommends "
            f"{business_decision.lower()}ing "
            f"the original purchasing recommendation."
        ),

        "original_recommendation": {
            "action": recommendation.get(
                "action"
            ),

            "quantity": original_quantity,
        },

        "human_review": {
            "required": human_review_required,

            "status": (
                "PENDING"
                if human_review_required
                else "READY"
            ),
        },
    }