frappe.pages['s'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Weekly Scheduled Items',
        single_column: true
    });

    $(wrapper).html(`
        <h3>Weekly Scheduled Items</h3>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;margin-top: -70px;">
            <a></a>
            <a href="/supplier_portal?section=create_asn" class="btn btn-primary">Create ASN</a>
        </div>

        <div class="d-flex gap-3 mb-4">
            <div class="info-card" id="current_week"></div>
            <div class="info-card" id="current_month"></div>
            <div class="info-card" id="current_year"></div>
        </div>

        <table class="table table-bordered">
            <thead>
                <tr>
                    <th>Purchase Order</th>
                    <th>Item</th>
                    <th>Month</th>
                    <th>Year</th>
                    <th id="week_column"></th>
                </tr>
            </thead>
            <tbody id="schedule-table-body"></tbody>
        </table>
    `);

    frappe.call({
        method: "supplier_portal.supplier_portal.page.s.s.fetch_all_scheduled_items",
        callback: function(response) {
            if (response.message) {
                let data = response.message;
                $("#current_week").html(`<strong>Current Week:</strong> ${data.current_week}`);
                $("#current_month").html(`<strong>Current Month:</strong> ${data.current_month}`);
                $("#current_year").html(`<strong>Current Year:</strong> ${data.current_year}`);
                $("#week_column").text(data.current_week);

                let tableBody = $("#schedule-table-body");
                tableBody.empty();
                data.scheduled_items.forEach(row => {
                    tableBody.append(`<tr>
                        <td>${row.purchase_order}</td>
                        <td>${row.item}</td>
                        <td>${row.month}</td>
                        <td>${row.year}</td>
                        <td>${row.week_qty || '-'}</td>
                    </tr>`);
                });
            }
        }
    });
};
