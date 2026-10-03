# Copyright (c) 2026, Bipin Kole and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": _("Payment Entry"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Payment Entries",
            "width": 180,
        },
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("Payment Type"),
            "fieldname": "payment_type",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Party Type"),
            "fieldname": "party_type",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Party"),
            "fieldname": "party",
            "fieldtype": "Link",
            "options": "Party",
            "width": 180,
        },
        {
            "label": _("Account Paid From"),
            "fieldname": "account_paid_from",
            "fieldtype": "Link",
            "options": "Account",
            "width": 180,
        },
        {
            "label": _("Account Paid To"),
            "fieldname": "account_paid_to",
            "fieldtype": "Link",
            "options": "Account",
            "width": 180,
        },
        {
            "label": _("Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 120,
        },
    ]


def get_data(filters):
    filter_dict = {}

    if filters.get("name"):
        filter_dict["name"] = filters.get("name")

    return frappe.get_all(
        "Payment Entries",
        filters=filter_dict,
        fields=[
            "name",
            "posting_date",
            "payment_type",
            "party_type",
            "party",
            "account_paid_from",
            "account_paid_to",
            "amount",
        ],
        order_by="posting_date desc",
    )