# APM User Experience Monitoring

User Experience Monitoring (UEM) provides insights into real user interactions with applications, measuring performance from the end-user perspective. This guide covers Real User Monitoring (RUM), synthetic monitoring, Core Web Vitals tracking, user journey analysis, and enterprise-grade UX monitoring implementations essential for optimizing application performance and user satisfaction.

## Real User Monitoring (RUM) Framework

### Client-Side Performance Tracking

```javascript
// real-user-monitoring.js - Comprehensive RUM implementation

class RealUserMonitoring {
    constructor(config = {}) {
        this.config = {
            apiEndpoint: config.apiEndpoint || '/api/rum',
            sampleRate: config.sampleRate || 1.0, // 100% by default
            bufferSize: config.bufferSize || 100,
            flushInterval: config.flushInterval || 5000, // 5 seconds
            enableAutoCapture: config.enableAutoCapture !== false,
            captureErrors: config.captureErrors !== false,
            captureResources: config.captureResources !== false,
            captureUserInteractions: config.captureUserInteractions !== false,
            enableHeatmap: config.enableHeatmap || false,
            ...config
        };
        
        this.sessionId = this.generateSessionId();
        this.userId = config.userId || this.generateUserId();
        this.buffer = [];
        this.startTime = performance.now();
        this.pageLoadStartTime = performance.timing.navigationStart;
        
        this.init();
    }
    
    init() {
        if (Math.random() > this.config.sampleRate) {
            return; // Skip monitoring based on sample rate
        }
        
        this.setupPerformanceObserver();
        this.capturePageLoad();
        
        if (this.config.enableAutoCapture) {
            this.setupAutoCapture();
        }
        
        if (this.config.captureErrors) {
            this.setupErrorCapture();
        }
        
        if (this.config.captureUserInteractions) {
            this.setupUserInteractionCapture();
        }
        
        if (this.config.enableHeatmap) {
            this.setupHeatmapCapture();
        }
        
        this.startPeriodicFlush();
        this.setupPageUnloadCapture();
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    generateUserId() {
        let userId = localStorage.getItem('rum_user_id');
        if (!userId) {
            userId = 'user_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('rum_user_id', userId);
        }
        return userId;
    }
    
    setupPerformanceObserver() {
        // Observe navigation timing
        if ('PerformanceObserver' in window) {
            // Observe paint timings
            try {
                const paintObserver = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        this.addMetric({
                            type: 'paint',
                            name: entry.name,
                            startTime: entry.startTime,
                            duration: entry.duration || 0,
                            timestamp: Date.now()
                        });
                    }
                });
                paintObserver.observe({ entryTypes: ['paint'] });
            } catch (e) {
                console.warn('Paint observer not supported:', e);
            }
            
            // Observe largest contentful paint
            try {
                const lcpObserver = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    
                    this.addMetric({
                        type: 'lcp',
                        name: 'largest-contentful-paint',
                        startTime: lastEntry.startTime,
                        size: lastEntry.size,
                        element: lastEntry.element?.tagName?.toLowerCase(),
                        url: lastEntry.url,
                        timestamp: Date.now()
                    });
                });
                lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
            } catch (e) {
                console.warn('LCP observer not supported:', e);
            }
            
            // Observe layout shifts
            try {
                const clsObserver = new PerformanceObserver((list) => {
                    let clsValue = 0;
                    for (const entry of list.getEntries()) {
                        if (!entry.hadRecentInput) {
                            clsValue += entry.value;
                        }
                    }
                    
                    if (clsValue > 0) {
                        this.addMetric({
                            type: 'cls',
                            name: 'cumulative-layout-shift',
                            value: clsValue,
                            timestamp: Date.now()
                        });
                    }
                });
                clsObserver.observe({ entryTypes: ['layout-shift'] });
            } catch (e) {
                console.warn('CLS observer not supported:', e);
            }
            
            // Observe first input delay
            try {
                const fidObserver = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        this.addMetric({
                            type: 'fid',
                            name: 'first-input-delay',
                            startTime: entry.startTime,
                            processingStart: entry.processingStart,
                            duration: entry.duration,
                            inputDelay: entry.processingStart - entry.startTime,
                            timestamp: Date.now()
                        });
                    }
                });
                fidObserver.observe({ entryTypes: ['first-input'] });
            } catch (e) {
                console.warn('FID observer not supported:', e);
            }
            
            // Observe resources
            if (this.config.captureResources) {
                try {
                    const resourceObserver = new PerformanceObserver((list) => {
                        for (const entry of list.getEntries()) {
                            this.addMetric({
                                type: 'resource',
                                name: entry.name,
                                initiatorType: entry.initiatorType,
                                duration: entry.duration,
                                transferSize: entry.transferSize,
                                encodedBodySize: entry.encodedBodySize,
                                decodedBodySize: entry.decodedBodySize,
                                startTime: entry.startTime,
                                timestamp: Date.now()
                            });
                        }
                    });
                    resourceObserver.observe({ entryTypes: ['resource'] });
                } catch (e) {
                    console.warn('Resource observer not supported:', e);
                }
            }
        }
    }
    
    capturePageLoad() {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const navigation = performance.getEntriesByType('navigation')[0];
                const paintEntries = performance.getEntriesByType('paint');
                
                const pageLoadMetrics = {
                    type: 'page_load',
                    url: window.location.href,
                    title: document.title,
                    referrer: document.referrer,
                    userAgent: navigator.userAgent,
                    viewport: {
                        width: window.innerWidth,
                        height: window.innerHeight
                    },
                    screen: {
                        width: screen.width,
                        height: screen.height,
                        colorDepth: screen.colorDepth
                    },
                    connection: this.getConnectionInfo(),
                    timing: {},
                    timestamp: Date.now()
                };
                
                if (navigation) {
                    pageLoadMetrics.timing = {
                        navigationStart: 0,
                        unloadEventStart: navigation.unloadEventStart - navigation.navigationStart,
                        unloadEventEnd: navigation.unloadEventEnd - navigation.navigationStart,
                        redirectStart: navigation.redirectStart - navigation.navigationStart,
                        redirectEnd: navigation.redirectEnd - navigation.navigationStart,
                        fetchStart: navigation.fetchStart - navigation.navigationStart,
                        domainLookupStart: navigation.domainLookupStart - navigation.navigationStart,
                        domainLookupEnd: navigation.domainLookupEnd - navigation.navigationStart,
                        connectStart: navigation.connectStart - navigation.navigationStart,
                        connectEnd: navigation.connectEnd - navigation.navigationStart,
                        secureConnectionStart: navigation.secureConnectionStart - navigation.navigationStart,
                        requestStart: navigation.requestStart - navigation.navigationStart,
                        responseStart: navigation.responseStart - navigation.navigationStart,
                        responseEnd: navigation.responseEnd - navigation.navigationStart,
                        domLoading: navigation.domLoading - navigation.navigationStart,
                        domInteractive: navigation.domInteractive - navigation.navigationStart,
                        domContentLoadedEventStart: navigation.domContentLoadedEventStart - navigation.navigationStart,
                        domContentLoadedEventEnd: navigation.domContentLoadedEventEnd - navigation.navigationStart,
                        domComplete: navigation.domComplete - navigation.navigationStart,
                        loadEventStart: navigation.loadEventStart - navigation.navigationStart,
                        loadEventEnd: navigation.loadEventEnd - navigation.navigationStart
                    };
                    
                    // Calculate key metrics
                    pageLoadMetrics.calculated = {
                        ttfb: navigation.responseStart - navigation.requestStart, // Time to First Byte
                        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.navigationStart,
                        windowLoad: navigation.loadEventEnd - navigation.navigationStart,
                        firstPaint: paintEntries.find(e => e.name === 'first-paint')?.startTime || 0,
                        firstContentfulPaint: paintEntries.find(e => e.name === 'first-contentful-paint')?.startTime || 0
                    };
                }
                
                this.addMetric(pageLoadMetrics);
            }, 0);
        });
    }
    
    getConnectionInfo() {
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        if (connection) {
            return {
                effectiveType: connection.effectiveType,
                downlink: connection.downlink,
                rtt: connection.rtt,
                saveData: connection.saveData
            };
        }
        return null;
    }
    
    setupAutoCapture() {
        // Capture route changes (for SPAs)
        this.setupRouteChangeCapture();
        
        // Capture AJAX requests
        this.setupAjaxCapture();
        
        // Capture console errors
        this.setupConsoleErrorCapture();
    }
    
    setupRouteChangeCapture() {
        // Handle pushState/popState for SPAs
        const originalPushState = history.pushState;
        const originalPopState = history.popState;
        
        const captureRouteChange = (type, url) => {
            this.addMetric({
                type: 'route_change',
                changeType: type,
                from: this.currentUrl || window.location.href,
                to: url,
                timestamp: Date.now()
            });
            this.currentUrl = url;
        };
        
        history.pushState = function(state, title, url) {
            const result = originalPushState.apply(this, arguments);
            captureRouteChange('pushstate', url);
            return result;
        };
        
        window.addEventListener('popstate', (event) => {
            captureRouteChange('popstate', window.location.href);
        });
        
        this.currentUrl = window.location.href;
    }
    
    setupAjaxCapture() {
        // Monkey patch XMLHttpRequest
        const originalXHROpen = XMLHttpRequest.prototype.open;
        const originalXHRSend = XMLHttpRequest.prototype.send;
        
        XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
            this._rumStartTime = performance.now();
            this._rumMethod = method;
            this._rumUrl = url;
            return originalXHROpen.apply(this, arguments);
        };
        
        XMLHttpRequest.prototype.send = function(body) {
            const xhr = this;
            const startTime = this._rumStartTime;
            
            xhr.addEventListener('loadend', function() {
                const endTime = performance.now();
                const duration = endTime - startTime;
                
                window.rumInstance?.addMetric({
                    type: 'xhr',
                    method: xhr._rumMethod,
                    url: xhr._rumUrl,
                    status: xhr.status,
                    statusText: xhr.statusText,
                    duration: duration,
                    responseSize: xhr.responseText?.length || 0,
                    timestamp: Date.now()
                });
            });
            
            return originalXHRSend.apply(this, arguments);
        };
        
        // Monkey patch fetch
        if (window.fetch) {
            const originalFetch = window.fetch;
            window.fetch = function(input, init = {}) {
                const startTime = performance.now();
                const url = typeof input === 'string' ? input : input.url;
                const method = init.method || 'GET';
                
                return originalFetch.apply(this, arguments).then(response => {
                    const endTime = performance.now();
                    const duration = endTime - startTime;
                    
                    window.rumInstance?.addMetric({
                        type: 'fetch',
                        method: method,
                        url: url,
                        status: response.status,
                        statusText: response.statusText,
                        duration: duration,
                        timestamp: Date.now()
                    });
                    
                    return response;
                });
            };
        }
        
        window.rumInstance = this;
    }
    
    setupErrorCapture() {
        window.addEventListener('error', (event) => {
            this.addMetric({
                type: 'javascript_error',
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack,
                timestamp: Date.now()
            });
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.addMetric({
                type: 'unhandled_promise_rejection',
                reason: event.reason?.toString() || 'Unknown promise rejection',
                stack: event.reason?.stack,
                timestamp: Date.now()
            });
        });
    }
    
    setupConsoleErrorCapture() {
        const originalConsoleError = console.error;
        console.error = function(...args) {
            window.rumInstance?.addMetric({
                type: 'console_error',
                message: args.join(' '),
                timestamp: Date.now()
            });
            return originalConsoleError.apply(this, arguments);
        };
    }
    
    setupUserInteractionCapture() {
        // Capture clicks
        document.addEventListener('click', (event) => {
            const element = event.target;
            const elementInfo = this.getElementInfo(element);
            
            this.addMetric({
                type: 'click',
                element: elementInfo,
                coordinates: { x: event.clientX, y: event.clientY },
                timestamp: Date.now()
            });
        }, true);
        
        // Capture form submissions
        document.addEventListener('submit', (event) => {
            const form = event.target;
            const formInfo = this.getElementInfo(form);
            
            this.addMetric({
                type: 'form_submit',
                form: formInfo,
                timestamp: Date.now()
            });
        }, true);
        
        // Capture scroll events (throttled)
        let scrollTimeout;
        document.addEventListener('scroll', (event) => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                this.addMetric({
                    type: 'scroll',
                    scrollY: window.scrollY,
                    scrollX: window.scrollX,
                    timestamp: Date.now()
                });
            }, 100);
        }, true);
    }
    
    setupHeatmapCapture() {
        let heatmapData = [];
        
        document.addEventListener('click', (event) => {
            heatmapData.push({
                x: event.clientX,
                y: event.clientY,
                timestamp: Date.now()
            });
            
            // Send heatmap data periodically
            if (heatmapData.length >= 50) {
                this.addMetric({
                    type: 'heatmap_clicks',
                    data: heatmapData,
                    viewport: {
                        width: window.innerWidth,
                        height: window.innerHeight
                    },
                    timestamp: Date.now()
                });
                heatmapData = [];
            }
        });
        
        // Send remaining heatmap data on page unload
        window.addEventListener('beforeunload', () => {
            if (heatmapData.length > 0) {
                this.addMetric({
                    type: 'heatmap_clicks',
                    data: heatmapData,
                    viewport: {
                        width: window.innerWidth,
                        height: window.innerHeight
                    },
                    timestamp: Date.now()
                });
            }
        });
    }
    
    getElementInfo(element) {
        return {
            tagName: element.tagName?.toLowerCase(),
            id: element.id,
            className: element.className,
            textContent: element.textContent?.substring(0, 100),
            href: element.href,
            src: element.src,
            xpath: this.getXPath(element)
        };
    }
    
    getXPath(element) {
        if (element.id !== '') {
            return `//*[@id="${element.id}"]`;
        }
        if (element === document.body) {
            return '/html/body';
        }
        
        let ix = 0;
        const siblings = element.parentNode?.childNodes || [];
        for (let i = 0; i < siblings.length; i++) {
            const sibling = siblings[i];
            if (sibling === element) {
                return this.getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
            }
            if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                ix++;
            }
        }
        return '';
    }
    
    setupPageUnloadCapture() {
        window.addEventListener('beforeunload', () => {
            this.addMetric({
                type: 'page_unload',
                url: window.location.href,
                sessionDuration: performance.now() - this.startTime,
                timestamp: Date.now()
            });
            this.flushBuffer(true); // Synchronous flush on unload
        });
        
        // Capture visibility changes
        document.addEventListener('visibilitychange', () => {
            this.addMetric({
                type: 'visibility_change',
                visibilityState: document.visibilityState,
                hidden: document.hidden,
                timestamp: Date.now()
            });
        });
    }
    
    addMetric(metric) {
        // Add session and user context
        const enrichedMetric = {
            ...metric,
            sessionId: this.sessionId,
            userId: this.userId,
            url: window.location.href,
            userAgent: navigator.userAgent,
            timestamp: metric.timestamp || Date.now()
        };
        
        this.buffer.push(enrichedMetric);
        
        if (this.buffer.length >= this.config.bufferSize) {
            this.flushBuffer();
        }
    }
    
    startPeriodicFlush() {
        setInterval(() => {
            if (this.buffer.length > 0) {
                this.flushBuffer();
            }
        }, this.config.flushInterval);
    }
    
    flushBuffer(synchronous = false) {
        if (this.buffer.length === 0) return;
        
        const payload = {
            sessionId: this.sessionId,
            userId: this.userId,
            metrics: [...this.buffer],
            metadata: {
                userAgent: navigator.userAgent,
                url: window.location.href,
                timestamp: Date.now()
            }
        };
        
        this.buffer = []; // Clear buffer
        
        if (synchronous) {
            // Use sendBeacon for reliability during page unload
            if (navigator.sendBeacon) {
                navigator.sendBeacon(this.config.apiEndpoint, JSON.stringify(payload));
            }
        } else {
            // Use regular fetch
            fetch(this.config.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            }).catch(error => {
                console.warn('RUM data transmission failed:', error);
            });
        }
    }
    
    // Public API methods
    trackCustomEvent(eventName, data = {}) {
        this.addMetric({
            type: 'custom_event',
            eventName: eventName,
            data: data,
            timestamp: Date.now()
        });
    }
    
    trackUserTiming(name, startTime, endTime) {
        this.addMetric({
            type: 'user_timing',
            name: name,
            startTime: startTime,
            endTime: endTime,
            duration: endTime - startTime,
            timestamp: Date.now()
        });
    }
    
    setUserContext(userId, userData = {}) {
        this.userId = userId;
        this.addMetric({
            type: 'user_context',
            userId: userId,
            userData: userData,
            timestamp: Date.now()
        });
    }
    
    addBreadcrumb(message, category = 'default', data = {}) {
        this.addMetric({
            type: 'breadcrumb',
            message: message,
            category: category,
            data: data,
            timestamp: Date.now()
        });
    }
}

