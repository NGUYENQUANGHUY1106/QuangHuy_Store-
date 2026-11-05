function getCookie(name) {
    return document.cookie.split('; ').find(function (row) { return row.startsWith(name + '='); })?.split('=')[1];
}
document.querySelectorAll('.wishlist-toggle').forEach(function (button) {
    button.addEventListener('click', function () {
        fetch(button.dataset.url, {method: 'POST', headers: {'X-CSRFToken': getCookie('csrftoken') || ''}})
            .then(function (response) { if (response.status === 401) { window.location.href = '/login/'; } return response.json(); })
            .then(function (data) { if (data.success) { button.classList.toggle('is-active', data.added); button.textContent = data.added ? '♥' : '♡'; } });
    });
});
