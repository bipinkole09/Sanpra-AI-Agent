# Copyright (c) 2026, Bipin Kole and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class SalesInvoices(Document):

    def validate(self):
        self.total_qty = 0
        self.total_amount = 0

        for item in self.items_table:
            item.amount = flt(item.qty) * flt(item.rate)

            self.total_qty += flt(item.qty)
            self.total_amount += flt(item.amount)

        if self.total_amount <= 0:
            frappe.throw("Total Amount must be greater than zero")

        if not self.customer:
            frappe.throw("Please Select Customer")

        if not self.debit_to:
            frappe.throw("Please Select Debit To Account")

        if not self.income_account:
            frappe.throw("Please Select Income Account")