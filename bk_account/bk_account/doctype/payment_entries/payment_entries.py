# Copyright (c) 2026, Bipin Kole and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PaymentEntries(Document):

    def on_submit(self):
        self.make_gl_entries()

    def on_cancel(self):
        self.make_reverse_gl_entries()

    def make_gl_entries(self):
        pass

    def make_reverse_gl_entries(self):
        pass