/**
 * CartMax Performance Monitoring and Optimization
 */

(function() {
    'use strict';

    // Performance monitoring
    const performance = window.performance;
    const CartMaxPerf = {
        // Track page load performance
        trackPageLoad: function() {
            if (!performance || !performance.timing) return;
            
            window.addEventListener('load', function() {
                setTimeout(function() {
                    const timing = performance.timing;
                    const metrics = {
                        pageLoad: timing.loadEventEnd - timing.navigationStart,
                        domReady: timing.domContentLoadedEventEnd - timing.navigationStart,
                        firstPaint: timing.responseStart - timing.navigationStart,
                        networkLatency: timing.responseEnd - timing.fetchStart
                    };
                    
                    console.log('CartMax Performance Metrics:', metrics);
                    
                    // Send to analytics if available
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'page_load_time', {
                            value: metrics.pageLoad,
                            custom_map: {
                                dom_ready: metrics.domReady,
                                first_paint: metrics.firstPaint
                            }
                        });
                    }
                }, 0);
            });
        },

        // Preload critical resources
        preloadResources: function() {
            const criticalResources = [
                { href: '/static/css/cartmax-modern.min.css', as: 'style' },
                { href: '/static/js/main.min.js', as: 'script' },
                { href: 'https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiA.woff2', as: 'font', crossorigin: 'anonymous' }
            ];

            criticalResources.forEach(function(resource) {
                const link = document.createElement('link');
                link.rel = 'preload';
                link.href = resource.href;
                link.as = resource.as;
                if (resource.crossorigin) link.crossOrigin = resource.crossorigin;
                document.head.appendChild(link);
            });
        },

        // Image lazy loading optimization
        optimizeImages: function() {
            // Add native lazy loading support
            const images = document.querySelectorAll('img:not([loading])');
            images.forEach(function(img) {
                if (img.offsetTop > window.innerHeight * 2) {
                    img.loading = 'lazy';
                }
            });

            // WebP support detection and fallback
            const supportsWebP = (function() {
                const canvas = document.createElement('canvas');
                canvas.width = 1;
                canvas.height = 1;
                return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
            })();

            if (supportsWebP) {
                document.documentElement.classList.add('webp');
            } else {
                document.documentElement.classList.add('no-webp');
            }
        },

        // Service Worker registration for caching
        registerServiceWorker: function() {
            if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                    navigator.serviceWorker.register('/sw.js')
                        .then(function(registration) {
                            console.log('ServiceWorker registration successful');
                        })
                        .catch(function(err) {
                            console.log('ServiceWorker registration failed');
                        });
                });
            }
        },

        // Critical CSS detection
        loadNonCriticalCSS: function() {
            const nonCriticalCSS = [
                '/static/css/print.css',
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css'
            ];

            nonCriticalCSS.forEach(function(href) {
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = href;
                link.media = 'print';
                link.onload = function() {
                    this.media = 'all';
                };
                document.head.appendChild(link);
            });
        },

        // Resource hints
        addResourceHints: function() {
            const hints = [
                { rel: 'dns-prefetch', href: '//fonts.googleapis.com' },
                { rel: 'dns-prefetch', href: '//fonts.gstatic.com' },
                { rel: 'dns-prefetch', href: '//cdn.jsdelivr.net' },
                { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
                { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: true }
            ];

            hints.forEach(function(hint) {
                const link = document.createElement('link');
                link.rel = hint.rel;
                link.href = hint.href;
                if (hint.crossorigin) link.crossOrigin = hint.crossorigin;
                document.head.appendChild(link);
            });
        },

        // Memory usage monitoring
        monitorMemory: function() {
            if (performance.memory) {
                const memoryInfo = {
                    used: Math.round(performance.memory.usedJSHeapSize / 1048576),
                    total: Math.round(performance.memory.totalJSHeapSize / 1048576),
                    limit: Math.round(performance.memory.jsHeapSizeLimit / 1048576)
                };
                console.log('Memory Usage (MB):', memoryInfo);
                
                // Warn if memory usage is high
                if (memoryInfo.used > 50) {
                    console.warn('High memory usage detected:', memoryInfo.used + 'MB');
                }
            }
        },

        // Network information
        checkNetworkStatus: function() {
            if ('connection' in navigator) {
                const connection = navigator.connection;
                const networkInfo = {
                    effectiveType: connection.effectiveType,
                    downlink: connection.downlink,
                    rtt: connection.rtt,
                    saveData: connection.saveData
                };
                
                console.log('Network Info:', networkInfo);
                
                // Adjust behavior based on connection
                if (connection.saveData || connection.effectiveType === '2g') {
                    document.documentElement.classList.add('slow-connection');
                    // Disable non-essential animations
                    const style = document.createElement('style');
                    style.textContent = `
                        .slow-connection * {
                            animation-duration: 0.01ms !important;
                            transition-duration: 0.01ms !important;
                        }
                    `;
                    document.head.appendChild(style);
                }
            }
        },

        // Initialize all performance optimizations
        init: function() {
            // Run immediately
            this.addResourceHints();
            this.optimizeImages();
            this.checkNetworkStatus();
            
            // Run on DOM ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', function() {
                    CartMaxPerf.preloadResources();
                    CartMaxPerf.loadNonCriticalCSS();
                });
            } else {
                this.preloadResources();
                this.loadNonCriticalCSS();
            }
            
            // Run on load
            this.trackPageLoad();
            this.registerServiceWorker();
            
            // Monitor memory every 30 seconds
            setInterval(this.monitorMemory, 30000);
        }
    };

    // Auto-initialize
    CartMaxPerf.init();

    // Expose to global scope
    window.CartMaxPerf = CartMaxPerf;

})();