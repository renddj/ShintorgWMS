function loadOptions(url, selectEl, placeholder) {
    selectEl.innerHTML = '<option value="">-- ' + placeholder + ' --</option>';
    fetch(url)
        .then(function(r) { return r.json(); })
        .then(function(data) {
            data.forEach(function(item) {
                var opt = document.createElement("option");
                opt.value = item.id;
                opt.textContent = item.name;
                selectEl.appendChild(opt);
            });
        });
}

document.addEventListener("DOMContentLoaded", function () {

    // ── Фильтрация таблицы товаров ───────────────────────────────────────────
    var searchInput    = document.getElementById("search-input");
    var filterBrand    = document.getElementById("filter-brand");
    var filterSeason   = document.getElementById("filter-season");
    var filterTireType = document.getElementById("filter-tire-type");
    var filterSize     = document.getElementById("filter-size");

    function filterTable() {
        var query  = searchInput    ? searchInput.value.toLowerCase()  : "";
        var brand  = filterBrand    ? filterBrand.value.toLowerCase()  : "";
        var season = filterSeason   ? filterSeason.value               : "";
        var ttype  = filterTireType ? filterTireType.value             : "";
        var size   = filterSize     ? filterSize.value.toLowerCase()   : "";

        document.querySelectorAll("table tbody tr[data-search]").forEach(function(row) {
            var ok =
                (!query  || (row.dataset.search   || "").includes(query))  &&
                (!brand  || (row.dataset.brand    || "").includes(brand))  &&
                (!season || row.dataset.season    === season)              &&
                (!ttype  || row.dataset.tireType  === ttype)               &&
                (!size   || (row.dataset.size     || "").includes(size));
            row.style.display = ok ? "" : "none";
        });
    }

    [searchInput, filterBrand, filterSeason, filterTireType, filterSize].forEach(function(el) {
        if (el) el.addEventListener("input", filterTable);
    });

    // ── Форма "Создать адрес хранения" ──────────────────────────────────────
    var addrType    = document.getElementById("addr-type");
    var addrZone    = document.getElementById("zone_id");
    var addrRow     = document.getElementById("row_id");
    var addrShelf   = document.getElementById("shelf_id");
    var addrLevel   = document.getElementById("level_id");
    var addrShelfWrap = document.getElementById("shelf-row");
    var addrLevelWrap = document.getElementById("level-row");

    function toggleAddrFields() {
        if (!addrType) return;
        var ext = addrType.value === "zone_row_shelf_level";
        if (addrShelfWrap) addrShelfWrap.style.display = ext ? "" : "none";
        if (addrLevelWrap) addrLevelWrap.style.display = ext ? "" : "none";
    }
    if (addrType) { addrType.addEventListener("change", toggleAddrFields); toggleAddrFields(); }

    if (addrZone && addrRow) {
        addrZone.addEventListener("change", function() {
            if (this.value) {
                loadOptions("/api/rows?zone_id=" + this.value, addrRow, "выберите ряд");
                if (addrShelf) addrShelf.innerHTML = '<option value="">-- стеллаж --</option>';
                if (addrLevel) addrLevel.innerHTML = '<option value="">-- уровень --</option>';
            }
        });
    }
    if (addrRow && addrShelf) {
        addrRow.addEventListener("change", function() {
            if (this.value) loadOptions("/api/shelves?row_id=" + this.value, addrShelf, "стеллаж");
        });
    }
    if (addrShelf && addrLevel) {
        addrShelf.addEventListener("change", function() {
            if (this.value) loadOptions("/api/levels?shelf_id=" + this.value, addrLevel, "уровень");
        });
    }

    // ── Форма "Добавить стеллаж" ─────────────────────────────────────────────
    var shelfFormZone = document.getElementById("shelf-zone-select");
    var shelfFormRow  = document.getElementById("shelf-row-select");

    if (shelfFormZone && shelfFormRow) {
        shelfFormZone.addEventListener("change", function() {
            if (this.value) loadOptions("/api/rows?zone_id=" + this.value, shelfFormRow, "выберите ряд");
            else shelfFormRow.innerHTML = '<option value="">-- ряд --</option>';
        });

        // Загрузить ряды при открытии аккордеона (если зона уже выбрана)
        var colShelfEl = document.getElementById("colShelf");
        if (colShelfEl) {
            colShelfEl.addEventListener("show.bs.collapse", function() {
                if (shelfFormZone.value) {
                    loadOptions("/api/rows?zone_id=" + shelfFormZone.value, shelfFormRow, "выберите ряд");
                }
            });
        }
    }

    // ── Форма "Добавить уровень" ─────────────────────────────────────────────
    var levelFormZone  = document.getElementById("level-zone-select");
    var levelFormRow   = document.getElementById("level-row-select");
    var levelFormShelf = document.getElementById("level-shelf-select");

    if (levelFormZone && levelFormRow) {
        levelFormZone.addEventListener("change", function() {
            if (this.value) {
                loadOptions("/api/rows?zone_id=" + this.value, levelFormRow, "выберите ряд");
                if (levelFormShelf) levelFormShelf.innerHTML = '<option value="">-- стеллаж --</option>';
            } else {
                levelFormRow.innerHTML = '<option value="">-- ряд --</option>';
                if (levelFormShelf) levelFormShelf.innerHTML = '<option value="">-- стеллаж --</option>';
            }
        });

        var colLevelEl = document.getElementById("colLevel");
        if (colLevelEl) {
            colLevelEl.addEventListener("show.bs.collapse", function() {
                if (levelFormZone.value) {
                    loadOptions("/api/rows?zone_id=" + levelFormZone.value, levelFormRow, "выберите ряд");
                }
            });
        }
    }
    if (levelFormRow && levelFormShelf) {
        levelFormRow.addEventListener("change", function() {
            if (this.value) loadOptions("/api/shelves?row_id=" + this.value, levelFormShelf, "выберите стеллаж");
            else levelFormShelf.innerHTML = '<option value="">-- стеллаж --</option>';
        });
    }

    // ── Поиск товара в форме задания ─────────────────────────────────────────
    var productSearch = document.getElementById("product-search");
    if (productSearch) {
        productSearch.addEventListener("input", function() {
            var q = this.value.toLowerCase();
            document.querySelectorAll(".product-option").forEach(function(opt) {
                opt.style.display = (opt.dataset.search || "").includes(q) ? "" : "none";
            });
        });
    }

    // ── Confirm для опасных действий ─────────────────────────────────────────
    document.querySelectorAll("[data-confirm]").forEach(function(el) {
        el.addEventListener("click", function(e) {
            if (!confirm(this.dataset.confirm)) e.preventDefault();
        });
    });

    // ── Проблема toggle ──────────────────────────────────────────────────────
    var problemBtn  = document.getElementById("problem-toggle");
    var problemForm = document.getElementById("problem-form");
    if (problemBtn && problemForm) {
        problemBtn.addEventListener("click", function() {
            problemForm.style.display = problemForm.style.display === "none" ? "" : "none";
        });
    }

});
