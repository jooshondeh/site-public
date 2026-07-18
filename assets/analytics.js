(() => {
  'use strict';

  const measurementId = 'G-WWCZJ4MDGN';
  const storageKey = 'nexgen_analytics_consent_v2';

  const getConsent = () => {
    try {
      return window.localStorage.getItem(storageKey);
    } catch {
      return null;
    }
  };

  const setConsent = (value) => {
    try {
      window.localStorage.setItem(storageKey, value);
    } catch {
      // The selected state still applies for this page when storage is blocked.
    }
  };

  const consentParameters = (analyticsValue) => ({
    analytics_storage: analyticsValue,
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied'
  });

  let analyticsReady = false;
  let trackingAttached = false;

  const sendEvent = (name, parameters = {}) => {
    if (!analyticsReady || typeof window.gtag !== 'function') return;
    window.gtag('event', name, parameters);
  };

  const locationName = (element) => {
    if (element.closest('header')) return 'header';
    if (element.closest('.hero')) return 'hero';
    if (element.closest('#contact')) return 'contact';
    if (element.closest('footer')) return 'footer';
    if (element.closest('.booking-page')) return 'booking_page';
    return 'page';
  };

  const attachEventTracking = () => {
    if (trackingAttached) return;
    trackingAttached = true;

    document.querySelectorAll('a[data-call-phone]').forEach((link) => {
      link.addEventListener('click', () => {
        sendEvent('click_to_call', { link_location: locationName(link) });
      });
    });

    document.querySelectorAll('a[href^="mailto:"]').forEach((link) => {
      link.addEventListener('click', () => {
        sendEvent('email_click', { link_location: locationName(link) });
      });
    });

    document
      .querySelectorAll(
        '[data-booking-open], a[href*="outlook.office.com/book/"]'
      )
      .forEach((link) => {
        link.addEventListener('click', () => {
          sendEvent('booking_click', { link_location: locationName(link) });
        });
      });

    document.querySelectorAll('a.google-business').forEach((link) => {
      link.addEventListener('click', () => {
        sendEvent('google_business_click', {
          link_location: locationName(link)
        });
      });
    });

    const form = document.querySelector('[data-contact-form]');
    if (form) {
      let started = false;
      form.addEventListener('focusin', () => {
        if (started) return;
        started = true;
        sendEvent('contact_form_start');
      });
    }

    window.addEventListener('nexgen:contact-form-success', () => {
      sendEvent('generate_lead', { method: 'contact_form' });
    });

    window.addEventListener('nexgen:contact-form-error', () => {
      sendEvent('contact_form_error');
    });

    window.addEventListener('nexgen:section-change', (event) => {
      const sectionId = event.detail?.sectionId;
      if (sectionId) {
        sendEvent('section_view', { section_id: sectionId });
      }
    });

    const reached = new Set();
    const trackScroll = () => {
      const documentHeight = Math.max(
        document.body.scrollHeight,
        document.documentElement.scrollHeight
      );
      const viewportBottom = window.scrollY + window.innerHeight;
      const percentage = Math.min(
        100,
        Math.round((viewportBottom / documentHeight) * 100)
      );

      [25, 50, 75, 90].forEach((threshold) => {
        if (percentage >= threshold && !reached.has(threshold)) {
          reached.add(threshold);
          sendEvent('scroll_depth', { percent_scrolled: threshold });
        }
      });
    };

    window.addEventListener('scroll', trackScroll, { passive: true });
    trackScroll();

    const vitals = {};

    const reportVitals = () => {
      Object.entries(vitals).forEach(([metricName, value]) => {
        sendEvent('web_vital', {
          metric_name: metricName,
          metric_value: Math.round(value),
          non_interaction: true
        });
      });
    };

    try {
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const last = entries[entries.length - 1];
        if (last) vitals.LCP = last.startTime;
      }).observe({ type: 'largest-contentful-paint', buffered: true });
    } catch {}

    try {
      let cls = 0;
      new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (!entry.hadRecentInput) cls += entry.value;
        });
        vitals.CLS = cls * 1000;
      }).observe({ type: 'layout-shift', buffered: true });
    } catch {}

    try {
      new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          vitals.INP = Math.max(vitals.INP || 0, entry.duration || 0);
        });
      }).observe({
        type: 'event',
        durationThreshold: 40,
        buffered: true
      });
    } catch {}

    window.addEventListener('pagehide', reportVitals, { once: true });
  };

  const applyConsent = (value, sendCurrentPage = false) => {
    if (typeof window.gtag !== 'function') return;

    window.gtag(
      'consent',
      'update',
      consentParameters(value === 'granted' ? 'granted' : 'denied')
    );

    analyticsReady = value === 'granted';

    if (analyticsReady) {
      attachEventTracking();

      if (sendCurrentPage) {
        window.gtag('event', 'page_view', {
          page_title: document.title,
          page_location: window.location.href,
          page_path: `${window.location.pathname}${window.location.hash}`
        });
      }
    }
  };

  const removeBanner = () => {
    document.querySelector('[data-analytics-consent]')?.remove();
  };

  const chooseConsent = (value) => {
    setConsent(value);
    applyConsent(value, value === 'granted');
    removeBanner();
  };

  const privacyUrl = () =>
    document.querySelector('a[href*="privacy/"]')?.href ||
    new URL('/privacy/', window.location.origin).href;

  const showConsentBanner = () => {
    if (document.querySelector('[data-analytics-consent]')) return;

    const banner = document.createElement('section');
    banner.className = 'analytics-consent';
    banner.dataset.analyticsConsent = '';
    banner.setAttribute('aria-label', 'Analytics preferences');
    banner.innerHTML = `
      <div class="analytics-consent__copy">
        <strong>Analytics preferences</strong>
        <span>
          Allow anonymous website analytics to help improve the site.
          Contact-form contents are never sent to Google Analytics.
        </span>
        <a href="${privacyUrl()}">Privacy Policy</a>
      </div>
      <div class="analytics-consent__actions">
        <button
          type="button"
          class="button button-secondary button-small"
          data-analytics-decline
        >Decline</button>
        <button
          type="button"
          class="button button-primary button-small"
          data-analytics-accept
        >Allow analytics</button>
      </div>
    `;

    banner
      .querySelector('[data-analytics-accept]')
      .addEventListener('click', () => chooseConsent('granted'));

    banner
      .querySelector('[data-analytics-decline]')
      .addEventListener('click', () => chooseConsent('denied'));

    document.body.append(banner);
  };

  const addSettingsLink = () => {
    const legal = document.querySelector('.footer-legal');
    if (!legal || legal.querySelector('[data-analytics-settings]')) return;

    const settings = document.createElement('button');
    settings.type = 'button';
    settings.className = 'footer-settings-link';
    settings.dataset.analyticsSettings = '';
    settings.textContent = 'Analytics settings';

    settings.addEventListener('click', () => {
      try {
        window.localStorage.removeItem(storageKey);
      } catch {}

      applyConsent('denied');
      showConsentBanner();
    });

    legal.append(settings);
  };

  document.addEventListener('DOMContentLoaded', () => {
    addSettingsLink();

    const consent = getConsent();

    if (consent === 'granted') {
      applyConsent('granted');
    } else if (consent === 'denied') {
      applyConsent('denied');
    } else {
      applyConsent('denied');
      showConsentBanner();
    }
  });
})();
