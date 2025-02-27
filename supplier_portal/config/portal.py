from frappe import _

def get_data():
    return [
        {
            "module_name": "Supplier Portal",
            "category": "Modules",
            "label": _("Supplier Portal"),
            "icon": "octicon octicon-file-directory",
            "color": "#3498db",
            "type": "module",
            "link": "/supplier_portal"
        }
    ]
