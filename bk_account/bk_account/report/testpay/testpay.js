// Copyright (c) 2026, Bipin Kole and contributors
// For license information, please see license.txt

frappe.query_reports["TestPAY"] = {
	filters: [
		{
			"fieldname": "name",
			"label": __("Payment Entries"),
			"fieldtype": "Link",
			"options":("Payment Entries"),
		},
	],
};
