// Copyright (c) 2026, Bipin Kole and contributors
// For license information, please see license.txt

console.log("Sales Invoice Items JS Loaded");

frappe.ui.form.on("Sales Invoice Items", {

    qty: function(frm, cdt, cdn) {
        console.log("Qty Changed");
        calculate(frm, cdt, cdn);
    },

    rate: function(frm, cdt, cdn) {
        console.log("Rate Changed");
        calculate(frm, cdt, cdn);
    }

});

function calculate(frm, cdt, cdn) {

    let row = locals[cdt][cdn];

    let amount = (row.qty || 0) * (row.rate || 0);

    console.log("Qty :", row.qty);
    console.log("Rate :", row.rate);
    console.log("Amount :", amount);

    frappe.model.set_value(cdt, cdn, "amount", amount);
}