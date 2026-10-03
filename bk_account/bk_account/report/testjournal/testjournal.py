# Copyright (c) 2026, Bipin Kole and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters: dict | None = None):
    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data


def get_columns(filters):
    return [
        {
            "label": ("Journal Entry"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Journal Entries",
            "width": 150
        },
        {
            "label": ("Party"),
            "fieldname": "party",
            "fieldtype": "Link",
            "options": "Party",
            "width": 150
        },
        {
            "label": ("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 150
        },
		{
            "label": ("Account"),
            "fieldname": "account",
            "fieldtype": "Link",
			"options": "Acount",
            "width": 150
        },
		{
            "label": ("Party"),
            "fieldname": "party",
            "fieldtype": "Link",
			"options": "Party",
            "width": 150
        },
		{
            "label": ("Debit"),
            "fieldname": "debit",
            "fieldtype": "Currency",
            "width": 150
        },
		{
            "label": ("Credit"),
            "fieldname": "credit",
            "fieldtype": "Currency",
            "width": 150
        },
		{
            "label": ("Description"),
            "fieldname": "description",
            "fieldtype": "Small Text",
            "width": 150
        },
        {
            "label": ("Total Debit"),
            "fieldname": "total_debit",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": ("Total Credit"),
            "fieldname": "total_credit",
            "fieldtype": "Currency",
            "width": 130
        },
        {
           "label": ("Difference"),
            "fieldname": "difference",
            "fieldtype": "Currency",
            "width": 130
        },	
    ]


def get_data(filters):
    data = []

    invoices = frappe.get_all(
        "Journal Entries",
        fields=[
            "name",
            "party",
            "posting_date",
            "total_debit",
            "total_credit",
            "difference"			
        ]
    )

    for invoice in invoices:

        items = frappe.get_all(
            "Journal Entry Accounts",
            filters={
                "parent": invoice.name
            },
            fields=[
                "account",
                "party",
                "debit",
                "credit",
				"description"
            ]
        )

        for item in items:
            data.append({
                "name": invoice.name,
                "party": invoice.party,
                "posting_date": invoice.posting_date,
                "account": item.account,
                "party": item.party,
                "debit": item.debit,
                "credit": item.credit,
                "description": item.description,
                "total_debit": invoice.total_debit,
                "total_credit": invoice.total_credit,
                "difference": invoice.difference, 				
            })

    return data