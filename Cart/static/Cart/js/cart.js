document.querySelectorAll('.cart-page form:not(.quantity-form)').forEach(function (form) {
    form.addEventListener('submit', function () {
        form.querySelectorAll('button').forEach(function (button) {
            button.disabled = true;
        });
    });
});

document.querySelectorAll('.quantity-form input[name="quantity"]').forEach(function (input) {
    let timer;
    input.addEventListener('input', function () {
        clearTimeout(timer);
        const form = input.closest('form');
        const status = form.querySelector('.quantity-saving');
        const quantity = Number(input.value);
        if (!Number.isInteger(quantity) || quantity < Number(input.min) || quantity > Number(input.max)) {
            status.textContent = 'Số lượng không hợp lệ';
            return;
        }
        status.textContent = 'Đang cập nhật...';
        timer = setTimeout(function () {
            form.requestSubmit();
        }, 350);
    });
});
