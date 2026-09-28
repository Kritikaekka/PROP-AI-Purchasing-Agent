const API_BASE_URL = "http://127.0.0.1:8000";

const STORE_ID = "DEMO-DEL-01";
const PRODUCT_ID = "HIR-SHELTER-BB";

let currentDecisionId = null;
let investigationData = null;


/* =====================================================
   HELPERS
===================================================== */

function $(id) {
    return document.getElementById(id);
}


function formatINR(value) {

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {
        return "—";
    }

    return "₹" + Number(value).toLocaleString("en-IN");
}


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


function showMessage(text) {

    const message = $("message");

    if (!message) return;

    message.textContent = text;

    message.classList.add("show");

    setTimeout(() => {
        message.classList.remove("show");
    }, 3500);
}


/* =====================================================
   WORKFLOW
===================================================== */

function setWorkflow(stepIndex) {

    const steps =
        document.querySelectorAll(".workflow-step");

    steps.forEach((step, index) => {

        step.classList.remove("active");

        if (index === stepIndex) {
            step.classList.add("active");
        }

    });
}


/* =====================================================
   RESET
===================================================== */

function resetReviewUI() {

    currentDecisionId = null;
    investigationData = null;


    $("results").classList.remove(
        "visible"
    );


    $("approval-pending-state").style.display =
        "block";


    $("approval-rejected-state")
        .classList
        .remove("visible");


    $("approval-status-text").textContent =
        "PENDING APPROVAL";


    $("approve-btn").disabled = false;
    $("reject-btn").disabled = false;


    $("approve-btn").innerHTML =
        'Approve purchase <span>→</span>';


    $("reject-btn").textContent =
        "Reject";


    $("execution-status").textContent =
        "Waiting.";


    $("execution-content").textContent =
        "Purchase order will appear here after human approval.";


    $("validation-status").textContent =
        "Awaiting order.";


    $("validation-content").textContent =
        "PROP will validate the completed purchase.";


    setWorkflow(0);
}


/* =====================================================
   INVESTIGATE
===================================================== */

async function investigate() {

    const button =
        $("investigate-btn");

    const navButton =
        $("nav-review-btn");


    button.disabled = true;
    navButton.disabled = true;


    button.innerHTML =
        'Reviewing <span>...</span>';


    resetReviewUI();


    try {

        /*
         * STEP 01
         * REVIEW
         */

        setWorkflow(0);

        await sleep(350);


        /*
         * STEP 02
         * CHECK
         */

        setWorkflow(1);

        await sleep(350);


        const response =
            await fetch(
                `${API_BASE_URL}/agent/investigate/${STORE_ID}/${PRODUCT_ID}`
            );


        if (!response.ok) {

            throw new Error(
                `Backend returned ${response.status}`
            );
        }


        const data =
            await response.json();


        if (data.error) {

            throw new Error(
                data.error
            );
        }


        investigationData = data;

        currentDecisionId =
            data.decision_id;


        /*
         * STEP 03
         * RECOMMEND
         */

        setWorkflow(2);


        displayInvestigation(data);


        $("results")
            .classList
            .add("visible");


        showMessage(
            "Review complete. PROP has challenged the recommendation."
        );


        await sleep(300);


        $("results").scrollIntoView({
            behavior: "smooth",
            block: "start"
        });


    } catch (error) {

        console.error(error);

        showMessage(
            error.message
        );

    } finally {

        button.disabled = false;
        navButton.disabled = false;

        button.innerHTML =
            'Review purchase <span>→</span>';
    }
}


/* =====================================================
   DISPLAY INVESTIGATION
===================================================== */

