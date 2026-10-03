
import frappe
from frappe import _


def execute(filters: dict | None = None):
    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data


def get_columns(filters):
    return [
        {
            "label": _("Sales Invoice"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Sales Invoices",
            "width": 200
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Party",
            "width": 200
        },
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 150
        },
        {
            "label": _("Posting Due Date"),
            "fieldname": "posting_due_date",
            "fieldtype": "Date",
            "width": 150
        },
        {
            "label": _("Item"),
            "fieldname": "item",
            "fieldtype": "Data",
            "width":100
        },
        {
            "label": _("Qty"),
            "fieldname": "qty",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Rate"),
            "fieldname": "rate",
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "label": _("Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 100
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
            "width": 100,
        },
         {
            "label": ("Debit To"),
            "fieldname": "debit_to",
            "fieldtype": "Link",
            "options": "Acount",
            "width": 150,
        },
        {
            "label": ("Income Account"),
            "fieldname": "income_account",
            "fieldtype": "Link",
            "options": "Acount",
            "width": 150,
        },		
    ]


def get_data(filters):
    data = []

    invoices = frappe.get_all(
        "Sales Invoices",
        fields=[
            "name",
            "customer",
            "posting_date",
            "posting_due_date",
            "total_qty",
            "total_amount",
            "debit_to",
            "income_account"			
        ]
    )

    for invoice in invoices:

        items = frappe.get_all(
            "Sales Invoice Items",
            filters={
                "parent": invoice.name
            },
            fields=[
                "item",
                "qty",
                "rate",
                "amount"
            ]
        )

        for item in items:
            data.append({
                "name": invoice.name,
                "customer": invoice.customer,
                "posting_date": invoice.posting_date,
                "posting_due_date": invoice.posting_due_date,
                "item": item.item,
                "qty": item.qty,
                "rate": item.rate,
                "amount": item.amount,
                "total_qty": invoice.total_qty,
                "total_amount": invoice.total_amount,
                "debit_to": invoice.debit_to,
                "income_account": invoice.income_account, 				
            })

    return data