const loading = document.querySelector('#page-loading');

document.querySelectorAll('form[role="search"]').forEach((form) => {
    form.addEventListener('submit', () => {
        if (loading) {
            loading.hidden = false;
        }
    });
});