function displayInvestigation(data) {

    const evidence =
        data.evidence || {};

    const analysis =
        data.analysis || {};

    const recommendation =
        data.recommendation || {};

    const challenge =
        data.challenge || {};

    const finalDecision =
        data.final_decision || {};


    /* =================================================
       EVIDENCE
    ================================================= */

    const inventory =
        evidence.inventory || {};

    const sales =
        evidence.sales || {};

    const forecast =
        evidence.forecast || {};

    const supplier =
        evidence.supplier || {};

    const constraints =
        evidence.store_constraints || {};


    $("inventory-value").textContent =
        inventory.available_quantity ?? "—";


    $("sales-value").textContent =
        sales.average_daily_sales ?? "—";


    $("forecast-value").textContent =
        forecast.trend_adjusted_forecast ?? "—";


    $("gap-value").textContent =
        analysis.forecast_gap ?? "—";


    $("supplier-value").textContent =
        supplier.available_quantity ?? "—";


    $("lead-time-value").textContent =
        supplier.lead_time_days ?? "—";


    $("budget-value").textContent =
        formatINR(
            constraints.purchasing_budget_inr
        );


    $("storage-value").textContent =
        constraints.available_storage ?? "—";


    /* =================================================
       ORIGINAL RECOMMENDATION
    ================================================= */

    const originalQuantity =
        recommendation.original_quantity ??
        analysis.original_recommendation?.quantity ??
        800;


    const originalCost =
        analysis.original_recommendation?.estimated_cost_inr ??
        originalQuantity *
        (supplier.unit_price || 0);


    $("original-quantity").textContent =
        originalQuantity;


    $("original-cost").textContent =
        formatINR(originalCost);


    /* =================================================
       PROP RECOMMENDATION
    ================================================= */

    const review =
        challenge.recommendation_review || {};


    const propQuantity =
        recommendation.quantity ??
        analysis.agent_recommendation?.quantity ??
        review.aura_quantity ??
        0;


    const propCost =
        recommendation.estimated_cost_inr ??
        analysis.agent_recommendation?.estimated_cost_inr ??
        review.aura_cost_inr ??
        0;


    $("prop-quantity").textContent =
        propQuantity;


    $("prop-cost").textContent =
        formatINR(propCost);


    /* =================================================
       CONSTRAINTS
    ================================================= */

    const originalFitsBudget =
        review.original_fits_budget ??
        analysis.original_recommendation?.fits_budget ??
        false;


    const originalFitsStorage =
        review.original_fits_storage ??
        analysis.original_recommendation?.fits_storage ??
        false;


    const originalFitsSupplier =
        review.original_fits_supplier ??
        false;


    const propFitsBudget =
        review.aura_fits_budget ??
        analysis.agent_recommendation?.fits_budget ??
        true;


    const propFitsStorage =
        review.aura_fits_storage ??
        analysis.agent_recommendation?.fits_storage ??
        true;


    const propFitsSupplier =
        review.aura_fits_supplier ??
        analysis.agent_recommendation?.fits_supplier_capacity ??
        true;


    $("original-constraint-list").innerHTML = `

        <div>
            ${originalFitsBudget ? "✓" : "×"}
            Budget
        </div>

        <div>
            ${originalFitsStorage ? "✓" : "×"}
            Storage
        </div>

        <div>
            ${originalFitsSupplier ? "✓" : "×"}
            Supplier
        </div>

    `;


    $("prop-constraint-list").innerHTML = `

        <div>
            ${propFitsBudget ? "✓" : "×"}
            Budget
        </div>

        <div>
            ${propFitsStorage ? "✓" : "×"}
            Storage
        </div>

        <div>
            ${propFitsSupplier ? "✓" : "×"}
            Supplier
        </div>

    `;


    const originalFeasible =
        originalFitsBudget &&
        originalFitsStorage &&
        originalFitsSupplier;


    const propFeasible =
        propFitsBudget &&
        propFitsStorage &&
        propFitsSupplier;


    $("original-constraint-status").textContent =
        originalFeasible
            ? "FEASIBLE"
            : "NOT FEASIBLE";


    $("original-constraint-status").className =
        "constraint-status " +
        (
            originalFeasible
                ? "pass"
                : "fail"
        );


    $("prop-constraint-status").textContent =
        propFeasible
            ? "FEASIBLE"
            : "REVIEW REQUIRED";


    $("prop-constraint-status").className =
        "constraint-status " +
        (
            propFeasible
                ? "pass"
                : "fail"
        );


    /* =================================================
       CHALLENGE FINDINGS
    ================================================= */

    const issues =
        challenge.recommendation_issues || [];

    const warnings =
        challenge.warnings || [];

    const challenges =
        challenge.challenges || [];


    const allFindings = [
        ...issues,
        ...challenges,
        ...warnings
    ];


    $("challenge-count").textContent =
        allFindings.length;


    $("challenge-status").textContent =
        challenge.challenge_status ||
        "CAUTION";


    const list =
        $("challenge-list");


    list.innerHTML = "";


    if (allFindings.length === 0) {

        list.innerHTML = `

            <div class="challenge-item">

                <div class="challenge-item-number">
                    01
                </div>

                <div class="challenge-item-icon">
                    ✓
                </div>

                <div class="challenge-item-text">
                    No blocking issues were found.
                </div>

            </div>

        `;

    } else {

        allFindings.forEach(
            (finding, index) => {

                const item =
                    document.createElement("div");


                item.className =
                    "challenge-item";


                const message =
                    finding.message ||
                    finding.type ||
                    "Review finding";


                item.innerHTML = `

                    <div class="challenge-item-number">
                        ${String(index + 1).padStart(2, "0")}
                    </div>

                    <div class="challenge-item-icon">
                        ${
                            finding.severity === "HIGH"
                                ? "!"
                                : "•"
                        }
                    </div>

                    <div class="challenge-item-text">
                        ${message}
                    </div>

                `;


                list.appendChild(item);
            }
        );
    }


    /* =================================================
       DECISION
    ================================================= */

    const businessDecision =
        finalDecision.business_decision ||
        challenge.business_decision ||
        "MODIFY";


    $("decision-status").textContent =
        businessDecision + ".";


    $("decision-original-quantity").textContent =
        finalDecision.original_quantity ??
        originalQuantity;


    $("decision-quantity").textContent =
        finalDecision.final_quantity ??
        propQuantity;


    $("decision-cost").textContent =
        formatINR(
            finalDecision.estimated_cost_inr ??
            propCost
        );


    $("decision-reason").textContent =
        finalDecision.reason ||
        "PROP modified the purchasing recommendation after considering demand, inventory, supplier capacity, budget and storage.";


    /* =================================================
       APPROVAL
    ================================================= */

    $("approval-pending-state").style.display =
        "block";


    $("approval-rejected-state")
        .classList
        .remove("visible");


    $("approval-status-text").textContent =
        "PENDING APPROVAL";


    $("approve-btn").disabled = false;
    $("reject-btn").disabled = false;


    /* =================================================
       EXECUTION
    ================================================= */

    $("execution-status").textContent =
        "Waiting.";


    $("execution-content").textContent =
        "Purchase order will appear here after human approval.";


    /* =================================================
       VALIDATION
    ================================================= */

    $("validation-status").textContent =
        "Awaiting order.";


    $("validation-content").textContent =
        "PROP will validate the completed purchase.";
}


