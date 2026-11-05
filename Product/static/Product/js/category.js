const filterForm = document.querySelector('#category-filter-form');
const categoryLoading = document.querySelector('#category-loading');
const filterPanel = document.querySelector('.filter-panel');

if (filterPanel && window.matchMedia('(max-width: 900px)').matches) {
    filterPanel.removeAttribute('open');
}

if (filterForm && categoryLoading) {
    filterForm.addEventListener('submit', () => {
        categoryLoading.hidden = false;
    });
}
