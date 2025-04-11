import frappe
from frappe import _
from datetime import datetime

def get_context(context):
    """Fetch data for the supplier portal web page."""

    # Redirect to login if user is not logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect

    section = frappe.form_dict.get("section", "")
    po_id = frappe.form_dict.get("po_id", None)
    asn_id = frappe.form_dict.get("asn_id", None) 

    today = datetime.today()

    # Determine the current week based on today's date
    if 1 <= today.day <= 7:
        current_week = "Week-1 (1st - 7th)"
    elif 8 <= today.day <= 14:
        current_week = "Week-2 (8th - 14th)"
    elif 15 <= today.day <= 21:
        current_week = "Week-3 (15th - 21st)"
    elif 22 <= today.day <= 28:
        current_week = "Week-4 (22nd - 28th)"
    else:
        current_week = "Week-5 (29th - End of Month)"

    # Assign values to the context (used in Jinja templates)
    context.current_month = today.strftime("%B")  # Example: "March"
    context.current_year = today.year  # Example: 2024
    context.current_week = current_week

    


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
    # if po_id and section == "create_asn":
    #     purchase_order = frappe.get_doc("Purchase Order", po_id)

    #     # Fetch items table
    #     purchase_order.items = frappe.get_all(
    #         "Purchase Order Item",
    #         filters={"parent": po_id},
    #         fields=["item_code", "item_name", "qty", "rate", "amount"]
    #     )

    #     # Format date
    #     purchase_order.transaction_date = frappe.utils.format_date(
    #         purchase_order.transaction_date, "dd-MM-yyyy"
    #     )

    #     context.purchase_order = purchase_order
    #     context.section = "create_asn"
    #     return

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
    if section == "scheduled_items":
        context.update(fetch_all_scheduled_items())
    if section == "create_asn":
        context.update(fetch_all_scheduled_items())

  
    # if asn_id:
    if asn_id and section == "":
        asn = frappe.get_doc("Advance Shipment Notification", asn_id)
        
        # Fetch child table items
        asn.items = frappe.get_all(
            "ASN Items",  # Replace with actual child table name if different
            filters={"parent": asn_id},
            fields=["item_code", "item_name", "supplied_quantity", "uom"]
        )

        asn.posting_date = frappe.utils.format_date(asn.posting_date, "dd-MM-yyyy")

        context.asn = asn
        context.section = "asn_detail"
        return

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
                filters={"docstatus": 1,"supplier": ["in", supplier_list]},
                order_by="posting_date DESC",
                limit_page_length=100,
                as_list=False
            )

            for asn in asn_list:
                asn["posting_date"] = frappe.utils.format_date(asn["posting_date"], "dd-MM-yyyy")

    ## Set context values
    context.section = section
    context.asn_list = asn_list
    context.url = frappe.utils.get_url()
##-----------------------------------------------------------------------------------------------------------------------------------------------

# @frappe.whitelist()
# def create_asn(po_id):
#     # Your logic here (e.g., create ASN, update records, etc.)
#     doc = frappe.get_doc("Purchase Order", po_id)
#     # Perform necessary actions
#     return frappe.msgprint(f"ASN created for {po_id}")

# @frappe.whitelist()
# def create_asn(data):
#     data = frappe.parse_json(data)
#     po_id = data.get("po_id")
#     supplier_invoice_scan_copy = data.get("supplier_invoice_scan_copy")
#     invoice_no = data.get("invoice_no")
#     invoice_date = data.get("invoice_date")
    
#     if not po_id:
#         return frappe.throw(_("Purchase Order ID is required"))
    
#     # Create ASN document
#     asn = frappe.new_doc("Advance Shipment Notification")
#     asn.purchase_order = po_id
#     asn.supplier = frappe.get_value("Purchase Order", po_id, "supplier")
#     asn.supplier_invoice_no = invoice_no
#     asn.supplier_invoice_scan_copy = supplier_invoice_scan_copy
#     asn.invoice_date = invoice_date

#     if supplier_invoice_scan_copy:
#         file_doc = frappe.get_value("File", {"file_url": supplier_invoice_scan_copy}, "name")
#         if file_doc:
#             asn.supplier_invoice_scan_copy = supplier_invoice_scan_copy
#         else:
#             frappe.throw(_("Invalid file URL"))

#     # Add ASN items
#     if "items" in data and isinstance(data["items"], list):
#         for item in data["items"]:
#             asn.append("items", {
#                 "item_code": item.get("item_code"),
#                 "purchase_order": po_id,
#                 "supplied_quantity": float(item.get("qty")),
#                 "item_name": frappe.get_value("Item", item.get("item_code"), "item_name"),
#                 "uom": frappe.get_value("Purchase Order Item", 
#                                         {"parent": po_id, "item_code": item.get("item_code")},
#                                         "uom") 
#             })

#     asn.insert(ignore_permissions=True)
#     asn.submit()  # Submitting the ASN

#     frappe.msgprint(_("Advance Shipping Notification created successfully"))

#     return asn.name