/* =====================================================
   APPROVE
===================================================== */

async function approvePurchase() {

    if (!currentDecisionId) {

        showMessage(
            "No purchase decision is available."
        );

        return;
    }


    const approveButton =
        $("approve-btn");

    const rejectButton =
        $("reject-btn");


    approveButton.disabled = true;
    rejectButton.disabled = true;


    approveButton.innerHTML =
        "Approving...";


    $("approval-status-text").textContent =
        "APPROVING";


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/agent/approve/${currentDecisionId}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    }
                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            data.success === false
        ) {

            throw new Error(
                data.message ||
                data.detail ||
                "Approval failed."
            );
        }


        $("approval-status-text").textContent =
            "APPROVED";


        /*
         * APPROVE
         * ↓
         * ORDER
         */

        setWorkflow(4);


        showMessage(
            "Purchase approved. Creating the order."
        );


        await sleep(500);


        $("execution-panel").scrollIntoView({
            behavior: "smooth",
            block: "center"
        });


        await sleep(500);


        await executePurchase();


    } catch (error) {

        console.error(error);


        approveButton.disabled = false;
        rejectButton.disabled = false;


        approveButton.innerHTML =
            'Approve purchase <span>→</span>';


        $("approval-status-text").textContent =
            "PENDING APPROVAL";


        showMessage(
            error.message
        );
    }
}


/* =====================================================
   REJECT
===================================================== */

