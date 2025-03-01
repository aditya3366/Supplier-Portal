import frappe

def custom_redirect(login_manager):
    user = frappe.session.user
    user_type = frappe.get_value("User", user, "user_type")

    # Redirect Website Users to Supplier Portal
    if user_type == "Website User":
        frappe.local.response["home_page"] = "/supplier_portal"
