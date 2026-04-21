"""CloudPayments integration — Checkout links + status checks."""

import base64
import aiohttp
from app.config import config

CHECKOUT_URL = "https://checkout.cloudpayments.ru"
API_URL = "https://api.cloudpayments.ru"


def _auth_header() -> str:
    """Basic Auth header for CloudPayments API."""
    creds = f"{config.CLOUDPAYMENTS_PUBLIC_ID}:{config.CLOUDPAYMENTS_API_SECRET}"
    return "Basic " + base64.b64encode(creds.encode()).decode()


def create_payment_url(invoice_id: str, amount: int, description: str, email: str = "") -> str:
    """Generate CloudPayments checkout URL."""
    params = {
        "publicId": config.CLOUDPAYMENTS_PUBLIC_ID,
        "amount": amount,
        "currency": "RUB",
        "invoiceId": invoice_id,
        "description": description,
        "accountId": email,
        "skin": "modern",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items() if v)
    return f"{CHECKOUT_URL}/?{query}"


async def check_payment(invoice_id: str) -> dict | None:
    """Check payment status by invoice ID."""
    if not config.CLOUDPAYMENTS_PUBLIC_ID or not config.CLOUDPAYMENTS_API_SECRET:
        return None
    
    headers = {
        "Authorization": _auth_header(),
        "Content-Type": "application/json",
    }
    payload = {"InvoiceId": invoice_id}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/v2/payments/find", headers=headers, json=payload) as resp:
            if resp.status != 200:
                return None
            return await resp.json()


async def get_payment_status(invoice_id: str) -> str:
    """Simplified status check: returns 'completed', 'pending', 'failed', or 'unknown'."""
    data = await check_payment(invoice_id)
    if not data or not data.get("Success"):
        return "unknown"
    
    model = data.get("Model", {})
    status = model.get("Status", "")
    
    if status in ("Completed", "Authorized"):
        return "completed"
    if status in ("Declined", "Cancelled"):
        return "failed"
    return "pending"


def process_webhook(data: dict) -> dict:
    """Process incoming CloudPayments webhook.
    
    Expected fields:
    - TransactionId
    - Amount
    - Currency
    - Status (Completed, Declined, etc.)
    - InvoiceId
    - AccountId
    - Data (optional JSON string)
    """
    return {
        "transaction_id": data.get("TransactionId"),
        "invoice_id": data.get("InvoiceId"),
        "amount": data.get("Amount"),
        "currency": data.get("Currency"),
        "status": data.get("Status"),
        "account_id": data.get("AccountId"),
        "success": data.get("Status") == "Completed",
    }
