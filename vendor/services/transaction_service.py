from datetime import datetime
from typing import List, Optional, Tuple
from odmantic import AIOEngine
from bson import ObjectId
from fastapi import HTTPException, status
import logging

from vendor.models.transaction import Transaction
from vendor.models.invoice import Invoice
from vendor.schemas.transaction import TransactionCreateRequest, TransactionUpdateRequest
from core.enums import TransactionStatus, InvoiceStatus

logger = logging.getLogger(__name__)


async def sync_invoice_paid_amount(engine: AIOEngine, vendor_id: str, invoice_id: str):
    """
    Recalculate total paid amount for an invoice based on all 'paid' transactions
    """
    transactions = await engine.find(
        Transaction,
        (Transaction.invoice_id == invoice_id) & 
        (Transaction.vendor_id == vendor_id) & 
        (Transaction.status == TransactionStatus.PAID)
    )
    
    total_paid = sum(t.amount for t in transactions)
    
    invoice = await engine.find_one(
        Invoice,
        (Invoice.id == ObjectId(invoice_id)) & (Invoice.vendor_id == vendor_id)
    )
    
    if invoice:
        invoice.paid_amount = total_paid
        invoice.balance_due = max(0.0, invoice.grand_total - total_paid)
        
        # Auto-update status
        if invoice.balance_due == 0:
            invoice.status = InvoiceStatus.PAID
        elif total_paid > 0:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
            
        invoice.updated_at = datetime.utcnow()
        await engine.save(invoice)
        logger.info(f"🔄 Synced invoice {invoice_id}: Paid={total_paid}, Balance={invoice.balance_due}")


async def create_transaction(engine: AIOEngine, vendor_id: str, payload: TransactionCreateRequest) -> Transaction:
    """Create a new transaction"""
    transaction = Transaction(
        vendor_id=vendor_id,
        invoice_id=payload.invoice_id,
        booking_id=payload.booking_id,
        customer_id=payload.customer_id,
        amount=payload.amount,
        status=payload.status,
        payment_method=payload.payment_method,
        payment_reference=payload.payment_reference,
        notes=payload.notes,
        date=payload.date if payload.date else datetime.utcnow().strftime("%Y-%m-%d"),
        time=payload.time if payload.time else datetime.utcnow().strftime("%H:%M:%S")
    )
    
    await engine.save(transaction)
    
    if transaction.status == TransactionStatus.PAID:
        await sync_invoice_paid_amount(engine, vendor_id, payload.invoice_id)
        
    logger.info(f"💰 Transaction created for invoice {payload.invoice_id}: {payload.amount}")
    return transaction


async def update_transaction(
    engine: AIOEngine, 
    vendor_id: str, 
    transaction_id: str, 
    payload: TransactionUpdateRequest
) -> Transaction:
    """Update transaction status or amount and sync invoice if needed"""
    try:
        transaction = await engine.find_one(
            Transaction,
            (Transaction.id == ObjectId(transaction_id)) & (Transaction.vendor_id == vendor_id)
        )
    except Exception:
        transaction = None
        
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    old_status = transaction.status
    old_amount = transaction.amount
    
    if payload.status:
        transaction.status = payload.status
    if payload.amount is not None:
        transaction.amount = payload.amount
        
    transaction.updated_at = datetime.utcnow()
    await engine.save(transaction)
    
    # Sync if status changed to/from 'paid' or if amount changed while 'paid'
    if (transaction.status != old_status or transaction.amount != old_amount) and \
       (transaction.status == TransactionStatus.PAID or old_status == TransactionStatus.PAID):
        await sync_invoice_paid_amount(engine, vendor_id, transaction.invoice_id)
        
    return transaction


async def list_transactions(
    engine: AIOEngine,
    vendor_id: str,
    invoice_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    status: Optional[TransactionStatus] = None,
    skip: int = 0,
    limit: int = 50
) -> Tuple[List[Transaction], int]:
    """List transactions with filters"""
    query = [Transaction.vendor_id == vendor_id]
    
    if invoice_id:
        query.append(Transaction.invoice_id == invoice_id)
    if customer_id:
        query.append(Transaction.customer_id == customer_id)
    if status:
        query.append(Transaction.status == status)
        
    transactions = await engine.find(
        Transaction,
        *query,
        sort=Transaction.created_at.desc(),
        skip=skip,
        limit=limit
    )
    total = await engine.count(Transaction, *query)
    
    return transactions, total


async def delete_transaction(engine: AIOEngine, vendor_id: str, transaction_id: str) -> bool:
    """Hard delete a transaction and sync invoice if it was 'paid'"""
    try:
        transaction = await engine.find_one(
            Transaction,
            (Transaction.id == ObjectId(transaction_id)) & (Transaction.vendor_id == vendor_id)
        )
    except Exception:
        transaction = None
        
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    invoice_id = transaction.invoice_id
    was_paid = transaction.status == TransactionStatus.PAID
    
    await engine.delete(transaction)
    
    if was_paid:
        await sync_invoice_paid_amount(engine, vendor_id, invoice_id)
        
    return True
