function initColorSelection() {
    const pillsContainer = document.getElementById("color-pills");
    const hiddenColor = document.getElementById("color_name");
    if (!pillsContainer || !hiddenColor) return;

    pillsContainer.querySelectorAll(".color-pill").forEach((pill, index) => {
        pill.addEventListener("click", () => {
            pillsContainer.querySelectorAll(".color-pill").forEach((p) => p.classList.remove("selected"));
            pill.classList.add("selected");
            hiddenColor.value = pill.dataset.color || "";
        });
        if (index === 0) {
            pill.classList.add("selected");
            hiddenColor.value = pill.dataset.color || "";
        }
    });
}

function initPurchaseAjax() {
    const form = document.getElementById("purchase-form");
    if (!form) return;

    const feedback = document.getElementById("purchase-feedback");
    const stockCount = document.getElementById("stock-count");
    const quantityInput = document.getElementById("quantity-input");
    const addressInput = form.querySelector("input[name='shipping_address']");
    const buyNowBtn = document.getElementById("buy-now-btn");
    const validationMsg = document.getElementById("purchase-validation");

    const getCurrentStock = () => Number(quantityInput?.max || 0);

    const validatePurchaseForm = () => {
        if (!quantityInput || !addressInput || !buyNowBtn) return false;

        const stock = getCurrentStock();
        const qty = Number(quantityInput.value);
        const address = addressInput.value.trim();
        let message = "";

        if (stock <= 0) {
            message = "Out of stock.";
        } else if (!Number.isFinite(qty) || qty < 1) {
            message = "Quantity must be at least 1.";
        } else if (qty > stock) {
            message = `Only ${stock} item(s) left in stock.`;
        } else if (!address) {
            message = "Please enter shipping address.";
        }

        const isInvalid = message !== "";
        buyNowBtn.disabled = isInvalid;

        if (validationMsg) {
            validationMsg.textContent = message;
        }

        return !isInvalid;
    };

    quantityInput?.addEventListener("input", validatePurchaseForm);
    quantityInput?.addEventListener("change", validatePurchaseForm);
    addressInput?.addEventListener("input", validatePurchaseForm);
    validatePurchaseForm();

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!validatePurchaseForm()) return;

        const formData = new FormData(form);
        const response = await fetch(form.action, {
            method: "POST",
            headers: { "X-Requested-With": "XMLHttpRequest" },
            body: formData,
        });
        const data = await response.json();

        if (!feedback) return;

        if (!data.ok) {
            feedback.textContent = data.message;
            feedback.style.color = "#8a4f50";
            return;
        }

        feedback.textContent = `${data.message} Order #${data.order_id}.`;
        feedback.style.color = "#2b5d4b";

        if (typeof data.new_stock === "number" && stockCount) {
            stockCount.innerHTML = `<strong>Stock:</strong> ${data.new_stock}`;
            if (quantityInput) {
                quantityInput.max = String(data.new_stock);
                if (Number(quantityInput.value) > data.new_stock) {
                    quantityInput.value = data.new_stock > 0 ? "1" : "0";
                }
            }
        }

        validatePurchaseForm();
    });
}

function initDeleteConfirm() {
    const modal = document.getElementById("deleteConfirmModal");
    const modalMessage = document.getElementById("delete-confirm-message");
    const cancelBtn = document.getElementById("delete-confirm-cancel");
    const confirmBtn = document.getElementById("delete-confirm-submit");
    if (!modal || !modalMessage || !cancelBtn || !confirmBtn) return;

    let pendingForm = null;

    const openModal = (form) => {
        pendingForm = form;
        const message =
            form.getAttribute("data-confirm-message") ||
            "Are you sure you want to delete this item?";
        modalMessage.textContent = message;
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
    };

    const closeModal = () => {
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
        pendingForm = null;
    };

    document.querySelectorAll(".delete-form").forEach((form) => {
        form.addEventListener("submit", (event) => {
            event.preventDefault();
            openModal(form);
        });
    });

    cancelBtn.addEventListener("click", closeModal);

    confirmBtn.addEventListener("click", () => {
        if (!pendingForm) return;
        pendingForm.submit();
    });

    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && modal.classList.contains("is-open")) {
            closeModal();
        }
    });
}

