const shippingBox = document.getElementById('shipping-options');
const subtotalElement = document.getElementById('checkout-subtotal');

function money(value) {
    return new Intl.NumberFormat('vi-VN').format(value) + 'đ';
}

function updateTotal(fee) {
    const subtotal = Number(subtotalElement.dataset.value || 0);
    document.getElementById('shipping-fee').textContent = money(fee);
    document.getElementById('checkout-total').textContent = money(subtotal + fee);
}

function bindShippingOptions() {
    const options = shippingBox.querySelectorAll('input[name="shipping_method"]');
    options.forEach(function (option) {
        option.addEventListener('change', function () {
            updateTotal(Number(option.dataset.fee || 0));
        });
    });
    const selected = shippingBox.querySelector('input[name="shipping_method"]:checked');
    updateTotal(selected ? Number(selected.dataset.fee || 0) : 0);
}

document.querySelectorAll('input[name="address_id"]').forEach(function (address) {
    address.addEventListener('change', async function () {
        shippingBox.innerHTML = '<p>Đang tính phí vận chuyển...</p>';
        const response = await fetch(shippingBox.dataset.url + '?address_id=' + encodeURIComponent(address.value));
        const data = await response.json();
        if (!response.ok || !data.options.length) {
            shippingBox.innerHTML = '<p>Địa chỉ này chưa có phương thức giao hàng.</p>';
            updateTotal(0);
            return;
        }
        shippingBox.innerHTML = data.options.map(function (option, index) {
            return '<label class="option-card"><input type="radio" name="shipping_method" value="' +
                option.code + '" data-fee="' + option.fee + '" ' + (index === 0 ? 'checked' : '') +
                ' required><span><strong>' + option.name + ' — ' + money(option.fee) +
                '</strong><small>Dự kiến ' + option.eta + '</small></span></label>';
        }).join('');
        bindShippingOptions();
    });
});

if (shippingBox && subtotalElement) {
    bindShippingOptions();
}
