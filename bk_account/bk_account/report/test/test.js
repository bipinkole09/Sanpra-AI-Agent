// Copyright (c) 2026, Bipin Kole and contributors
// For license information, please see license.txt

frappe.query_reports["Test"] = {
	filters: [
		{
			"fieldname": "name",
			"label": __("Sales Invoices"),
			"fieldtype": "Link",
			"options": "Sales Invoices"

		},
	],
};
