from fastapi import FastAPI, HTTPException, Header
from typing import Optional
from datetime import datetime

app = FastAPI(title="DueFlow API")

API_KEY = "dueflow_demo_key"

customers = [
    {
        "customer_id": "CUS-101",
        "name": "Ravi Kumar",
        "phone": "9876543210",
        "merchant_id": "MER-501"
    },
    {
        "customer_id": "CUS-102",
        "name": "Suresh Kumar",
        "phone": "9876543211",
        "merchant_id": "MER-501"
    }
]

debts = [
    {
        "debt_id": "DEBT-9001",
        "customer_id": "CUS-101",
        "merchant_id": "MER-501",
        "customer_name": "Ravi Kumar",
        "original_amount": 1500,
        "paid_amount": 0,
        "outstanding_amount": 1500,
        "status": "OPEN",
        "category": "BUSINESS",
        "created_at": "2026-09-01T10:00:00+05:30"
    }
]

payments = []
messages = []
approvals = []


def check_key(x_api_key: Optional[str]):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/")
def root():
    return {"service": "DueFlow API", "status": "ok"}


@app.get("/customers/lookup")
def customer_lookup(
    name: Optional[str] = None,
    customer_id: Optional[str] = None,
    x_api_key: Optional[str] = Header(None)
):
    check_key(x_api_key)

    results = customers

    if customer_id:
        results = [c for c in results if c["customer_id"] == customer_id]

    if name:
        results = [
            c for c in results
            if name.lower() in c["name"].lower()
        ]

    return {"customers": results}


@app.post("/debts/create")
def create_debt(payload: dict, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)

    debt_id = f"DEBT-{9000 + len(debts) + 1}"

    debt = {
        "debt_id": debt_id,
        "customer_id": payload["customer_id"],
        "merchant_id": payload["merchant_id"],
        "customer_name": payload.get("customer_name"),
        "original_amount": payload["amount"],
        "paid_amount": 0,
        "outstanding_amount": payload["amount"],
        "status": "OPEN",
        "category": payload.get("category", "BUSINESS"),
        "reason": payload.get("reason", ""),
        "created_at": datetime.now().isoformat()
    }

    debts.append(debt)
    return debt


@app.get("/debts")
def list_debts(
    merchant_id: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    x_api_key: Optional[str] = Header(None)
):
    check_key(x_api_key)

    results = debts

    if merchant_id:
        results = [d for d in results if d["merchant_id"] == merchant_id]

    if status:
        results = [d for d in results if d["status"] == status]

    if category:
        results = [d for d in results if d["category"] == category]

    return {"debts": results}


@app.post("/payments")
def receive_payment(payload: dict, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)

    payment = {
        "payment_id": payload["payment_id"],
        "customer_id": payload["customer_id"],
        "merchant_id": payload["merchant_id"],
        "amount": payload["amount"],
        "timestamp": payload.get("timestamp", datetime.now().isoformat()),
        "status": "RECEIVED"
    }

    payments.append(payment)
    return payment


@app.post("/payments/reconcile")
def reconcile_payment(payload: dict, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)

    debt_id = payload["debt_id"]
    payment_id = payload["payment_id"]
    amount = payload["amount"]

    debt = next((d for d in debts if d["debt_id"] == debt_id), None)

    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")

    if amount > debt["outstanding_amount"]:
        raise HTTPException(
            status_code=400,
            detail="Payment exceeds outstanding amount"
        )

    debt["paid_amount"] += amount
    debt["outstanding_amount"] -= amount

    if debt["outstanding_amount"] == 0:
        debt["status"] = "SETTLED"
    else:
        debt["status"] = "PARTIALLY_PAID"

    return {
        "debt_id": debt_id,
        "payment_id": payment_id,
        "payment_applied": amount,
        "paid_amount": debt["paid_amount"],
        "outstanding_amount": debt["outstanding_amount"],
        "status": debt["status"]
    }


@app.post("/merchant/approval")
def merchant_approval(payload: dict, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)

    approval = {
        "approval_id": f"APR-{len(approvals) + 1}",
        "status": payload.get("status", "PENDING"),
        "action": payload.get("action"),
        "reason": payload.get("reason")
    }

    approvals.append(approval)
    return approval


@app.post("/messages/send")
def send_message(payload: dict, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)

    message = {
        "message_id": f"MSG-{len(messages) + 1}",
        "customer_id": payload["customer_id"],
        "message": payload["message"],
        "status": "SENT"
    }

    messages.append(message)
    return message


@app.get("/customer/dues")
def customer_dues(
    customer_id: str,
    x_api_key: Optional[str] = Header(None)
):
    check_key(x_api_key)

    customer_debts = [
        d for d in debts
        if d["customer_id"] == customer_id
        and d["outstanding_amount"] > 0
    ]

    return {
        "customer_id": customer_id,
        "dues": customer_debts,
        "total_outstanding": sum(
            d["outstanding_amount"] for d in customer_debts
        )
    }