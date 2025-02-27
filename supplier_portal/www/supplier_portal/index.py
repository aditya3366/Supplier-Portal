import frappe

def get_context(context):
    """Fetch data for the supplier portal web page."""
    # Get section from URL
    section = frappe.form_dict.get("section", "")

    purchase_orders = []
    if section == "purchase_orders":
        purchase_orders = frappe.get_all(
            "Purchase Order",
            fields=["name", "transaction_date", "status", "total"],
            filters={"docstatus": 1},  # Fetch only submitted orders
            order_by="transaction_date DESC",
            limit_page_length=10,
            as_list=False
        )

        # Convert transaction_date to string format (DD-MM-YYYY)
        for po in purchase_orders:
            po["transaction_date"] = frappe.utils.format_date(po["transaction_date"], "dd-MM-yyyy")

    # Pass variables to the template
    context.section = section
    context.purchase_orders = purchase_orders
    context.url = frappe.utils.get_url()  # Get base URL for links