@frappe.whitelist()
def create_asn(data):
    data = frappe.parse_json(data)
    supplier_invoice_scan_copy = data.get("supplier_invoice_scan_copy")
    invoice_no = data.get("invoice_no")
    invoice_date = data.get("invoice_date")
    shipping_by = data.get("shipping_by")
    vehical_no = data.get("vehical_no")

    # Create ASN document
    asn = frappe.new_doc("Advance Shipment Notification")
    
    asn.supplier_invoice_no = invoice_no
    asn.supplier_invoice_scan_copy = supplier_invoice_scan_copy
    asn.invoice_date = invoice_date
    asn.shipping_by = shipping_by
    asn.vehical_no = vehical_no

    # Validate file existence
    if supplier_invoice_scan_copy:
        file_doc = frappe.get_value("File", {"file_url": supplier_invoice_scan_copy}, "name")
        if not file_doc:
            frappe.throw(_("Invalid file URL"))

    supplied_qty_tracker = {}

    # Add ASN items
    if "items" in data and isinstance(data["items"], list):
        for item in data["items"]:
            item_code = item.get("item_code")
            purchase_order = item.get("purchase_order")
            supplied_qty = float(item.get("qty"))
            year = item.get("year")
            month = item.get("month")
            current_week = item.get("current_week")
            week_qty = float(item.get("week_qty", 0))

            # Fetch item name
            item_name = frappe.get_value("Item", item_code, "item_name")
            uom = frappe.get_value("Purchase Order Item",{"parent": purchase_order, "item_code": item_code},"uom")
            supplier = frappe.get_value("Purchase Order",{"name": purchase_order, "item_code": item_code},"uom")

            existing_supplied_qty = frappe.db.sql("""
                SELECT SUM(supplied_quantity) 
                FROM `tabASN Items`
                WHERE parentfield = 'items' 
                AND item_code = %s 
                AND month = %s 
                AND year = %s 
                AND week = %s
            """, (item_code, month, year, current_week))[0][0] or 0

            # Calculate total supplied quantity including the current entry
            total_supplied_qty = existing_supplied_qty + supplied_qty

            # Check if total supplied quantity exceeds week_qty
            if total_supplied_qty > week_qty:
                frappe.throw(
                    _("Total supplied quantity ({}) exceeds the allowed week quantity ({}) for item: {}")
                    .format(total_supplied_qty, week_qty, item_code)
                )
               
            # Append to ASN
            asn.append("items", {
                "item_code": item_code,
                "purchase_order": purchase_order,
                "supplied_quantity": supplied_qty,
                "item_name": item_name,
                "uom":uom,
                "week": current_week,
                "week_qty": week_qty,
                "month": month,
                "year": year
            })

    asn.insert(ignore_permissions=True)
    asn.submit()  # Submitting the ASN

    frappe.msgprint(_("Advance Shipping Notification created successfully"))

    return asn.name  # Return ASN name for frontend redirection


#------------------------------------------------------------------------------------------------------------------------------------


import frappe
from frappe.utils.pdf import get_pdf

@frappe.whitelist()
def view_asn_print(asn_id):
    """Render the ASN Print Format for preview and download as PDF"""
    if not asn_id:
        frappe.throw(_("ASN ID is required"))

    asn = frappe.get_doc("Advance Shipment Notification", asn_id)
    context = {"asn": asn}

    # Render HTML template
    html = frappe.render_template("templates/asn_print.html", context)

    # Convert HTML to PDF
    pdf_data = get_pdf(html)

    # Send PDF as response
    frappe.local.response.filename = f"ASN_{asn_id}.pdf"
    frappe.local.response.filecontent = pdf_data
    frappe.local.response.type = "pdf"



def fetch_all_scheduled_items():
    """Fetch all rows from the Item Schedule child table across all Purchase Orders 
       where the current month and year match the values in the table."""
    
    today = datetime.today()
    current_month = today.strftime("%B")  # Example: "October"
    current_year = today.year

    # Determine the current week column based on today's date
    if 1 <= today.day <= 7:
        current_week_column = "week_i"
    elif 8 <= today.day <= 14:
        current_week_column = "week_ii"
    elif 15 <= today.day <= 21:
        current_week_column = "week_iii"
    elif 22 <= today.day <= 28:
        current_week_column = "week_iv"
    else:
        current_week_column = "week_v"

    # Fetch data where the month and year match the current month and year
    scheduled_items = frappe.db.sql(f"""
        SELECT 
            sc.purchase_order,
            sc.item,
            sc.month,
            sc.year,
            sc.{current_week_column} AS week_qty
        FROM `tabItem Schedule` sc
        INNER JOIN `tabPurchase Order` po ON sc.parent = po.name
        WHERE sc.month = %s AND sc.year = %s
        ORDER BY sc.purchase_order, sc.item
    """, (current_month, current_year), as_dict=True)

    # Return a dictionary with filtered results
    return {
        "scheduled_items": scheduled_items,
        # "current_week": current_week_column.replace("_", " ").title(),  # Example: "Week IV"
        "current_month": current_month,
        "current_year": current_year
    }


# def get_current_week(today):
#     """Get the current week range (e.g., "Week 1: 1st - 7th")."""
#     first_day_of_month = today.replace(day=1)
#     week_number = get_current_week_number(today)
#     start_day = first_day_of_month.day + (week_number - 1) * 7
#     end_day = min(start_day + 6, (today.replace(day=1, month=today.month % 12 + 1) - today.replace(day=1)).days)
#     return f"Week {week_number}: {start_day}th - {end_day}th"


# def get_current_week_number(today):
#     """Calculate the current week of the month."""
#     first_day_of_month = today.replace(day=1)
#     week_number = ((today - first_day_of_month).days // 7) + 1
#     return week_number


