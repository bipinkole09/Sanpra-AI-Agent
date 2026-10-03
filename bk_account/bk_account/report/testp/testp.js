// Copyright (c) 2026, Bipin Kole and contributors
// For license information, please see license.txt

frappe.query_reports["TestP"] = {
	filters: [
		{
			"fieldname": "name",
			"label": __("Purchase Invoices"),
			"fieldtype": "Link",
			"options": "Purchase Invoices"
		},
	],
};
