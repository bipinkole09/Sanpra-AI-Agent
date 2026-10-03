# Copyright (c) 2026, Bipin Kole and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class JournalEntries(Document):

    def validate(self):

        self.total_debit = 0
        self.total_credit = 0

        for row in self.accounting_entries:
            self.total_debit += row.debit
            self.total_credit += row.credit

    def on_submit(self):
        self.make_gl_entries()

    def on_cancel(self):
        self.make_reverse_gl_entries()

    def make_gl_entries(self):
        pass

    def make_reverse_gl_entries(self):
        pass