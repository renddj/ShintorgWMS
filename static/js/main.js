// Live search for product table
document.addEventListener("DOMContentLoaded", function () {
    var searchInput = document.getElementById("search-input");
    var filterType = document.getElementById("filter-type");
    var filterZone = document.getElementById("filter-zone");

    function filterTable() {
        var query = searchInput ? searchInput.value.toLowerCase() : "";
        var type = filterType ? filterType.value : "";
        var zone = filterZone ? filterZone.value : "";

        var rows = document.querySelectorAll("table tbody tr[data-search]");
        rows.forEach(function (row) {
            var text = (row.dataset.search || "").toLowerCase();
            var rowType = row.dataset.type || "";
            var rowZone = row.dataset.zone || "";

            var matchSearch = !query || text.includes(query);
            var matchType = !type || rowType === type;
            var matchZone = !zone || rowZone === zone;

            row.style.display = (matchSearch && matchType && matchZone) ? "" : "none";
        });
    }

    if (searchInput) searchInput.addEventListener("input", filterTable);
    if (filterType) filterType.addEventListener("change", filterTable);
    if (filterZone) filterZone.addEventListener("change", filterTable);

    // Address form: cascade selects
    var addrType = document.getElementById("addr-type");
    var zoneSelect = document.getElementById("zone_id");
    var rowSelect = document.getElementById("row_id");
    var shelfSelect = document.getElementById("shelf_id");
    var levelSelect = document.getElementById("level_id");
    var shelfRow = document.getElementById("shelf-row");
    var levelRow = document.getElementById("level-row");

    function toggleAddrFields() {
        if (!addrType) return;
        var isExtended = addrType.value === "zone_row_shelf_level";
        if (shelfRow) shelfRow.style.display = isExtended ? "" : "none";
        if (levelRow) levelRow.style.display = isExtended ? "" : "none";
    }

    if (addrType) {
        addrType.addEventListener("change", toggleAddrFields);
        toggleAddrFields();
    }

    function loadOptions(url, select, placeholder) {
        select.innerHTML = '<option value="">-- ' + placeholder + ' --</option>';
        fetch(url)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                data.forEach(function (item) {
                    var opt = document.createElement("option");
                    opt.value = item.id;
                    opt.textContent = item.name;
                    select.appendChild(opt);
                });
            });
    }

    if (zoneSelect && rowSelect) {
        zoneSelect.addEventListener("change", function () {
            if (this.value) {
                loadOptions("/api/rows?zone_id=" + this.value, rowSelect, "выберите ряд");
                if (shelfSelect) shelfSelect.innerHTML = '<option value="">-- выберите стеллаж --</option>';
                if (levelSelect) levelSelect.innerHTML = '<option value="">-- выберите уровень --</option>';
            }
        });
    }

    if (rowSelect && shelfSelect) {
        rowSelect.addEventListener("change", function () {
            if (this.value) {
                loadOptions("/api/shelves?row_id=" + this.value, shelfSelect, "выберите стеллаж");
                if (levelSelect) levelSelect.innerHTML = '<option value="">-- выберите уровень --</option>';
            }
        });
    }

    if (shelfSelect && levelSelect) {
        shelfSelect.addEventListener("change", function () {
            if (this.value) {
                loadOptions("/api/levels?shelf_id=" + this.value, levelSelect, "выберите уровень");
            }
        });
    }

    // Product search in task form
    var productSearch = document.getElementById("product-search");
    var productId = document.getElementById("product_id");
    var productList = document.getElementById("product-list");

    if (productSearch && productList) {
        productSearch.addEventListener("input", function () {
            var q = this.value.toLowerCase();
            var items = productList.querySelectorAll(".product-option");
            items.forEach(function (item) {
                var txt = item.dataset.search || "";
                item.style.display = txt.includes(q) ? "" : "none";
            });
        });
    }

    // Confirm delete/cancel
    document.querySelectorAll("[data-confirm]").forEach(function (el) {
        el.addEventListener("click", function (e) {
            if (!confirm(this.dataset.confirm)) e.preventDefault();
        });
    });

    // Problem form toggle
    var problemBtn = document.getElementById("problem-toggle");
    var problemForm = document.getElementById("problem-form");
    if (problemBtn && problemForm) {
        problemBtn.addEventListener("click", function () {
            problemForm.style.display = problemForm.style.display === "none" ? "" : "none";
        });
    }
});
