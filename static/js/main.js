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

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

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
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initColorSelection();
    initPurchaseAjax();
});
