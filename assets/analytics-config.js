(() => {
  'use strict';

  const measurementId = '';
  window.NEXGEN_ANALYTICS_CONFIG = Object.freeze({
    googleAnalyticsMeasurementId: measurementId,
    requireConsent: true,
    respectDoNotTrack: true
  });

  if (!/^G-[A-Z0-9]+$/i.test(measurementId)) return;

  const currentScript = document.currentScript;
  const loadAnalytics = () => {
    if (document.querySelector('script[data-nexgen-analytics-loader]')) return;
    const script = document.createElement('script');
    script.async = true;
    script.dataset.nexgenAnalyticsLoader = '';
    script.src = new URL('analytics.js?v=20260718prod3', currentScript?.src || document.baseURI).href;
    document.head.append(script);
  };

  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(loadAnalytics, { timeout: 1600 });
  } else {
    window.setTimeout(loadAnalytics, 0);
  }
})();
