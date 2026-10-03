# Copyright (c) 2026, Bipin Kole and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class GLEntries(Document):

    def make_gl_entry(
        self,
        account,
        debit_amount=0,
        credit_amount=0
    ):
        # your code here
        pass