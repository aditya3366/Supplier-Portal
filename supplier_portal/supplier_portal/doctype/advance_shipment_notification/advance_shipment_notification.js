// Copyright (c) 2025, Aditya Das and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Advance Shipment Notification", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Advance Shipment Notification", {
    refresh: function (frm) {
        // Add button only if the ASN is submitted
        if (frm.doc.name) {
            frm.add_custom_button(__('Create Purchase Receipt'), function () {
                frappe.call({
                    method: "supplier_portal.supplier_portal.doctype.advance_shipment_notification.advance_shipment_notification.create_purchase_receipt",
                    args: {
                        asn_name: frm.doc.name
                    },
                    callback: function (r) {
                        if (r.message) {
                            frappe.msgprint(__("Purchase Receipt {0} created successfully!", [r.message]));
                            frappe.set_route("Form", "Purchase Receipt", r.message);
                        }
                    }
                });
            }, __("Create"));
        }
    }
});
