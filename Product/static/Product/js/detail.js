const detailRoot = document.querySelector('.product-detail');
const variantForm = document.querySelector('#variant-form');

if (detailRoot && variantForm) {
    const sizeOptions = document.querySelector('#size-options');
    const colorOptions = document.querySelector('#color-options');
    const variantSelect = document.querySelector('#variant-select');
    const price = document.querySelector('#variant-price');
    const sku = document.querySelector('#variant-sku');
    const stock = document.querySelector('#variant-stock');
    const quantity = document.querySelector('#quantity');
    const addButton = document.querySelector('#add-cart-button');
    const buyButton = document.querySelector('#buy-now-button');
    const mainImage = document.querySelector('#detail-main-image');
    let variants = [];
    let selectedSize = '';
    let selectedColor = '';

    const money = (value) => new Intl.NumberFormat('vi-VN').format(value) + '₫';
    const unique = (items) => [...new Set(items)];

    function makeOption(value, group, container) {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = value;
        button.dataset.value = value;
        button.addEventListener('click', () => {
            if (group === 'size') selectedSize = value;
            else selectedColor = value;
            container.querySelectorAll('button').forEach((item) => item.classList.toggle('is-active', item === button));
            updateVariant();
        });
        container.append(button);
    }

    function updateVariant() {
        const variant = variants.find((item) => item.size === selectedSize && item.color === selectedColor);
        variantSelect.value = variant ? variant.id : '';
        if (!variant) {
            sku.textContent = '—';
            stock.textContent = 'Chọn đủ size và màu sắc';
            quantity.disabled = true;
            addButton.disabled = true;
            buyButton.disabled = true;
            return;
        }
        sku.textContent = variant.sku;
        price.innerHTML = variant.sale_price < variant.price
            ? '<strong>' + money(variant.sale_price) + '</strong><del>' + money(variant.price) + '</del>'
            : '<strong>' + money(variant.price) + '</strong>';
        stock.textContent = variant.stock > 0 ? 'Còn ' + variant.stock + ' sản phẩm' : 'Hết hàng';
        quantity.max = variant.stock;
        quantity.value = 1;
        quantity.disabled = variant.stock <= 0;
        addButton.disabled = variant.stock <= 0;
        buyButton.disabled = variant.stock <= 0;
        if (variant.image) mainImage.src = variant.image;
    }

    fetch(detailRoot.dataset.variantsUrl)
        .then((response) => response.json())
        .then((data) => {
            variants = data.variants;
            variantSelect.closest('.fallback-variant').classList.add('is-enhanced');
            unique(variants.map((item) => item.size)).forEach((value) => makeOption(value, 'size', sizeOptions));
            unique(variants.map((item) => item.color)).forEach((value) => makeOption(value, 'color', colorOptions));
            const firstAvailable = variants.find((item) => item.stock > 0) || variants[0];
            if (firstAvailable) {
                sizeOptions.querySelector(`[data-value="${CSS.escape(firstAvailable.size)}"]`)?.click();
                colorOptions.querySelector(`[data-value="${CSS.escape(firstAvailable.color)}"]`)?.click();
            }
        });

    variantSelect.addEventListener('change', () => {
        const variant = variants.find((item) => String(item.id) === variantSelect.value);
        if (variant) {
            selectedSize = variant.size;
            selectedColor = variant.color;
            updateVariant();
        }
    });
}

document.querySelectorAll('.product-detail__thumbnails button').forEach((button) => {
    button.addEventListener('click', () => {
        document.querySelector('#detail-main-image').src = button.dataset.image;
        document.querySelectorAll('.product-detail__thumbnails button').forEach((item) => item.classList.toggle('is-active', item === button));
    });
});
