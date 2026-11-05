document.querySelectorAll('.cart-page form').forEach(function (form) {
    form.addEventListener('submit', function () {
        form.querySelectorAll('button').forEach(function (button) {
            button.disabled = true;
        });
    });
});
