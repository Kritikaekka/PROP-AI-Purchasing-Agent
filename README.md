# AURA — AI Purchasing Agent

AURA is an AI-assisted purchasing decision system designed to investigate
inventory and demand conditions, challenge the recommendation for safety,
request human approval, execute a purchase order, and validate the outcome.

The system demonstrates an end-to-end purchasing workflow:

INVESTIGATE → CHALLENGE → DECIDE → HUMAN APPROVAL → EXECUTE → VALIDATE


## 1. Problem

A purchasing system should not blindly create purchase orders whenever
inventory is low.

AURA evaluates multiple signals before taking action:

- Current inventory
- Reserved inventory
- Historical sales
- Average daily demand
- Demand forecast
- Open purchase orders
- Supplier availability
- Minimum order quantity
- Supplier lead time
- Unit price

The system then challenges the recommendation before execution.

A human approval step is required before a purchase order can be created.


## 2. Solution

AURA separates the purchasing workflow into six stages.

### 1. Investigate

Collects evidence from the database:

- Inventory
- Sales history
- Forecast
- Open purchase orders
- Supplier information

The investigation engine calculates:

- Average daily sales
- Forecast gap
- Demand signal
- Inventory risk
- Recommended purchase quantity
- Estimated purchase cost


### 2. Challenge

The Challenge Engine independently checks the investigation.

It checks for conditions such as:

- Stale forecasts
- Forecast inconsistencies
- Invalid inventory
- Invalid reserved inventory
- Existing open purchase orders
- Supplier shortages
- Forecast gaps
- MOQ constraints
- Lead-time concerns

The challenge result can block or caution a purchasing decision.


### 3. Decide

The Decision Stage converts the investigation and challenge results
into a final purchasing action.

Possible outcomes include:

- CREATE_PURCHASE_ORDER
- NO_PURCHASE
- REVIEW_FORECAST
- SUPPLIER_SHORTAGE
- REVIEW


### 4. Human Approval

AURA does not execute a purchase automatically.

A human reviewer must explicitly approve an executable purchase decision.

This creates a human-in-the-loop control before financial action.


### 5. Execute

After approval, the Execution Engine:

1. Creates a purchase order
2. Records the decision ID
3. Records supplier and product information
4. Records quantity and price
5. Updates store inventory
6. Updates supplier inventory


### 6. Validate

The Validation Engine verifies that execution actually produced
the expected state.

It checks:

- Purchase order exists
- Purchase order status is correct
- Execution record exists
- Store inventory was updated correctly
- Supplier inventory was updated correctly


## 3. Demo Scenario

The working demonstration uses:

**Store**

AURA Demo Delhi Store

**Store ID**

`DEMO-DEL-01`

**Product**

Hirono Shelter Series Blind Box

**Product ID**

`HIR-SHELTER-BB`

**Supplier**

`SUP-001`


### Demo inputs

The scenario contains:

| Signal | Value |
|---|---:|
| Store inventory | 10 units |
| Reserved inventory | 0 units |
| Sales observed | 70 units / 7 days |
| Average daily sales | 10 units/day |
| 7-day forecast | 60 units |
| Forecast gap | 50 units |
| Supplier inventory | 100 units |
| Lead time | 4 days |
| Unit price | ₹1,800 |
| Open purchase orders | 0 |


### AURA decision

AURA determines that additional inventory is required.

Recommended purchase:

**50 units**

Estimated cost:

**₹90,000**


The Challenge Engine identifies a forecast-gap warning but does not
block the purchase because the supplier can cover the required quantity.

The system therefore waits for human approval.


## 4. Successful Execution

After human approval, AURA creates a purchase order.

Example result:

- Quantity: 50 units
- Unit price: ₹1,800
- Total cost: ₹90,000
- Purchase order status: `CREATED`

The store inventory increases from:

`10 → 60`

The supplier inventory decreases from:

`100 → 50`


## 5. Validation Result

The final validation verifies all execution conditions.

The successful demo passed:

- `PURCHASE_ORDER_EXISTS`
- `PURCHASE_ORDER_STATUS`
- `EXECUTION_RECORD`
- `STORE_INVENTORY_UPDATED`
- `SUPPLIER_INVENTORY_UPDATED`

Final validation status:

**PASSED**


## 6. Safety Scenario

AURA also supports a blocked purchasing scenario.

For example, if a forecast is stale, the Challenge Engine can block
execution and require human review rather than allowing an unsafe
automatic purchase.

This demonstrates that AURA is not only an execution system; it also
contains a decision-challenge layer intended to catch problematic
recommendations before financial action.


## 7. Architecture

```text
                    ┌─────────────────────┐
                    │      Frontend       │
                    │ HTML / CSS / JS     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      FastAPI        │
                    │      REST API       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Investigation Engine │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Challenge Engine   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Decision Stage    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Human Approval     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Execution Engine   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Validation Engine   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    MongoDB Atlas    │
                    └─────────────────────┘