async function rejectPurchase() {

    if (!currentDecisionId) {

        showMessage(
            "No purchase decision is available."
        );

        return;
    }


    const approveButton =
        $("approve-btn");

    const rejectButton =
        $("reject-btn");


    approveButton.disabled = true;
    rejectButton.disabled = true;


    rejectButton.textContent =
        "Rejecting...";


    $("approval-status-text").textContent =
        "REJECTING";


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/agent/reject/${currentDecisionId}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        reason:
                            "Rejected by human reviewer."
                    })
                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            data.success === false
        ) {

            throw new Error(
                data.message ||
                data.detail ||
                "Rejection failed."
            );
        }


        /*
         * IMPORTANT:
         *
         * REJECTION IS TERMINAL.
         *
         * We DO NOT call:
         *
         * /execute
         *
         * /validate
         *
         * No PO is created.
         *
         * No inventory changes.
         *
         * No supplier changes.
         */


        $("approval-pending-state").style.display =
            "none";


        $("approval-rejected-state")
            .classList
            .add("visible");


        $("approval-status-text").textContent =
            "REJECTED";


        $("execution-status").textContent =
            "Not executed.";


        $("execution-content").textContent =
            "The purchase was rejected before execution. No purchase order was created.";


        $("validation-status").textContent =
            "Not required.";


        $("validation-content").textContent =
            "Validation was skipped because no purchase was executed.";


        /*
         * Keep the workflow at APPROVE.
         */

        setWorkflow(3);


        showMessage(
            "Purchase rejected. Nothing was executed."
        );


        await sleep(400);


        $("approval-panel").scrollIntoView({
            behavior: "smooth",
            block: "center"
        });


    } catch (error) {

        console.error(error);


        approveButton.disabled = false;
        rejectButton.disabled = false;


        rejectButton.textContent =
            "Reject";


        $("approval-status-text").textContent =
            "PENDING APPROVAL";


        showMessage(
            error.message
        );
    }
}


/* =====================================================
   REVIEW AGAIN
===================================================== */

async function reviewAgain() {

    resetReviewUI();


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });


    await sleep(500);


    showMessage(
        "Ready for a new purchase review."
    );
}


/* =====================================================
   EXECUTE
===================================================== */

async function executePurchase() {

    if (!currentDecisionId) {
        return;
    }


    $("execution-status").textContent =
        "Creating order...";


    $("execution-content").innerHTML = `
        PROP is creating the approved
        purchase order.
    `;


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/agent/execute/${currentDecisionId}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    }
                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            data.success === false
        ) {

            throw new Error(
                data.message ||
                data.detail ||
                "Execution failed."
            );
        }


        $("execution-status").textContent =
            "Order created.";


        const execution =
            data.execution || data;


        const purchaseOrderId =
            execution.purchase_order_id ||
            execution.po_id ||
            data.purchase_order_id ||
            "Purchase order created";


        $("execution-content").innerHTML = `

            <strong>
                ${purchaseOrderId}
            </strong>

            <br><br>

            The approved purchase order has
            been created successfully.

        `;


        /*
         * ORDER
         * ↓
         * VERIFY
         */

        setWorkflow(5);


        showMessage(
            "Purchase order created."
        );


        await sleep(700);


        $("validation-panel").scrollIntoView({
            behavior: "smooth",
            block: "center"
        });


        await sleep(500);


        await validatePurchase();


    } catch (error) {

        console.error(error);


        $("execution-status").textContent =
            "Execution failed.";


        $("execution-content").textContent =
            error.message;


        showMessage(
            error.message
        );
    }
}


/* =====================================================
   VALIDATE
===================================================== */

async function validatePurchase() {

    if (!currentDecisionId) {
        return;
    }


    $("validation-status").textContent =
        "Checking...";


    $("validation-content").innerHTML = `
        PROP is verifying the purchase,
        inventory and supplier state.
    `;


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/agent/validate/${currentDecisionId}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    }
                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            data.success === false
        ) {

            throw new Error(
                data.message ||
                data.detail ||
                "Validation failed."
            );
        }


        $("validation-status").textContent =
            "Verified.";


        $("validation-content").innerHTML = `

            <strong>
                Purchase validated successfully.
            </strong>

            <br><br>

            The purchase order exists,
            execution completed,
            inventory was updated,
            and supplier stock was adjusted.

        `;


        showMessage(
            "Purchase successfully validated."
        );


    } catch (error) {

        console.error(error);


        $("validation-status").textContent =
            "Validation failed.";


        $("validation-content").textContent =
            error.message;


        showMessage(
            error.message
        );
    }
}


/* =====================================================
   EVENTS
===================================================== */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        $("investigate-btn")
            .addEventListener(
                "click",
                investigate
            );


        $("nav-review-btn")
            .addEventListener(
                "click",
                investigate
            );


        $("approve-btn")
            .addEventListener(
                "click",
                approvePurchase
            );


        $("reject-btn")
            .addEventListener(
                "click",
                rejectPurchase
            );


        $("review-again-btn")
            .addEventListener(
                "click",
                reviewAgain
            );


        resetReviewUI();

    }
);