// Core Web Vitals specific tracking
class CoreWebVitalsTracker {
    constructor(callback) {
        this.callback = callback;
        this.vitals = {
            lcp: null,
            fid: null,
            cls: null,
            fcp: null,
            ttfb: null
        };
        
        this.trackLCP();
        this.trackFID();
        this.trackCLS();
        this.trackFCP();
        this.trackTTFB();
    }
    
    trackLCP() {
        if ('PerformanceObserver' in window) {
            try {
                const observer = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    
                    this.vitals.lcp = {
                        value: lastEntry.startTime,
                        rating: this.getRating('lcp', lastEntry.startTime),
                        element: lastEntry.element?.tagName?.toLowerCase(),
                        url: lastEntry.url,
                        timestamp: Date.now()
                    };
                    
                    this.callback('lcp', this.vitals.lcp);
                });
                
                observer.observe({ entryTypes: ['largest-contentful-paint'] });
            } catch (e) {
                console.warn('LCP tracking not supported:', e);
            }
        }
    }
    
    trackFID() {
        if ('PerformanceObserver' in window) {
            try {
                const observer = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        const fidValue = entry.processingStart - entry.startTime;
                        
                        this.vitals.fid = {
                            value: fidValue,
                            rating: this.getRating('fid', fidValue),
                            eventType: entry.name,
                            timestamp: Date.now()
                        };
                        
                        this.callback('fid', this.vitals.fid);
                    }
                });
                
                observer.observe({ entryTypes: ['first-input'] });
            } catch (e) {
                console.warn('FID tracking not supported:', e);
            }
        }
    }
    
    trackCLS() {
        if ('PerformanceObserver' in window) {
            try {
                let clsValue = 0;
                let sessionValue = 0;
                let sessionEntries = [];
                
                const observer = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (!entry.hadRecentInput) {
                            const firstSessionEntry = sessionEntries[0];
                            const lastSessionEntry = sessionEntries[sessionEntries.length - 1];
                            
                            if (sessionValue && 
                                entry.startTime - lastSessionEntry.startTime < 1000 &&
                                entry.startTime - firstSessionEntry.startTime < 5000) {
                                sessionValue += entry.value;
                                sessionEntries.push(entry);
                            } else {
                                sessionValue = entry.value;
                                sessionEntries = [entry];
                            }
                            
                            if (sessionValue > clsValue) {
                                clsValue = sessionValue;
                                
                                this.vitals.cls = {
                                    value: clsValue,
                                    rating: this.getRating('cls', clsValue),
                                    entries: sessionEntries.length,
                                    timestamp: Date.now()
                                };
                                
                                this.callback('cls', this.vitals.cls);
                            }
                        }
                    }
                });
                
                observer.observe({ entryTypes: ['layout-shift'] });
            } catch (e) {
                console.warn('CLS tracking not supported:', e);
            }
        }
    }
    
    trackFCP() {
        if ('PerformanceObserver' in window) {
            try {
                const observer = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (entry.name === 'first-contentful-paint') {
                            this.vitals.fcp = {
                                value: entry.startTime,
                                rating: this.getRating('fcp', entry.startTime),
                                timestamp: Date.now()
                            };
                            
                            this.callback('fcp', this.vitals.fcp);
                            observer.disconnect();
                        }
                    }
                });
                
                observer.observe({ entryTypes: ['paint'] });
            } catch (e) {
                console.warn('FCP tracking not supported:', e);
            }
        }
    }
    
    trackTTFB() {
        // Use Navigation API if available, otherwise fall back to performance.timing
        if ('PerformanceObserver' in window) {
            try {
                const observer = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (entry.entryType === 'navigation') {
                            const ttfb = entry.responseStart - entry.requestStart;
                            
                            this.vitals.ttfb = {
                                value: ttfb,
                                rating: this.getRating('ttfb', ttfb),
                                timestamp: Date.now()
                            };
                            
                            this.callback('ttfb', this.vitals.ttfb);
                            observer.disconnect();
                        }
                    }
                });
                
                observer.observe({ entryTypes: ['navigation'] });
            } catch (e) {
                console.warn('TTFB tracking not supported:', e);
            }
        }
    }
    
    getRating(metric, value) {
        const thresholds = {
            lcp: { good: 2500, poor: 4000 },
            fid: { good: 100, poor: 300 },
            cls: { good: 0.1, poor: 0.25 },
            fcp: { good: 1800, poor: 3000 },
            ttfb: { good: 800, poor: 1800 }
        };
        
        const threshold = thresholds[metric];
        if (!threshold) return 'unknown';
        
        if (value <= threshold.good) return 'good';
        if (value <= threshold.poor) return 'needs-improvement';
        return 'poor';
    }
    
    getAllVitals() {
        return this.vitals;
    }
}

