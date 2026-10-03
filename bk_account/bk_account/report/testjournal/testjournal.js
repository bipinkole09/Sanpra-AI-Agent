// Copyright (c) 2026, Bipin Kole and contributors
// For license information, please see license.txt

frappe.query_reports["TestJournal"] = {
	filters: [
		{
			"fieldname": "name",
			"label": __("Journal Entries"),
			"fieldtype": "Link",
			"options": "Journal Entries"
		},
	],
};
