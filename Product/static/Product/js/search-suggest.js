const searchForm = document.querySelector('.header-search');
const searchInput = document.querySelector('#header-search-input');
const suggestionBox = document.querySelector('#search-suggestions');
let suggestionTimer;

function formatPrice(value) {
    return new Intl.NumberFormat('vi-VN').format(value) + '₫';
}

function closeSuggestions() {
    if (suggestionBox) suggestionBox.hidden = true;
}

function renderSuggestions(results) {
    suggestionBox.replaceChildren();
    if (!results.length) {
        const message = document.createElement('p');
        message.className = 'suggestion-message';
        message.textContent = 'Không tìm thấy sản phẩm phù hợp.';
        suggestionBox.append(message);
    }

    results.forEach((product) => {
        const link = document.createElement('a');
        link.className = 'suggestion-item';
        link.href = product.url;

        const image = document.createElement('img');
        image.src = product.image || '/static/Product/images/product-placeholder.svg';
        image.alt = '';

        const content = document.createElement('span');
        const name = document.createElement('strong');
        name.textContent = product.name;
        const meta = document.createElement('small');
        meta.textContent = product.brand + ' · Từ ' + formatPrice(product.price);
        content.append(name, meta);
        link.append(image, content);
        suggestionBox.append(link);
    });
    suggestionBox.hidden = false;
}

if (searchForm && searchInput && suggestionBox) {
    searchInput.addEventListener('input', () => {
        clearTimeout(suggestionTimer);
        const query = searchInput.value.trim();
        if (query.length < 2) {
            closeSuggestions();
            return;
        }

        suggestionTimer = setTimeout(async () => {
            const url = searchForm.dataset.suggestUrl + '?q=' + encodeURIComponent(query);
            try {
                const response = await fetch(url, {headers: {'X-Requested-With': 'XMLHttpRequest'}});
                if (!response.ok) return closeSuggestions();
                const data = await response.json();
                if (searchInput.value.trim() === query) renderSuggestions(data.results);
            } catch (error) {
                closeSuggestions();
            }
        }, 300);
    });

    searchForm.addEventListener('submit', () => {
        const query = searchInput.value.trim();
        if (query) {
            const history = JSON.parse(localStorage.getItem('product_search_history') || '[]');
            localStorage.setItem('product_search_history', JSON.stringify([query, ...history.filter((item) => item !== query)].slice(0, 5)));
        }
    });

    document.addEventListener('click', (event) => {
        if (!searchForm.contains(event.target)) closeSuggestions();
    });

    searchInput.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') closeSuggestions();
    });
}