function initMerchantCharts() {
    if (!window.Chart || !window.merchantChartsData) return;
    const data = window.merchantChartsData;

    const salesCanvas = document.getElementById("salesTrendChart");
    if (salesCanvas) {
        new Chart(salesCanvas, {
            type: "line",
            data: {
                labels: data.salesLabels.length ? data.salesLabels : ["No sales yet"],
                datasets: [
                    {
                        label: "Revenue ($)",
                        data: data.salesValues.length ? data.salesValues : [0],
                        borderColor: "#50808e",
                        backgroundColor: "rgba(80, 128, 142, 0.2)",
                        tension: 0.3,
                        fill: true,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
            },
        });
    }

    const categoryCanvas = document.getElementById("categoryPieChart");
    if (categoryCanvas) {
        new Chart(categoryCanvas, {
            type: "pie",
            data: {
                labels: data.categoryLabels.length ? data.categoryLabels : ["No category data"],
                datasets: [
                    {
                        data: data.categoryValues.length ? data.categoryValues : [1],
                        backgroundColor: ["#a3c9a8", "#84b59f", "#69a297", "#50808e", "#ddd8c4"],
                        borderColor: "#f3f0e5",
                        borderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
            },
        });
    }

    const topCanvas = document.getElementById("topProductChart");
    if (topCanvas) {
        new Chart(topCanvas, {
            type: "bar",
            data: {
                labels: data.topLabels.length ? data.topLabels : ["No sales yet"],
                datasets: [
                    {
                        label: "Revenue ($)",
                        data: data.topValues.length ? data.topValues : [0],
                        backgroundColor: "#69a297",
                        borderRadius: 6,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true },
                },
            },
        });
    }
}

function initCategorySelector() {
    const categorySelect = document.getElementById("category_select");
    const newCategoryRow = document.getElementById("new-category-row");
    const newCategoryInput = document.getElementById("new_category_input");

    if (!categorySelect || !newCategoryRow || !newCategoryInput) return;

    const updateCategoryInput = () => {
        const isNew = categorySelect.value === "__new__";
        newCategoryRow.classList.toggle("hidden", !isNew);
        newCategoryInput.required = isNew;
        if (!isNew) {
            newCategoryInput.value = "";
        }
    };

    categorySelect.addEventListener("change", updateCategoryInput);
    updateCategoryInput();
}

function initProductImageFallback() {
    const fallbackSrc = "/static/images/product_default.png";
    document.querySelectorAll("[data-fallback-target='product-image']").forEach((img) => {
        img.addEventListener("error", () => {
            if (img.dataset.fallbackApplied === "true") return;
            img.dataset.fallbackApplied = "true";
            img.classList.add("is-fallback-image");
            img.src = fallbackSrc;
        });
    });
}

function initLongTextPreview() {
    const modal = document.getElementById("textPreviewModal");
    const titleEl = document.getElementById("text-preview-title");
    const contentEl = document.getElementById("text-preview-content");
    const closeBtn = document.getElementById("text-preview-close");
    if (!modal || !titleEl || !contentEl || !closeBtn) return;

    const closeModal = () => {
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
        contentEl.textContent = "";
    };

    document.querySelectorAll(".longtext-open").forEach((btn) => {
        btn.addEventListener("click", () => {
            const title = btn.getAttribute("data-longtext-title") || "Details";
            const text = btn.getAttribute("data-longtext-content") || "";
            titleEl.textContent = title;
            contentEl.textContent = text;
            modal.classList.add("is-open");
            modal.setAttribute("aria-hidden", "false");
        });
    });

    closeBtn.addEventListener("click", closeModal);
    modal.addEventListener("click", (event) => {
        if (event.target === modal) closeModal();
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && modal.classList.contains("is-open")) {
            closeModal();
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initColorSelection();
    initPurchaseAjax();
    initDeleteConfirm();
    initMerchantCharts();
    initCategorySelector();
    initProductImageFallback();
    initLongTextPreview();
});
