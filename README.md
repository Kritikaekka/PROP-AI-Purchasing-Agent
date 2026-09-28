# PROP — AI Purchasing Agent

PROP is a purchasing assistant that reviews an existing purchase recommendation, checks it against current business data and constraints, and proposes an action.

The system does not directly place an order from the original recommendation. It first investigates the available data, checks the recommendation, makes an independent decision, asks for human approval, and validates the result after execution.

## How It Works

The main flow is:

**Review → Check → Recommend → Approve → Order → Verify**

1. The user submits an existing purchase recommendation.
2. PROP collects the relevant inventory, sales, forecast, supplier and business-rule data.
3. The original recommendation is checked against the available constraints.
4. PROP calculates its own required quantity.
5. The system produces a decision:
   - ACCEPT
   - MODIFY
   - REJECT
   - INVESTIGATE FURTHER
6. A human must approve the final purchase before execution.
7. The purchase order is created and the relevant records are updated.
8. The validation step checks whether the expected changes actually happened.

## Example

The included demo starts with an original recommendation of **800 units**.

PROP finds:

| Check | Value |
|---|---:|
| Current inventory | 10 |
| 7-day sales | 70 |
| Average daily sales | 10 |
| Forecast | 60 |
| Forecast gap | 50 |
| Supplier stock | 100 |
| MOQ | 12 |
| Budget | ₹1,00,000 |
| Storage capacity | 100 |
| Unit price | ₹1,800 |

The original 800-unit recommendation would cost ₹14,40,000 and does not fit the available budget or storage.

PROP independently calculates a requirement of **50 units**.

The resulting decision is:

- Original recommendation: 800
- PROP recommendation: 50
- Decision: MODIFY
- Cost: ₹90,000
- Human approval: Required

After approval, the system creates the purchase order and updates inventory and supplier stock.

The validation step then checks the expected changes.

## Architecture

![PROP System Architecture](docs/architecture.png)

### Main Components

**Frontend**

The frontend is a small web application built with HTML, CSS and JavaScript. It is used to submit recommendations, view the analysis, approve or reject the decision, and see the execution and validation results.

**Backend**

The backend is built with FastAPI.

The main processing stages are:

- Investigation Engine
- Challenge Engine
- Decision Stage
- Approval Engine
- Execution Engine
- Validation Engine

**Database**

MongoDB Atlas stores the inventory, sales, forecasts, supplier information, purchase orders and execution records.

## Project Structure

```text
PROP-AI-Purchasing-Agent/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── seed_data.py
│   ├── demo_scenario.py
│   ├── requirements.txt
│   │
│   └── services/
│       ├── decision_engine.py
│       ├── challenge_engine.py
│       ├── decision_stage.py
│       ├── approval_engine.py
│       ├── execution_engine.py
│       └── validation_engine.py
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── docs/
│   └── architecture.png
│
├── .gitignore
├── README.md
└── ...