// Usage example
// Initialize RUM
const rum = new RealUserMonitoring({
    apiEndpoint: '/api/rum',
    sampleRate: 0.1, // 10% sampling
    userId: 'user_12345',
    enableHeatmap: true
});

// Track Core Web Vitals
const cwv = new CoreWebVitalsTracker((metric, data) => {
    console.log(`Core Web Vital ${metric}:`, data);
    
    // Send to analytics
    rum.trackCustomEvent(`cwv_${metric}`, data);
});

// Track custom user interactions
rum.trackCustomEvent('feature_used', {
    featureName: 'product_search',
    query: 'laptop',
    resultsCount: 25
});

// Track custom timing
const searchStartTime = performance.now();
// ... perform search operation
const searchEndTime = performance.now();
rum.trackUserTiming('product_search', searchStartTime, searchEndTime);

// Set user context
rum.setUserContext('user_12345', {
    plan: 'premium',
    region: 'us-east',
    experiments: ['new-checkout', 'recommendation-v2']
});
```

## Synthetic Monitoring Implementation

### Automated Browser Testing for Performance

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests

class SyntheticMonitoring:
    def __init__(self, base_url: str, locations: List[str] = None):
        self.base_url = base_url.rstrip('/')
        self.locations = locations or ['us-east', 'us-west', 'eu-west']
        self.results = []
        
    def setup_driver(self, location: str = None, mobile: bool = False) -> webdriver.Chrome:
        """Setup Chrome WebDriver with performance logging"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        if mobile:
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15')
            chrome_options.add_argument('--window-size=375,812')
        else:
            chrome_options.add_argument('--window-size=1920,1080')
        
        # Enable performance logging
        chrome_options.add_experimental_option('perfLoggingPrefs', {
            'enableNetwork': True,
            'enablePage': True,
            'enableTimeline': True
        })
        
        chrome_options.add_experimental_option('loggingPrefs', {
            'performance': 'ALL',
            'browser': 'ALL'
        })
        
        return webdriver.Chrome(options=chrome_options)
    
    def run_page_test(self, url: str, test_name: str, location: str = 'default', 
                     mobile: bool = False, user_flows: List[Dict] = None) -> Dict[str, Any]:
        """Run comprehensive page performance test"""
        
        driver = self.setup_driver(location, mobile)
        test_result = {
            'test_name': test_name,
            'url': url,
            'location': location,
            'mobile': mobile,
            'timestamp': datetime.utcnow().isoformat(),
            'success': False,
            'error': None,
            'metrics': {},
            'user_flows': []
        }
        
        try:
            # Navigate to page and measure load time
            start_time = time.time()
            driver.get(url)
            
            # Wait for page to be fully loaded
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            load_time = time.time() - start_time
            
            # Get navigation timing
            nav_timing = driver.execute_script("""
                var timing = performance.timing;
                return {
                    navigationStart: timing.navigationStart,
                    unloadEventStart: timing.unloadEventStart,
                    unloadEventEnd: timing.unloadEventEnd,
                    redirectStart: timing.redirectStart,
                    redirectEnd: timing.redirectEnd,
                    fetchStart: timing.fetchStart,
                    domainLookupStart: timing.domainLookupStart,
                    domainLookupEnd: timing.domainLookupEnd,
                    connectStart: timing.connectStart,
                    connectEnd: timing.connectEnd,
                    secureConnectionStart: timing.secureConnectionStart,
                    requestStart: timing.requestStart,
                    responseStart: timing.responseStart,
                    responseEnd: timing.responseEnd,
                    domLoading: timing.domLoading,
                    domInteractive: timing.domInteractive,
                    domContentLoadedEventStart: timing.domContentLoadedEventStart,
                    domContentLoadedEventEnd: timing.domContentLoadedEventEnd,
                    domComplete: timing.domComplete,
                    loadEventStart: timing.loadEventStart,
                    loadEventEnd: timing.loadEventEnd
                };
            """)
            
            # Calculate key metrics
            metrics = {
                'load_time': load_time * 1000,  # Convert to ms
                'ttfb': nav_timing['responseStart'] - nav_timing['requestStart'],
                'dom_content_loaded': nav_timing['domContentLoadedEventEnd'] - nav_timing['navigationStart'],
                'dom_interactive': nav_timing['domInteractive'] - nav_timing['navigationStart'],
                'dom_complete': nav_timing['domComplete'] - nav_timing['navigationStart'],
                'page_load': nav_timing['loadEventEnd'] - nav_timing['navigationStart']
            }
            
            # Get paint timings
            paint_timings = driver.execute_script("""
                var paintEntries = performance.getEntriesByType('paint');
                var result = {};
                paintEntries.forEach(function(entry) {
                    result[entry.name] = entry.startTime;
                });
                return result;
            """)
            
            metrics.update({
                'first_paint': paint_timings.get('first-paint', 0),
                'first_contentful_paint': paint_timings.get('first-contentful-paint', 0)
            })
            
            # Get Core Web Vitals
            cwv_script = """
                return new Promise((resolve) => {
                    var vitals = {};
                    
                    // LCP
                    if ('PerformanceObserver' in window) {
                        try {
                            new PerformanceObserver((list) => {
                                var entries = list.getEntries();
                                var lastEntry = entries[entries.length - 1];
                                vitals.lcp = lastEntry.startTime;
                            }).observe({entryTypes: ['largest-contentful-paint']});
                        } catch(e) {}
                        
                        // CLS
                        try {
                            var clsValue = 0;
                            new PerformanceObserver((list) => {
                                for (var entry of list.getEntries()) {
                                    if (!entry.hadRecentInput) {
                                        clsValue += entry.value;
                                    }
                                }
                                vitals.cls = clsValue;
                            }).observe({entryTypes: ['layout-shift']});
                        } catch(e) {}
                        
                        // FID
                        try {
                            new PerformanceObserver((list) => {
                                for (var entry of list.getEntries()) {
                                    vitals.fid = entry.processingStart - entry.startTime;
                                }
                            }).observe({entryTypes: ['first-input']});
                        } catch(e) {}
                    }
                    
                    // Wait a bit for observers to capture data
                    setTimeout(() => resolve(vitals), 2000);
                });
            """
            
            try:
                cwv = driver.execute_async_script(cwv_script)
                metrics.update(cwv)
            except:
                pass  # CWV measurement failed
            
            # Get resource loading metrics
            resource_metrics = driver.execute_script("""
                var resources = performance.getEntriesByType('resource');
                var totalSize = 0;
                var resourceCount = 0;
                var slowestResource = 0;
                var resourceTypes = {};
                
                resources.forEach(function(resource) {
                    totalSize += resource.transferSize || 0;
                    resourceCount++;
                    slowestResource = Math.max(slowestResource, resource.duration);
                    
                    var type = resource.initiatorType || 'other';
                    resourceTypes[type] = (resourceTypes[type] || 0) + 1;
                });
                
                return {
                    totalSize: totalSize,
                    resourceCount: resourceCount,
                    slowestResource: slowestResource,
                    resourceTypes: resourceTypes
                };
            """)
            
            metrics.update(resource_metrics)
            
            # Get page info
            page_info = {
                'title': driver.title,
                'url': driver.current_url,
                'viewport': driver.get_window_size()
            }
            
            # Run user flows if specified
            if user_flows:
                for flow in user_flows:
                    flow_result = self._run_user_flow(driver, flow)
                    test_result['user_flows'].append(flow_result)
            
            # Check for JavaScript errors
            browser_logs = driver.get_log('browser')
            js_errors = [log for log in browser_logs if log['level'] == 'SEVERE']
            
            test_result.update({
                'success': True,
                'metrics': metrics,
                'page_info': page_info,
                'js_errors': len(js_errors),
                'error_details': js_errors[:5]  # First 5 errors
            })
            
        except Exception as e:
            test_result['error'] = str(e)
            
        finally:
            driver.quit()
        
        self.results.append(test_result)
        return test_result
    
    def _run_user_flow(self, driver: webdriver.Chrome, flow: Dict) -> Dict[str, Any]:
        """Run a specific user flow scenario"""
        flow_result = {
            'name': flow.get('name', 'unnamed_flow'),
            'steps': [],
            'total_duration': 0,
            'success': False,
            'error': None
        }
        
        start_time = time.time()
        
        try:
            steps = flow.get('steps', [])
            for i, step in enumerate(steps):
                step_start = time.time()
                step_result = {'step': i + 1, 'action': step.get('action'), 'success': False}
                
                try:
                    if step['action'] == 'click':
                        element = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, step['selector']))
                        )
                        element.click()
                        
                    elif step['action'] == 'type':
                        element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, step['selector']))
                        )
                        element.clear()
                        element.send_keys(step['text'])
                        
                    elif step['action'] == 'wait':
                        time.sleep(step.get('duration', 1))
                        
                    elif step['action'] == 'wait_for_element':
                        WebDriverWait(driver, step.get('timeout', 10)).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, step['selector']))
                        )
                    
                    step_result['success'] = True
                    step_result['duration'] = (time.time() - step_start) * 1000
                    
                except Exception as e:
                    step_result['error'] = str(e)
                    step_result['duration'] = (time.time() - step_start) * 1000
                    break
                
                flow_result['steps'].append(step_result)
            
            flow_result['success'] = all(step['success'] for step in flow_result['steps'])
            flow_result['total_duration'] = (time.time() - start_time) * 1000
            
        except Exception as e:
            flow_result['error'] = str(e)
            flow_result['total_duration'] = (time.time() - start_time) * 1000
        
        return flow_result
    
    def run_multi_location_test(self, urls: List[str], test_scenarios: List[Dict]) -> Dict[str, Any]:
        """Run tests across multiple locations and scenarios"""
        
        multi_test_results = {
            'start_time': datetime.utcnow().isoformat(),
            'urls': urls,
            'locations': self.locations,
            'scenarios': len(test_scenarios),
            'results': []
        }
        
        for url in urls:
            for location in self.locations:
                for scenario in test_scenarios:
                    test_name = f"{scenario['name']}_{location}"
                    
                    print(f"Running test: {test_name} for {url}")
                    
                    result = self.run_page_test(
                        url=url,
                        test_name=test_name,
                        location=location,
                        mobile=scenario.get('mobile', False),
                        user_flows=scenario.get('user_flows', [])
                    )
                    
                    multi_test_results['results'].append(result)
                    
                    # Add delay between tests
                    time.sleep(2)
        
        # Calculate summary statistics
        multi_test_results['summary'] = self._calculate_summary(multi_test_results['results'])
        return multi_test_results
    
    def _calculate_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics from test results"""
        
        successful_results = [r for r in results if r['success']]
        
        if not successful_results:
            return {'error': 'No successful test results'}
        
        # Extract metrics for statistical analysis
        metrics_data = {}
        for result in successful_results:
            for metric_name, value in result['metrics'].items():
                if isinstance(value, (int, float)):
                    if metric_name not in metrics_data:
                        metrics_data[metric_name] = []
                    metrics_data[metric_name].append(value)
        
        # Calculate statistics
        summary = {
            'total_tests': len(results),
            'successful_tests': len(successful_results),
            'success_rate': len(successful_results) / len(results) * 100,
            'metrics_summary': {}
        }
        
        for metric_name, values in metrics_data.items():
            if values:
                summary['metrics_summary'][metric_name] = {
                    'min': min(values),
                    'max': max(values),
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'p95': statistics.quantiles(values, n=20)[18] if len(values) > 5 else max(values),
                    'p99': statistics.quantiles(values, n=100)[98] if len(values) > 10 else max(values)
                }
        
        # Location performance comparison
        location_performance = {}
        for result in successful_results:
            location = result['location']
            if location not in location_performance:
                location_performance[location] = {'load_times': [], 'ttfb': []}
            
            if 'load_time' in result['metrics']:
                location_performance[location]['load_times'].append(result['metrics']['load_time'])
            if 'ttfb' in result['metrics']:
                location_performance[location]['ttfb'].append(result['metrics']['ttfb'])
        
        for location, data in location_performance.items():
            if data['load_times']:
                location_performance[location] = {
                    'avg_load_time': statistics.mean(data['load_times']),
                    'avg_ttfb': statistics.mean(data['ttfb']) if data['ttfb'] else 0
                }
        
        summary['location_performance'] = location_performance
        return summary

# Usage example
def demonstrate_synthetic_monitoring():
    """Demonstrate synthetic monitoring capabilities"""
    
    print("🤖 Synthetic Monitoring Demo")
    print("=" * 30)
    
    # Initialize synthetic monitoring
    synthetic = SyntheticMonitoring('https://example.com')
    
    # Define test scenarios
    test_scenarios = [
        {
            'name': 'desktop_homepage',
            'mobile': False,
            'user_flows': []
        },
        {
            'name': 'mobile_homepage',
            'mobile': True,
            'user_flows': []
        },
        {
            'name': 'user_journey',
            'mobile': False,
            'user_flows': [
                {
                    'name': 'search_product',
                    'steps': [
                        {'action': 'click', 'selector': '#search-button'},
                        {'action': 'type', 'selector': '#search-input', 'text': 'laptop'},
                        {'action': 'click', 'selector': '#search-submit'},
                        {'action': 'wait_for_element', 'selector': '.search-results', 'timeout': 10}
                    ]
                }
            ]
        }
    ]
    
    # Test URLs
    test_urls = [
        'https://example.com',
        'https://example.com/products',
        'https://example.com/about'
    ]
    
    # Run multi-location tests
    print("Running synthetic tests across multiple locations...")
    results = synthetic.run_multi_location_test(test_urls, test_scenarios)
    
    print(f"\nTest Results Summary:")
    print(f"Total Tests: {results['summary']['total_tests']}")
    print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
    
    if 'metrics_summary' in results['summary']:
        print(f"\nPerformance Metrics:")
        for metric, stats in results['summary']['metrics_summary'].items():
            print(f"  {metric}:")
            print(f"    Mean: {stats['mean']:.1f}ms")
            print(f"    P95: {stats['p95']:.1f}ms")
    
    if 'location_performance' in results['summary']:
        print(f"\nLocation Performance:")
        for location, perf in results['summary']['location_performance'].items():
            print(f"  {location}:")
            print(f"    Avg Load Time: {perf['avg_load_time']:.1f}ms")
            print(f"    Avg TTFB: {perf['avg_ttfb']:.1f}ms")

if __name__ == "__main__":
    demonstrate_synthetic_monitoring()
```

This comprehensive User Experience Monitoring system provides enterprise-grade real user monitoring and synthetic testing capabilities essential for optimizing application performance and ensuring excellent user experiences across all platforms and locations.