# Copyright (c) 2025, Aditya Das and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AdvanceShipmentNotification(Document):
	pass

import frappe
from frappe.model.document import Document

@frappe.whitelist()
def create_purchase_receipt(asn_name):
    asn = frappe.get_doc("Advance Shipping Notification", asn_name)

    # Create new Purchase Receipt
    pr = frappe.new_doc("Purchase Receipt")
    pr.supplier = asn.supplier  # Map supplier
    pr.supplier_invoice_no = asn.supplier_invoice_no
    pr.invoice_date = asn.invoice_date
    pr.shipping_by = asn.shipping_by
    pr.vehicle_no = asn.vehical_no
    pr.asn_reference = asn.name  # Add ASN reference for tracking

    # Add Items from ASN
    for item in asn.items:
        pr.append("items", {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "qty": item.supplied_quantity,
            "uom": item.uom,
            "purchase_order": item.purchase_order
            
        })

    pr.insert(ignore_permissions=True)  # Insert as draft
    frappe.msgprint(_("Purchase Receipt {0} created successfully!".format(pr.name)))

    return pr.name
