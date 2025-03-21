import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def execute():
	frappe.reload_doc("buying", "doctype", "purchase_order")

	create_custom_field("Purchase Order",
		dict(fieldname="item_schedule_tab", label="Item Schedule",
			fieldtype="Tab Break", insert_after="other_charges_calculation"))

	create_custom_field("Purchase Order",
		dict(fieldname="item_schedule", label="Schedule",
			fieldtype="Table", options="Item Schedule", insert_after="item_schedule_tab", allow_on_submit=1))