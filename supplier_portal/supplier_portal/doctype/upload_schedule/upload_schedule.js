// Copyright (c) 2025, Aditya Das and contributors
// For license information, please see license.txt

GET_SCHEDULE_ITEMS = "supplier_portal.supplier_portal.doctype.upload_schedule.upload_schedule.download_excel_file"
UPLOAD_DATA = "supplier_portal.supplier_portal.doctype.upload_schedule.upload_schedule.create_schedule_log"

frappe.ui.form.on("Upload Schedule", {
    ////---------------------------------------------------------------------------------------------------------------------------------------
    refresh(frm) {
	    frm.set_value("for_month", "");
	    frm.set_value("supplier", "");
	    frm.disable_save();
	
	    // var today = "2025-11-30"; 
	    var today = frappe.datetime.get_today();
	    var current_date = frappe.datetime.str_to_obj(today);
	    var current_month_index = current_date.getMonth(); // Get current month index (0-11)
	    var current_year = current_date.getFullYear();
	
	    let month_names = ["January", "February", "March", "April", "May", "June", 
	                       "July", "August", "September", "October", "November", "December"];
	    
	    // Get next month index (handle December case)
	    var next_month_index = (current_month_index + 1) % 12;  
	    var next_month = month_names[next_month_index];
	
	    // If next month is January, increment the year
	    if (next_month_index === 0) {
	        current_year += 1;
	    }
	
	    // If current month is December, show all months
	    let remaining_months = (current_month_index === 11) ? month_names : month_names.slice(current_month_index + 1);
	
	    console.log("Next Month:", next_month);
	    console.log("Months to show:", remaining_months);
	
	    frm.set_df_property('for_month', 'options', remaining_months);
	    frm.set_value("year", current_year);
	    frm.set_value("for_month", next_month);
	},

	////---------------------------------------------------------------------------------------------------------------------------------------

    download_template(frm){
		frappe.call({
			method: GET_SCHEDULE_ITEMS,
			args: {'data': frm.doc},
			callback: function(r) {
				frappe.show_alert({
				    message:__('Downloading template'),
				    indicator:'green'
				}, 3);
				window.location.href = r.message.file_url;
			}
		});
		frm.set_value("attach_template", "")
	},

	////---------------------------------------------------------------------------------------------------------------------------------------

	upload_data: function(frm) {
	    if (!frm.doc.attach_template) {
	        frappe.throw("Please attach file first");
	    }
	    frappe.confirm('This process will erase all the previous uploaded data in Annexure I. Are you sure you want to proceed ahead?', () => {
	        frappe.show_progress("Processing", 0, 100, "Starting...");
	        frappe.call({
	            method: UPLOAD_DATA,
	            args: { 'data': frm.doc },
	            callback: function(r) {
	                frappe.show_alert({
	                    message: __('Creating Sales Forecast Upload Records'),
	                    indicator: 'green'
	                }, 3);
	                window.location.href = r.message.file_url;
	            }
	        });
	
	        frappe.realtime.on('progress_update', function(data) {
	            frappe.show_progress("Processing", data.progress, data.total, data.message);
	        });
	    }, () => {});
	},
	
	////---------------------------------------------------------------------------------------------------------------------------------------
});

