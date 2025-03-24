 # Copyright (c) 2025, Aditya Das and contributors
# For license information, please see license.txt

import frappe
import os
from frappe.utils import get_files_path
import json
import csv
import openpyxl
from openpyxl import Workbook
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import numbers

import frappe
from frappe.model.document import Document
from frappe.utils.file_manager import save_file
from frappe.utils import get_site_path, get_url
from frappe.handler import download_file

from frappe.model.document import Document



class UploadSchedule(Document):
	pass

ITEM_SCHEDULE_FIELDS = ['supplier','po_no', 'item_code', 'month', 'year', 'week_i', 'week_ii', 'week_iii', 'week_iv', 'week_v']

##-------------------------------------------------------------------------------------------------------------------------------------------------

def read_data_from_excel(file_path, field_list):
    try:
        # Read the Excel file
        df = pd.read_excel(file_path, header=0, usecols=field_list)
        df.fillna('', inplace=True)
        # Convert to list
        data_list = []
        for index, row in df.iterrows():
            row_dict = {}
            for col_name in field_list:
                row_dict[col_name] = row[col_name]
            data_list.append(row_dict)
        return data_list

    except Exception as e:
        raise e

##-------------------------------------------------------------------------------------------------------------------------------------------------

def get_po_items(data):
    branch = data.get("branch")
    
    # Start tracking the SQL query execution
    # frappe.msgprint(f"Fetching party-specific items for branch: {branch}")
    
    query = f"""
        SELECT po.supplier, po.name as po_no, poi.item_code, "{data.get("for_month")}" month, {data.get("year")} year, 
        	   "" week_i, "" week_ii, "" week_iii, "" week_iv, "" week_v
		FROM `tabPurchase Order` as po
		     LEFT JOIN `tabPurchase Order Item` as poi ON poi.parent = po.name
		WHERE po.supplier = "{data.get("supplier")}"
			  AND po.docstatus = 1
			  AND po.status NOT IN ("Completed", "To Bill", "Draft")
    """
    
    # Executing the query and capturing any potential errors
    try:
        report = frappe.db.sql(query, as_dict=True)
        # frappe.msgprint(f"SQL Query executed successfully, {len(report)} records fetched.")
    except Exception as e:
        frappe.msgprint(f"Error executing SQL query: {str(e)}")
        return []
    
    # Processing data to final_data structure
    final_data = [
        {   
            'supplier': r.supplier,
            "po_no": r.po_no,
            "item_code": r.item_code,
            "month": r.month,
            "year": r.year,
            "week_i": "",  
            "week_ii": "",
            "week_iii": "",
            "week_iv": "",
            "week_v": "",
        }
        for r in report    
    ]

    # Ensure custom_ref_code is numeric, convert it to integer if so
    for d in final_data:
        num = d.get("item_code")
        if num.isdigit():
            d.update({"item_code": int(num)})
        else:
            d.update({"item_code": num})

    
    return final_data

##-------------------------------------------------------------------------------------------------------------------------------------------------

def create_schedule_data(data):
    records = get_po_items(data)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "data"

    # Hardcoded headers if something is changed update here
    sheet.append(['supplier','po_no', 'item_code', 'month', 'year', 'week_i', 'week_ii', 'week_iii', 'week_iv', 'week_v'])
    
    # Adding data rows
    for record in records:
        row = list(record.values())
        sheet.append(row)  # Append the row data

    # Fetch the open forecast
    suplier = data.get('supplier').replace(" ", "_")
    year = data.get('year')
    month = data.get('for_month')
    file_path = f"/tmp/ITM_SCH_{suplier}_{month}_{year}_.xlsx"
    
    # Save the workbook to the file path
    workbook.save(file_path)
    return file_path

##-------------------------------------------------------------------------------------------------------------------------------------------------

