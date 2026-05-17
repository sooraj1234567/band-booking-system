/**
 * BandSphere Premium Interactive & Animations Engine
 * Provides ultra-smooth micro-interactions, scroll reveals, and high-fidelity physics transitions.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Scroll-Responsive Navbar
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        const handleScroll = () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        };
        window.addEventListener('scroll', handleScroll);
        handleScroll(); // Check initial state
    }

    // 2. High-Performance Intersection Observer for Smooth Scroll Reveals
    const revealElements = document.querySelectorAll('.band-card, .glass-panel, .stat-card, .review-card, .section-header, .form-box');
    
    // Set initial styles for reveal elements if not already set by CSS
    revealElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.8s cubic-bezier(0.16, 1, 0.3, 1)';
    });

    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Add a small delay based on index or just simple staggered reveal
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, 100);
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.05,
        rootMargin: '0px 0px -50px 0px'
    });

    revealElements.forEach(el => {
        revealObserver.observe(el);
    });

    // 3. Premium 3D Tilt Effect on Band Cards
    const cards = document.querySelectorAll('.band-card');
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left; // x coordinate inside the element
            const y = e.clientY - rect.top;  // y coordinate inside the element
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            // Calculate rotation values (-10deg to 10deg max)
            const rotateX = ((centerY - y) / centerY) * 10;
            const rotateY = ((x - centerX) / centerX) * 10;
            
            // Calculate gradient overlay position
            const inner = card.querySelector('.glass-panel');
            if (inner) {
                inner.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
                inner.style.boxShadow = `
                    ${-rotateY * 2}px ${rotateX * 2}px 30px rgba(0, 242, 254, 0.15),
                    0 15px 35px rgba(0, 0, 0, 0.5)
                `;
            }
        });

        card.addEventListener('mouseleave', () => {
            const inner = card.querySelector('.glass-panel');
            if (inner) {
                inner.style.transform = 'rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
                inner.style.boxShadow = '0 8px 32px 0 rgba(0, 0, 0, 0.4)';
            }
        });
    });

    // 4. Mouse-Track Background Glow (Sleek Desktop Experience)
    if (window.innerWidth > 768) {
        const glowBlob = document.createElement('div');
        glowBlob.className = 'blob blob-interactive';
        glowBlob.style.cssText = `
            position: fixed;
            width: 350px;
            height: 350px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(0, 242, 254, 0.08) 0%, rgba(155, 81, 224, 0.02) 70%, transparent 100%);
            pointer-events: none;
            z-index: -1;
            filter: blur(40px);
            opacity: 0;
            transition: opacity 0.5s ease;
            transform: translate(-50%, -50%);
        `;
        document.body.appendChild(glowBlob);

        window.addEventListener('mousemove', (e) => {
            glowBlob.style.opacity = '1';
            glowBlob.style.left = e.clientX + 'px';
            glowBlob.style.top = e.clientY + 'px';
        });

        document.addEventListener('mouseleave', () => {
            glowBlob.style.opacity = '0';
        });
    }

    // 5. Button Click Wave Effect (Micro-interaction ripple)
    const buttons = document.querySelectorAll('.glass-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const x = e.clientX - e.target.getBoundingClientRect().left;
            const y = e.clientY - e.target.getBoundingClientRect().top;
            
            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                width: 0;
                height: 0;
                transform: translate(-50%, -50%);
                pointer-events: none;
                animation: rippleEffect 0.6s linear;
                left: ${x}px;
                top: ${y}px;
            `;
            
            // Add custom animation style keyframe to document head if not exists
            if (!document.getElementById('ripple-animation-style')) {
                const style = document.createElement('style');
                style.id = 'ripple-animation-style';
                style.innerHTML = `
                    @keyframes rippleEffect {
                        to {
                            width: 300px;
                            height: 300px;
                            opacity: 0;
                        }
                    }
                `;
                document.head.appendChild(style);
            }
            
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });

    // 6. Smooth Page Entry Transition
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.6s ease-in-out';
    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 50);
});
