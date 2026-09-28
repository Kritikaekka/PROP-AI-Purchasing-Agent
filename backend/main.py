from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import (
    products_collection,
    stores_collection,
    inventory_collection,
    sales_collection,
    forecasts_collection,
    suppliers_collection,
    decisions_collection,
)

from services.decision_engine import investigate_purchase
from services.challenge_engine import challenge_investigation
from services.decision_stage import make_final_decision
from services.approval_engine import approve_decision, reject_decision
from services.execution_engine import execute_purchase
from services.validation_engine import validate_execution


app = FastAPI(
    title="PROP Purchasing Agent API",
    description="AI-assisted purchasing decision and validation system",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "PROP Purchasing Agent API is running",
        "version": "2.0.0",
    }


@app.get("/products/{product_id}", tags=["Data"])
def get_product(product_id: str):
    product = products_collection.find_one(
        {"product_id": product_id},
        {"_id": 0},
    )

    if not product:
        return {
            "error": "Product not found",
            "product_id": product_id,
        }

    return product


@app.get("/stores/{store_id}", tags=["Data"])
def get_store(store_id: str):
    store = stores_collection.find_one(
        {"store_id": store_id},
        {"_id": 0},
    )

    if not store:
        return {
            "error": "Store not found",
            "store_id": store_id,
        }

    return store


@app.get(
    "/inventory/{store_id}/{product_id}",
    tags=["Data"],
)
def get_inventory(
    store_id: str,
    product_id: str,
):
    inventory = inventory_collection.find_one(
        {
            "store_id": store_id,
            "product_id": product_id,
        },
        {"_id": 0},
    )

    if not inventory:
        return {
            "error": "Inventory not found",
            "store_id": store_id,
            "product_id": product_id,
        }

    return inventory


@app.get(
    "/sales/{store_id}/{product_id}",
    tags=["Data"],
)
def get_sales_history(
    store_id: str,
    product_id: str,
):
    sales = list(
        sales_collection.find(
            {
                "store_id": store_id,
                "product_id": product_id,
            },
            {"_id": 0},
        ).sort("date", 1)
    )

    return {
        "store_id": store_id,
        "product_id": product_id,
        "sales": sales,
    }


@app.get(
    "/forecast/{store_id}/{product_id}",
    tags=["Data"],
)
def get_forecast(
    store_id: str,
    product_id: str,
):
    forecast = forecasts_collection.find_one(
        {
            "store_id": store_id,
            "product_id": product_id,
        },
        {"_id": 0},
    )

    if not forecast:
        return {
            "error": "Forecast not found",
            "store_id": store_id,
            "product_id": product_id,
        }

    return forecast


@app.get(
    "/supplier/{supplier_id}",
    tags=["Data"],
)
def get_supplier(supplier_id: str):
    supplier = suppliers_collection.find_one(
        {"supplier_id": supplier_id},
        {"_id": 0},
    )

    if not supplier:
        return {
            "error": "Supplier not found",
            "supplier_id": supplier_id,
        }

    return supplier


@app.get(
    "/agent/investigate/{store_id}/{product_id}",
    tags=["PROP Agent"],
)
def investigate_agent(
    store_id: str,
    product_id: str,
):
    # ---------------------------------------------------------
    # 1. INVESTIGATE
    # ---------------------------------------------------------

    investigation = investigate_purchase(
        store_id=store_id,
        product_id=product_id,
    )

    # ---------------------------------------------------------
    # 2. CHALLENGE
    # ---------------------------------------------------------

    challenge = challenge_investigation(
        investigation
    )

    # ---------------------------------------------------------
    # 3. DECIDE
    # ---------------------------------------------------------

    final_decision = make_final_decision(
        investigation=investigation,
        challenge=challenge,
    )

    # ---------------------------------------------------------
    # 4. SAVE COMPLETE DECISION
    # ---------------------------------------------------------

    decisions_collection.update_one(
        {
            "decision_id": investigation.get(
                "decision_id"
            )
        },
        {
            "$set": {
                "challenge": challenge,
                "final_decision": final_decision,
            }
        },
    )

    # Include all stages in the API response.
    investigation["challenge"] = challenge
    investigation["final_decision"] = final_decision

    return investigation


@app.post(
    "/agent/approve/{decision_id}",
    tags=["Human Approval"],
)
def approve_agent_decision(
    decision_id: str,
):
    return approve_decision(
        decision_id=decision_id
    )


@app.post(
    "/agent/reject/{decision_id}",
    tags=["Human Approval"],
)
def reject_agent_decision(
    decision_id: str,
):
    return reject_decision(
        decision_id=decision_id
    )


@app.post(
    "/agent/execute/{decision_id}",
    tags=["Execution"],
)
def execute_agent_purchase(
    decision_id: str,
):
    return execute_purchase(
        decision_id=decision_id
    )


@app.post(
    "/agent/validate/{decision_id}",
    tags=["Validation"],
)
def validate_agent_execution(
    decision_id: str,
):
    return validate_execution(
        decision_id=decision_id
    )