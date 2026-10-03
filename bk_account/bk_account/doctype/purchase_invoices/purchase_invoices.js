// Copyright (c) 2026, Bipin Kole and contributors
// For license information, please see license.txt


frappe.ui.form.on("Purchase Invoice", {

    setup(frm) {

        // Credit To
        frm.set_query("credit_to", function () {
            return {
                filters: {
                    account_type: "Liability",
                    is_group: 0
                }
            };
        });

        // Expense Account
        frm.set_query("expense_account", function () {
            return {
                filters: {
                    account_type: "Expense",
                    is_group: 0
                }
            };
        });

    },

    refresh(frm) {
        calculate_purchase_totals(frm);
    }

});


frappe.ui.form.on("Purchase Invoice items", {

    qty(frm, cdt, cdn) {
        calculate_purchase_totals(frm);
    },

    rate(frm, cdt, cdn) {
        calculate_purchase_totals(frm);
    },

    items_add(frm, cdt, cdn) {
        calculate_purchase_totals(frm);
    },

    items_remove(frm, cdt, cdn) {
        calculate_purchase_totals(frm);
    }

});


function calculate_purchase_totals(frm) {

    let total_qty = 0;
    let total_amount = 0;

    (frm.doc.items_table || []).forEach(row => {

        let qty = flt(row.qty);
        let rate = flt(row.rate);

        // Calculate row Amount
        let amount = qty * rate;

        // Set Amount in Items Table
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

    // Set parent totals
    frm.set_value("total_qty", total_qty);
    frm.set_value("total_amount", total_amount);

}

// frappe.ui.form.on("Purchase Invoice", {

//     setup(frm) {

//         // Credit To
//         frm.set_query("credit_to", function () {
//             return {
//                 filters: {
//                     account_type: "Liability",
//                     is_group: 0
//                 }
//             };
//         });

//         // Expense Account
//         frm.set_query("expense_account", function () {
//             return {
//                 filters: {
//                     account_type: "Expense",
//                     is_group: 0
//                 }
//             };
//         });

//     }

// });



// frappe.ui.form.on("Purchase Invoices", {
//     refresh(frm) {
//         calculate_totals(frm);
//     }
// });


// frappe.ui.form.on("Purchase Invoice items", {

//     qty(frm, cdt, cdn) {
//         calculate_amount(frm, cdt, cdn);
//     },

//     rate(frm, cdt, cdn) {
//         calculate_amount(frm, cdt, cdn);
//     },

//     item(frm, cdt, cdn) {
//         calculate_amount(frm, cdt, cdn);
//     }

// });


// function calculate_amount(frm, cdt, cdn) {

//     let row = locals[cdt][cdn];

//     let qty = flt(row.qty);
//     let rate = flt(row.rate);

//     let amount = qty * rate;

//     frappe.model.set_value(cdt, cdn, "amount", amount);

//     calculate_totals(frm);
// }


// function calculate_totals(frm) {

//     let total_qty = 0;
//     let total_amount = 0;

//     (frm.doc.items || []).forEach(function(row) {

//         total_qty += flt(row.qty);
//         total_amount += flt(row.amount);

//     });

//     frm.set_value("total_qty", total_qty);
//     frm.set_value("total_amount", total_amount);
// }