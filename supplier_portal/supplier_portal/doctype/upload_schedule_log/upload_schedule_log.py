# Copyright (c) 2025, Aditya Das and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class UploadScheduleLog(Document):
	pass

def validate_po(doc, method=None):
	#--------------------------------------------------------------------------
	## UUDATE THE SCHEDULE IN THE PURCHASE ORDER
	#--------------------------------------------------------------------------
    if doc.purchase_order and doc.month and doc.year:
    	## Ge Purchase order doc...
        po = frappe.get_doc("Purchase Order", {'name': doc.purchase_order})
        
        ## append the schedule data in PO's item_schedule table..
        for s in doc.item_schedule:
            found = False
            for a in po.item_schedule:
                if a.item == s.item and a.month == s.month and a.year == s.year:
                    found = True
                    frappe.throw(f"You have already upload the schedule of item <b>{a.item}</b> for <b>{a.month}-{a.year}</b>. Please adjust the schedule directly in the PO.")
                else:
                    pass

            if found == False:       
                po.append("item_schedule", {
                    "purchase_order": s.purchase_order,
                    "item": s.item,
                    "month": s.month,
                    "year": s.year,
                    "week_i": s.week_i,
                    "week_ii": s.week_ii,
                    "week_iii": s.week_iii,
                    "week_iv": s.week_iv,
                    "week_v": s.week_v,
                    "total": s.total,
                })

        ## Validate if the Total Scheduled Quantity exceeds the Ordered Quantity...
        for i in po.items:
        	total_qty_scheduled = 0
        	for s in po.item_schedule:
        		if s.item == i.item_code:
        			total_qty_scheduled = total_qty_scheduled + s.total

        	if total_qty_scheduled > i.qty:
        		frappe.throw(f"In PO <b>{i.parent}</b>, total Scheduled quantity till now for item <b>{i.item_code}</b> is <b>{total_qty_scheduled}</b>, which is greater than the orderd qty <b>{i.qty}</b>. Please adjust the Item Schedule accordingly.")
        	else:
        		pass

        po.save()
