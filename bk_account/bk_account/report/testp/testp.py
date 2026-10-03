# Copyright (c) 2026, Bipin Kole and contributors

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": ("Purchase Invoice"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Purchase Invoices",
            "width": 200,
        },
        {
            "label": ("Supplier"),
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Party",
            "width": 150,
        },
        {
            "label": ("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
        },
        {
            "label": ("Payment Due Date"),
            "fieldname": "payment_due_date",
            "fieldtype": "Date",
        },
        {
            "label": ("Items"),
            "fieldname": "items",
            "fieldtype": "Link",
            "options": "Items",
            "width": 100,
        },
        {
            "label": ("Qty"),
            "fieldname": "qty",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": ("Rate"),
            "fieldname": "rate",
            "fieldtype": "Currency",
            "width": 100,
        },
        {
            "label": ("Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 100,
        },
        {
            "label": ("Total Qty"),
            "fieldname": "total_qty",
            "fieldtype": "float",
            "width": 100,
        },
        {
            "label": ("Total Amount"),
            "fieldname": "total_amount",
            "fieldtype": "Currency",
            "width": 150,
        },
         {
            "label": ("Credit To"),
            "fieldname": "credit_to",
            "fieldtype": "Link",
            "options": "Acount",
            "width": 150,
        },
        {
            "label": ("Expense Account"),
            "fieldname": "expense_account",
            "fieldtype": "Link",
            "options": "Acount",
            "width": 150,
        },
    ]


def get_data(filters=None):
    data = []

    conditions = {}

    if filters and filters.get("name"):
        conditions["name"] = filters.get("name")

    invoices = frappe.get_all(
        "Purchase Invoices",
        filters=conditions,
        fields=[
            "name",
            "supplier",
            "posting_date",
            "payment_due_date",
            "total_qty",
            "total_amount",
            "credit_to",
            "expense_account"
        ],
    )

    for invoice in invoices:

        child_items = frappe.get_all("Purchase Invoice items", filters={"parent": invoice.name},fields=["items","qty","rate","amount"])
        if child_items:
            for item in child_items:
                data.append(  
                    {
                        "name": invoice.name,
                        "supplier": invoice.supplier,
                        "posting_date": invoice.posting_date,
                        "payment_due_date": invoice.payment_due_date,
                        "items": item.get("items"),
                        "qty": item.get("qty"),
                        "rate": item.get("rate"),
                        "amount": item.get("amount"),
                        "total_qty": invoice.total_qty,
                        "total_amount": invoice.total_amount,
                        "credit_to": invoice.credit_to,
                        "expense_account": invoice.expense_account,  
                    }
                )
    return data