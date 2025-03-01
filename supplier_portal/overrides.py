import frappe

def custom_supplier_sidebar():
    return [
        {"title": "Dashboard", "route": "/dashboard", "icon": "home"},
        {"title": "Custom Quotations", "route": "/custom-quotations", "icon": "file-text"},
        {"title": "Purchase Orders", "route": "/purchase-orders", "icon": "shopping-cart"},
        {"title": "Invoices", "route": "/invoices", "icon": "credit-card"},
        {"title": "Addresses", "route": "/addresses", "icon": "map-marker"},
        {"title": "Profile", "route": "/me", "icon": "user"},
    ]

def override_supplier_sidebar():
    frappe.website_sidebar_items = custom_supplier_sidebar
