import frappe
from frappe import _

def get_context(context):
    """Fetch data for the supplier portal web page."""

    # Redirect to login if user is not logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect

    section = frappe.form_dict.get("section", "")
    po_id = frappe.form_dict.get("po_id", None)

    # If specific PO is requested, fetch its details
    if po_id:
        purchase_order = frappe.get_doc("Purchase Order", po_id)

        # Fetch items table
        purchase_order.items = frappe.get_all(
            "Purchase Order Item",
            filters={"parent": po_id},
            fields=["item_code", "item_name", "qty", "rate", "amount"]
        )

        # Format date
        purchase_order.transaction_date = frappe.utils.format_date(
            purchase_order.transaction_date, "dd-MM-yyyy"
        )

        context.purchase_order = purchase_order
        context.section = "purchase_order_detail"
        return

    purchase_orders = []
    if section == "purchase_orders":
        supplier_list = frappe.db.sql(
            """
            SELECT DISTINCT parent 
            FROM `tabPortal User` 
            WHERE user = %s AND parenttype = 'Supplier'
            """,
            (frappe.session.user,),
            as_list=True
        )

        supplier_list = [supplier[0] for supplier in supplier_list]

        if supplier_list:
            purchase_orders = frappe.get_all(
                "Purchase Order",
                fields=["name", "transaction_date", "status", "total", "supplier"],
                filters={"docstatus": 1, "supplier": ["in", supplier_list]},
                order_by="transaction_date DESC",
                limit_page_length=10,
                as_list=False
            )

            for po in purchase_orders:
                po["transaction_date"] = frappe.utils.format_date(po["transaction_date"], "dd-MM-yyyy")

    context.section = section
    context.purchase_orders = purchase_orders
    context.url = frappe.utils.get_url()
