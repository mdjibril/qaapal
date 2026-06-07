document.addEventListener('DOMContentLoaded', () => {
    // ----------------------------------------------------
    // 1. Pricing Toggle Logic
    // ----------------------------------------------------
    const billingToggle = document.getElementById('billing-toggle');
    const pricingCards = document.querySelectorAll('.pricing-card');

    const updatePricing = (isYearly) => {
        pricingCards.forEach(card => {
            const priceEl = card.querySelector('.price-value');
            const periodEl = card.querySelector('.price-period');
            const annualBillingEl = card.querySelector('.annual-billing-note');

            if (!priceEl) return;

            const monthlyPrice = parseFloat(card.getAttribute('data-price-monthly'));
            const yearlyPrice = parseFloat(card.getAttribute('data-price-yearly'));

            if (monthlyPrice === 0) {
                // Free plan remains free
                priceEl.textContent = '0';
                periodEl.textContent = '/forever';
                if (annualBillingEl) annualBillingEl.style.display = 'none';
            } else if (!isNaN(monthlyPrice)) {
                if (isYearly) {
                    priceEl.textContent = yearlyPrice;
                    periodEl.textContent = '/month';
                    if (annualBillingEl) {
                        const totalBilled = yearlyPrice * 12;
                        annualBillingEl.textContent = `Billed annually (₦${totalBilled.toLocaleString()}/yr)`;
                        annualBillingEl.style.display = 'block';
                    }
                } else {
                    priceEl.textContent = monthlyPrice;
                    periodEl.textContent = '/month';
                    if (annualBillingEl) annualBillingEl.style.display = 'none';
                }
            }
        });
    };

    if (billingToggle) {
        billingToggle.addEventListener('change', () => {
            updatePricing(billingToggle.checked);
        });
    }

    // ----------------------------------------------------
    // 2. BYOK Savings Calculator
    // ----------------------------------------------------
    const reportsSlider = document.getElementById('reports-slider');
    const reportsValue = document.getElementById('reports-value');
    const traditionalCostEl = document.getElementById('cost-traditional');
    const byokCostEl = document.getElementById('cost-byok');
    const savingsEl = document.getElementById('savings-value');

    const calculateSavings = () => {
        if (!reportsSlider) return;
        const reportsCount = parseInt(reportsSlider.value, 10);
        reportsValue.textContent = reportsCount;

        // Traditional SaaS model cost: let's estimate ₦1,000 per report generation
        const traditionalCost = reportsCount * 1000;

        // BYOK Model cost: ₦7,000 flat fee (Platform Pass) + average API usage cost (approx ₦30 per report)
        const byokCost = 7000 + (reportsCount * 30);

        // Savings
        const savings = Math.max(0, traditionalCost - byokCost);

        traditionalCostEl.textContent = `₦${traditionalCost.toLocaleString()}`;
        byokCostEl.textContent = `₦${byokCost.toLocaleString()}`;
        savingsEl.textContent = `₦${savings.toLocaleString()}`;
    };

    if (reportsSlider) {
        reportsSlider.addEventListener('input', calculateSavings);
        // Run once on load to initialize values
        calculateSavings();
    }

    // ----------------------------------------------------
    // 3. FAQ Accordion Logic (Smooth Height Transitions)
    // ----------------------------------------------------
    const faqItems = document.querySelectorAll('.faq-item');

    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        const answer = item.querySelector('.faq-answer');

        if (question && answer) {
            question.addEventListener('click', () => {
                const isOpen = item.classList.contains('active');
                
                // Close all other items first (optional, creates single-open accordion)
                faqItems.forEach(otherItem => {
                    if (otherItem !== item) {
                        otherItem.classList.remove('active');
                        const otherAnswer = otherItem.querySelector('.faq-answer');
                        if (otherAnswer) otherAnswer.style.maxHeight = null;
                    }
                });

                // Toggle current item
                if (isOpen) {
                    item.classList.remove('active');
                    answer.style.maxHeight = null;
                } else {
                    item.classList.add('active');
                    answer.style.maxHeight = answer.scrollHeight + 'px';
                }
            });
        }
    });

    // ----------------------------------------------------
    // 4. Mobile Navigation Toggle
    // ----------------------------------------------------
    const hamburgerMenu = document.getElementById('hamburger-menu');
    const navLinks = document.getElementById('nav-links');
    const navOverlay = document.getElementById('nav-overlay');

    const closeMenu = () => {
        hamburgerMenu.classList.remove('active');
        navLinks.classList.remove('active');
        navOverlay.classList.remove('active');
        hamburgerMenu.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
        document.documentElement.style.overflow = '';
    };

    const openMenu = () => {
        hamburgerMenu.classList.add('active');
        navLinks.classList.add('active');
        navOverlay.classList.add('active');
        hamburgerMenu.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden';
        document.documentElement.style.overflow = 'hidden';
    };

    if (hamburgerMenu && navLinks && navOverlay) {
        hamburgerMenu.addEventListener('click', () => {
            const isActive = hamburgerMenu.classList.contains('active');
            isActive ? closeMenu() : openMenu();
        });

        // Close menu when overlay is clicked
        navOverlay.addEventListener('click', closeMenu);

        // Close menu when a nav link is clicked
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', closeMenu);
        });
    }

    // ----------------------------------------------------
    // 5. Fixed Navbar Scroll Effect
    // ----------------------------------------------------
    const navbarWrapper = document.querySelector('.navbar-wrapper');
    if (navbarWrapper) {
        const handleScroll = () => {
            if (window.scrollY > 20) {
                navbarWrapper.classList.add('scrolled');
            } else {
                navbarWrapper.classList.remove('scrolled');
            }
        };
        window.addEventListener('scroll', handleScroll);
        // Run once on load to set initial state
        handleScroll();
    }
});