@frappe.whitelist()
def download_excel_file(data):
    data = json.loads(data)
    file_path = create_schedule_data(data)

    with open(file_path, "rb") as filedata:
        file_name = os.path.basename(file_path)  # Extract the file name from the path
        content = filedata.read()

    # Check if the file already exists in the files directory
    file_path_in_files = os.path.join(get_files_path(), file_name)

    # If file exists, rename it by appending a suffix
    if os.path.exists(file_path_in_files):
        base_name, extension = os.path.splitext(file_name)
        i = 1
        while os.path.exists(os.path.join(get_files_path(), f"{base_name}_{i}{extension}")):
            i += 1
        file_name = f"{base_name}_{i}{extension}"

    # Save file in the File Manager with the adjusted name
    file_object = save_file(file_name, content, "Upload Schedule", 'Upload Schedule', is_private=False)

    file_url = get_url() + "/files/" + file_object.file_name
    return {"file_url": file_url}

##----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@frappe.whitelist()
def create_schedule_log(data):
    data = json.loads(data)
    
    # Read excel data
    file_path = get_url() + data.get("attach_template")
    records = read_data_from_excel(file_path, ITEM_SCHEDULE_FIELDS)
    
    record_data = {}

    # Initialize progress tracking
    row_num = 0
    total_records = len(records)
    frappe.publish_realtime("progress_update", {"progress": 0, "total": total_records, "message": "Starting process..."})
    
    # **Step 1: Group records by `po_no`**
    for record in records:
        row_num += 1  # Track row number
        
        po_no = record['po_no']
        
        # Validation: Ensure `po_no` is not empty
        if po_no in ['', None]:
            frappe.throw(f"Error: po_no field is empty or null at row number {row_num}.")

        # Group by `po_no`
        if po_no not in record_data:
            record_data[po_no] = []
        
        record_data[po_no].append(record)

        # Publish progress update
        frappe.publish_realtime("progress_update", {
            "progress": row_num,
            "total": total_records,
            "message": f"Processing record {row_num}/{total_records}..."
        })
    # frappe.msgprint(f"{record_data}")
    try:
        processed_count = 0
        
        for po_no, po_records in record_data.items():
            # **Step 2: Create a separate Sales Forecast Upload Record per `po_no`**
            doc = frappe.new_doc("Upload Schedule Log")
            doc.purchase_order = po_no  # Assign PO Number 
            doc.supplier = record.get("supplier")
            doc.month = record.get("month")
            doc.year = record.get("year")
            doc.attached_file = data.get("attach_template")
            

            # **Step 3: Append records to the child table (`sales_forecast_logs`)**
            for record in po_records:
                doc.append("item_schedule", {
                    "purchase_order": record.get("po_no"),
                    "item": record.get("item_code"),
                    "month": record.get("month"),
                    "year": record.get("year"),
                    "week_i": record.get("week_i") or 0,
                    "week_ii": record.get("week_ii") or 0,
                    "week_iii": record.get("week_iii") or 0,
                    "week_iv": record.get("week_iv") or 0,
                    "week_v": record.get("week_v") or 0,
                    "total": (record.get("week_i") or 0) + (record.get("week_ii") or 0) + (record.get("week_iii") or 0) + (record.get("week_iv") or 0) + (record.get("week_v") or 0),
                })


            # Save and submit the document
            doc.save()
            frappe.msgprint(f"Item Schedule updated in the respected POs Successfully.")
            doc.submit()

            # # **Step 4: Show success message with document link**
            # formatted_name = doc.name.replace(" ", "%20")
            # document_link = f"http://india-salesdev.nelsongp.com/app/sales-forecast-upload-records/{formatted_name}"
            # frappe.msgprint(f"Sales Forecast Upload Records for PO <b>{po_no}</b> created successfully. <a href='{document_link}' target='_blank'>{doc.name}</a> to view the document.")

            # **Step 5: Progress update**
            processed_count += 1
            frappe.publish_realtime("progress_update", {
                "progress": processed_count,
                "total": len(record_data),
                "message": f"Created {processed_count}/{len(record_data)} records for PO {po_no}..."
            })

    except Exception as e:
        frappe.publish_realtime("progress_update", {
            "progress": row_num,
            "total": total_records,
            "message": f"Error encountered: {str(e)}"
        })
        raise e

##-------------------------------------------------------------------------------------------------------------------------------------------------
