// Copyright (c) 2026, Bipin Kole and contributors
// For license information, please see license.txt

// Copyright (c) 2026, Bipin Kole and contributors
// For license information, please see license.txt

frappe.ui.form.on("Sales Invoice", {

    setup(frm) {

        // Debit To
        frm.set_query("debit_to", function () {
            return {
                filters: {
                    account_type: "Asset",
                    is_group: 0
                }
            };
        });

        // Income Account
        frm.set_query("income_account", function () {
            return {
                filters: {
                    account_type: "Income",
                    is_group: 0
                }
            };
        });

    },

    refresh(frm) {
        calculate_sales_totals(frm);
    }

});


frappe.ui.form.on("Sales Invoice items", {

    qty(frm, cdt, cdn) {
        calculate_sales_totals(frm);
    },

    rate(frm, cdt, cdn) {
        calculate_sales_totals(frm);
    },

    items_add(frm, cdt, cdn) {
        calculate_sales_totals(frm);
    },

    items_remove(frm, cdt, cdn) {
        calculate_sales_totals(frm);
    }

});


function calculate_sales_totals(frm) {

    let total_qty = 0;
    let total_amount = 0;

    (frm.doc.items_table || []).forEach(row => {

        let qty = flt(row.qty);
        let rate = flt(row.rate);

        // Calculate row amount
        let amount = qty * rate;

        // Update Amount in Items Table
        frappe.model.set_value(
            row.doctype,
            row.name,
            "amount",
            amount
        );

        // Calculate totals
        total_qty += qty;
        total_amount += amount;

    });

    // Update parent totals
    frm.set_value("total_qty", total_qty);
    frm.set_value("total_amount", total_amount);

}