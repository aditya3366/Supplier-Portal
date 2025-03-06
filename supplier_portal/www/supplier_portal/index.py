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

    ##==============================================================================================================================================
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
                fields=["name", "transaction_date", "status", "total", "supplier", "grand_total"],
                filters={"docstatus": 1, "supplier": ["in", supplier_list]},
                order_by="transaction_date DESC",
                limit_page_length=100,
                as_list=False
            )

            total_pos = 0
            total_purchase = 0
            total_completed_po = 0
            total_incomplete_po = 0

            for po in purchase_orders:
                total_pos = total_pos + 1
                total_purchase = total_purchase + (float(po.grand_total) if po.grand_total else 0)

                if po.status == "Completed" or po.status == "To Bill":
                    total_completed_po = total_completed_po + 1

                if po.status == "To Receive and Bill":
                    total_incomplete_po = total_incomplete_po + 1


                po["transaction_date"] = frappe.utils.format_date(po["transaction_date"], "dd-MM-yyyy")

            context.total_pos = total_pos
            context.total_purchase = total_purchase
            context.total_completed_po = total_completed_po
            context.total_incomplete_po = total_incomplete_po

    ##==============================================================================================================================================
    # If specific PO is requested, fetch its details
    if po_id and section == "":
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

    ##==============================================================================================================================================
    if po_id and section == "create_asn":
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
        context.section = "create_asn"
        return

    ##==============================================================================================================================================
    purchase_receipts = []
    if section == "purchase_receipts":
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
            purchase_receipts = frappe.get_all(
                "Purchase Receipt",
                fields=["name", "posting_date", "status", "total", "supplier", "grand_total"],
                filters={"docstatus": 1, "supplier": ["in", supplier_list]},
                order_by="posting_date DESC",
                limit_page_length=100,
                as_list=False
            )
            total_prs = 0
            for pr in purchase_receipts:
                total_prs = total_prs + 1
                pr["posting_date"] = frappe.utils.format_date(pr["posting_date"], "dd-MM-yyyy")

            context.total_prs = total_prs


    context.section = section
    context.purchase_orders = purchase_orders
    context.purchase_receipts = purchase_receipts
    context.url = frappe.utils.get_url()

#-------------------------------------------------------------------------------------------------------------------------------------------------

  
    asn_list = []
    if section == "asn":
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
            asn_list = frappe.get_all(
                "Advance Shipment Notification",
                fields=["name", "posting_date", "purchase_order", "supplier_invoice_no"],
                filters={"supplier": ["in", supplier_list]},
                order_by="posting_date DESC",
                limit_page_length=100,
                as_list=False
            )

            for asn in asn_list:
                asn["posting_date"] = frappe.utils.format_date(asn["posting_date"], "dd-MM-yyyy")

    ## Set context values
    context.section = section
    context.purchase_orders = purchase_orders
    context.asn_list = asn_list
    context.url = frappe.utils.get_url()
##-----------------------------------------------------------------------------------------------------------------------------------------------

# @frappe.whitelist()
# def create_asn(po_id):
#     # Your logic here (e.g., create ASN, update records, etc.)
#     doc = frappe.get_doc("Purchase Order", po_id)
#     # Perform necessary actions
#     return frappe.msgprint(f"ASN created for {po_id}")

@frappe.whitelist()
def create_asn(data):
    data = frappe.parse_json(data)
    po_id = data.get("po_id")
    supplier_invoice_scan_copy = data.get("supplier_invoice_scan_copy")
    invoice_no = data.get("invoice_no")
    invoice_date = data.get("invoice_date")
    
    if not po_id:
        return frappe.throw(_("Purchase Order ID is required"))
    
    # Create ASN document
    asn = frappe.new_doc("Advance Shipment Notification")
    asn.purchase_order = po_id
    asn.supplier = frappe.get_value("Purchase Order", po_id, "supplier")
    asn.supplier_invoice_no = invoice_no
    asn.supplier_invoice_scan_copy = supplier_invoice_scan_copy
    asn.invoice_date = invoice_date

    if supplier_invoice_scan_copy:
        file_doc = frappe.get_value("File", {"file_url": supplier_invoice_scan_copy}, "name")
        if file_doc:
            asn.supplier_invoice_scan_copy = supplier_invoice_scan_copy
        else:
            frappe.throw(_("Invalid file URL"))

    # Add ASN items
    if "items" in data and isinstance(data["items"], list):
        for item in data["items"]:
            asn.append("items", {
                "item_code": item.get("item_code"),
                "supplied_quantity": float(item.get("qty")),
                "item_name": frappe.get_value("Item", item.get("item_code"), "item_name"),
                "uom": frappe.get_value("Purchase Order Item", 
                                        {"parent": po_id, "item_code": item.get("item_code")},
                                        "uom") 
            })

    asn.insert(ignore_permissions=True)
    asn.save()
    
    return frappe.msgprint(_("Advance Shipping Notification created successfully"))



