(() => {
  'use strict';

  document.documentElement.classList.add('js');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const scrollToElement = (element, block = 'center') => {
    element?.scrollIntoView({ behavior: reducedMotion.matches ? 'auto' : 'smooth', block });
  };

  // Preserve valid section URLs on refresh. Pages without a section hash start at top.
  const navigationEntry = performance.getEntriesByType?.('navigation')?.[0];
  const isPageReload =
    navigationEntry?.type === 'reload' ||
    performance.navigation?.type === 1;

  if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
  }

  const sectionHashIds = new Set(
    [...document.querySelectorAll('[data-nav-link][href^="#"]')]
      .map((link) => link.getAttribute('href')?.slice(1))
      .filter(Boolean)
  );

  const currentHashId = () => {
    const hash = window.location.hash.slice(1);
    try {
      return decodeURIComponent(hash);
    } catch {
      // A malformed incoming fragment must not disable the rest of the page.
      return hash;
    }
  };
  const isValidSectionHash = (id) => sectionHashIds.has(id) && !!document.getElementById(id);

  const scrollReloadToTop = () => {
    if (!isPageReload) return;

    const hashId = currentHashId();
    if (isValidSectionHash(hashId)) {
      document.getElementById(hashId)?.scrollIntoView({ behavior: 'auto', block: 'start' });
      return;
    }

    if (window.location.hash) {
      history.replaceState(
        history.state,
        document.title,
        `${window.location.pathname}${window.location.search}`
      );
    }

    window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
  };

  scrollReloadToTop();
  requestAnimationFrame(() => requestAnimationFrame(scrollReloadToTop));
  window.addEventListener('DOMContentLoaded', scrollReloadToTop, { once: true });
  window.addEventListener('load', scrollReloadToTop, { once: true });
  window.addEventListener('pageshow', scrollReloadToTop, { once: true });
  window.setTimeout(scrollReloadToTop, 120);

  // Native tel: links use real selectable text. Remove only badges injected
  // by browser calling features or extensions.
  const phoneDisplayText = '(804) 460-9640';
  const phoneDecorationGlyphs =
    /(?:\u260E\uFE0F?|\u260F|\u2706|\u{1F4DE}|\u{1F4F1}|\u{1F4F2}|\u{1F919})/gu;

  const isPhoneDecoration = (node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      const value = node.nodeValue.trim();
      return Boolean(value) &&
        value.replace(phoneDecorationGlyphs, '').trim() === '';
    }

    if (node.nodeType !== Node.ELEMENT_NODE) return false;

    const element = node;
    const text = element.textContent.trim();

    if (text && text.replace(phoneDecorationGlyphs, '').trim() === '') {
      return true;
    }

    const marker = [
      element.id,
      element.className,
      element.getAttribute('title'),
      element.getAttribute('aria-label'),
      element.getAttribute('alt'),
      element.getAttribute('src')
    ].filter(Boolean).join(' ');

    return /(?:green.?call|phone.?badge|call.?badge|dial.?badge|tel.?icon)/i.test(marker);
  };

  const removePhoneDecorations = (link) => {
    const display = link.querySelector(':scope > .phone-number-display');

    [...link.childNodes].forEach((node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        const value = node.nodeValue.trim();
        if (
          value &&
          value.replace(phoneDecorationGlyphs, '').trim() === ''
        ) {
          node.remove();
        }
        return;
      }

      if (node.nodeType !== Node.ELEMENT_NODE) return;

      const element = node;
      if (element.tagName === 'svg' || element === display) return;

      if (isPhoneDecoration(element)) {
        element.remove();
      }
    });

    if (display && display.textContent.trim() !== phoneDisplayText) {
      display.replaceChildren(document.createTextNode(phoneDisplayText));
    }

    let sibling = link.nextSibling;
    while (sibling && isPhoneDecoration(sibling)) {
      const next = sibling.nextSibling;
      sibling.remove();
      sibling = next;
    }
  };

  document.querySelectorAll('a[data-call-phone][href^="tel:"]').forEach((link) => {
    removePhoneDecorations(link);

    new MutationObserver(() => removePhoneDecorations(link)).observe(link, {
      subtree: true,
      childList: true,
      characterData: true
    });

    const parent = link.parentElement;
    if (parent) {
      new MutationObserver(() => removePhoneDecorations(link)).observe(parent, {
        childList: true
      });
    }

    requestAnimationFrame(() => removePhoneDecorations(link));
    window.setTimeout(() => removePhoneDecorations(link), 250);
  });

  const header = document.querySelector('[data-site-header]');
  const toggle = document.querySelector('[data-nav-toggle]');
  const nav = document.querySelector('[data-primary-nav]');
  const navLinks = Array.from(document.querySelectorAll('[data-nav-link]'));
  const mobileBreakpoint = window.matchMedia('(max-width: 1180px)');

  // CSS controls the minimum height; this offset follows wrapping and zoom.
  const measureHeader = () => {
    if (!header) return;
    const height = `${Math.ceil(header.getBoundingClientRect().height)}px`;
    if (document.documentElement.style.getPropertyValue('--header-height') !== height) {
      document.documentElement.style.setProperty('--header-height', height);
    }
  };
  measureHeader();
  if (header && 'ResizeObserver' in window) {
    new ResizeObserver(measureHeader).observe(header);
  } else {
    window.addEventListener('resize', measureHeader, { passive: true });
  }
  document.fonts?.ready.then(measureHeader);
  window.addEventListener('pageshow', measureHeader);

  const closeNav = () => {
    if (!toggle || !nav) return;
    nav.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Open navigation');
  };

  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = !nav.classList.contains('is-open');
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    });
    document.addEventListener('click', (event) => {
      if (!mobileBreakpoint.matches || !nav.classList.contains('is-open')) return;
      if (header && header.contains(event.target)) return;
      closeNav();
    });
    document.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape' || !nav.classList.contains('is-open')) return;
      event.preventDefault();
      closeNav();
      toggle.focus({ preventScroll: true });
    });
    if (typeof mobileBreakpoint.addEventListener === 'function') {
      mobileBreakpoint.addEventListener('change', closeNav);
    } else if (typeof mobileBreakpoint.addListener === 'function') {
      mobileBreakpoint.addListener(closeNav);
    }
    navLinks.forEach((link) => link.addEventListener('click', closeNav));
  }

  const sectionLinks = navLinks.filter((link) => {
    const href = link.getAttribute('href') || '';
    return href.startsWith('#') && href.length > 1;
  });

  let currentSectionId = null;
  let sectionUpdateFrame = null;

  const sectionUrl = (sectionId) => {
    const base = `${window.location.pathname}${window.location.search}`;
    return sectionId === 'home' ? base : `${base}#${sectionId}`;
  };

  const updateSectionUrl = (sectionId) => {
    if (!sectionId || sectionId === currentSectionId) return;
    currentSectionId = sectionId;

    const nextUrl = sectionUrl(sectionId);
    const currentUrl = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    if (nextUrl !== currentUrl) {
      history.replaceState(history.state, document.title, nextUrl);
    }

    window.dispatchEvent(new CustomEvent('nexgen:section-change', {
      detail: { sectionId }
    }));
  };

  const setActiveLink = ({ updateUrl = true } = {}) => {
    if (!sectionLinks.length) return;

    const offset = (header?.offsetHeight || 80) + 24;
    let current = sectionLinks[0].getAttribute('href').slice(1);

    for (const link of sectionLinks) {
      const id = link.getAttribute('href').slice(1);
      const section = document.getElementById(id);
      if (section && window.scrollY + offset >= section.offsetTop) current = id;
    }

    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) {
      current = sectionLinks[sectionLinks.length - 1].getAttribute('href').slice(1);
    }

    sectionLinks.forEach((link) => {
      const active = link.getAttribute('href') === `#${current}`;
      link.classList.toggle('is-active', active);
      if (active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });

    if (updateUrl) updateSectionUrl(current);
  };

  const scheduleSectionUpdate = () => {
    if (sectionUpdateFrame !== null) return;
    sectionUpdateFrame = requestAnimationFrame(() => {
      sectionUpdateFrame = null;
      setActiveLink();
    });
  };

  if (sectionLinks.length) {
    const initialHash = currentHashId();
    setActiveLink({ updateUrl: !isValidSectionHash(initialHash) });

    // Keep the menu available while its links are scrolled into view by touch
    // or keyboard. Selection, Escape, outside clicks and breakpoint changes close it.
    window.addEventListener('scroll', scheduleSectionUpdate, { passive: true });

    window.addEventListener('resize', scheduleSectionUpdate);
    window.addEventListener('pageshow', () => setActiveLink({
      updateUrl: !isValidSectionHash(currentHashId())
    }));
    window.addEventListener('hashchange', () => {
      currentSectionId = null;
      scheduleSectionUpdate();
    });
  }

  const warmExternalOrigin = (url) => {
    try {
      const origin = new URL(url, document.baseURI).origin;
      if (document.querySelector(`link[data-preconnect-origin="${origin}"]`)) return;
      const link = document.createElement('link');
      link.rel = 'preconnect';
      link.href = origin;
      link.crossOrigin = 'anonymous';
      link.dataset.preconnectOrigin = origin;
      document.head.append(link);
    } catch {
      // Ignore invalid external URLs.
    }
  };

  const nativeDialog = (modal) => typeof modal?.showModal === 'function';
  const fallbackModalState = new WeakMap();
  const isolateFallbackModal = (modal) => {
    if (nativeDialog(modal) || fallbackModalState.has(modal)) return;
    const saved = [];
    let branch = modal;
    while (branch.parentElement) {
      const parent = branch.parentElement;
      [...parent.children].forEach((element) => {
        if (element === branch || /^(SCRIPT|STYLE|LINK)$/.test(element.tagName)) return;
        saved.push({
          element,
          inert: element.getAttribute('inert'),
          ariaHidden: element.getAttribute('aria-hidden')
        });
        element.setAttribute('inert', '');
        element.setAttribute('aria-hidden', 'true');
      });
      if (parent === document.body) break;
      branch = parent;
    }
    fallbackModalState.set(modal, saved);
  };
  const restoreFallbackModal = (modal) => {
    (fallbackModalState.get(modal) || []).forEach(({ element, inert, ariaHidden }) => {
      if (inert === null) element.removeAttribute('inert');
      else element.setAttribute('inert', inert);
      if (ariaHidden === null) element.removeAttribute('aria-hidden');
      else element.setAttribute('aria-hidden', ariaHidden);
    });
    fallbackModalState.delete(modal);
  };

  const bookingModal = document.getElementById('nb-booking-modal');
  const bookingFrame = document.getElementById('nb-booking-iframe');
  const bookingOpeners = Array.from(document.querySelectorAll('[data-booking-open]'));
  bookingOpeners.forEach((opener) => {
    const bookingUrl = opener.getAttribute('href') || '';
    const warm = () => warmExternalOrigin(bookingUrl);
    opener.addEventListener('pointerenter', warm, { once: true, passive: true });
    opener.addEventListener('focus', warm, { once: true });
    opener.addEventListener('touchstart', warm, { once: true, passive: true });
  });
  const bookingClosers = bookingModal ? Array.from(bookingModal.querySelectorAll('[data-booking-close]')) : [];
  let bookingReturnFocus = null;

  const bookingFocusable = () => bookingModal
    ? Array.from(bookingModal.querySelectorAll('a[href], button:not([disabled]), iframe, [tabindex]:not([tabindex="-1"])'))
    : [];

  const openBooking = (event) => {
    if (!bookingModal || !bookingFrame) return;
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button > 0) return;
    event.preventDefault();
    if (bookingModal.classList.contains('is-open')) return;
    bookingReturnFocus = event.currentTarget || document.activeElement;
    if (!bookingFrame.getAttribute('src')) bookingFrame.src = bookingFrame.dataset.src || '';
    closeNav();
    bookingModal.classList.add('is-open');
    bookingModal.setAttribute('aria-hidden', 'false');
    bookingModal.setAttribute('aria-modal', 'true');
    if (nativeDialog(bookingModal)) bookingModal.showModal();
    else {
      bookingModal.setAttribute('open', '');
      isolateFallbackModal(bookingModal);
    }
    document.documentElement.classList.add('nb-modal-open');
    document.body.classList.add('nb-modal-open');
    window.setTimeout(() => bookingModal.querySelector('.nb-booking-close')?.focus({ preventScroll: true }), 0);
  };

  const closeBooking = (event) => {
    event?.preventDefault();
    if (!bookingModal?.classList.contains('is-open')) return;
    if (nativeDialog(bookingModal) && bookingModal.open) bookingModal.close();
    else bookingModal.removeAttribute('open');
    bookingModal.classList.remove('is-open');
    bookingModal.setAttribute('aria-hidden', 'true');
    bookingModal.removeAttribute('aria-modal');
    restoreFallbackModal(bookingModal);
    document.documentElement.classList.remove('nb-modal-open');
    document.body.classList.remove('nb-modal-open');
    const returnFocus = bookingReturnFocus;
    bookingReturnFocus = null;
    if (returnFocus instanceof HTMLElement && returnFocus.isConnected) {
      window.setTimeout(() => returnFocus.focus({ preventScroll: true }), 0);
    }
  };

  bookingOpeners.forEach((opener) => opener.addEventListener('click', openBooking));
  bookingClosers.forEach((closer) => closer.addEventListener('click', closeBooking));
  bookingModal?.addEventListener('cancel', closeBooking);
  bookingModal?.addEventListener('close', closeBooking);
  document.addEventListener('focusin', (event) => {
    if (!bookingModal?.classList.contains('is-open') || nativeDialog(bookingModal)) return;
    if (!bookingModal.contains(event.target)) bookingFocusable()[0]?.focus();
  });

  document.addEventListener('keydown', (event) => {
    if (!bookingModal?.classList.contains('is-open')) return;
    if (event.key === 'Escape') {
      closeBooking(event);
      return;
    }
    if (nativeDialog(bookingModal)) return;
    if (event.key !== 'Tab') return;
    const focusable = bookingFocusable();
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  const consultationLinks = document.querySelectorAll('[data-focus-contact]');
  const nameField = document.getElementById('contact-name');
  consultationLinks.forEach((link) => {
    link.addEventListener('click', () => {
      window.setTimeout(() => nameField?.focus({ preventScroll: true }), 450);
    });
  });

  const form = document.querySelector('[data-contact-form]');
  if (form) {
    const status = document.getElementById('contact-status');
    const submitButton = form.querySelector('button[type="submit"]');
    const submitLabel = submitButton?.querySelector('[data-submit-label]');
    const captchaError = document.getElementById('contact-captcha-error');
    const successModal = document.getElementById('contact-success-modal');
    const successClose = successModal?.querySelector('[data-success-close]');
    const requiredFields = Array.from(form.querySelectorAll('[required]'));
    const endpoint = form.getAttribute('action') || form.dataset.formspreeEndpoint || '';

    const captchaWidget = form.querySelector('[data-hcaptcha-lazy], .h-captcha[data-sitekey]');
    let captchaLoadStatus = captchaWidget?.querySelector('[data-hcaptcha-load-status]');
    const captchaSitekey = captchaWidget?.dataset.sitekey || '';
    let captchaWidgetId = null;
    let captchaLoadPromise = null;

    const setCaptchaLoadStatus = (message, busy = false) => {
      if (!captchaWidget) return;
      captchaWidget.setAttribute('aria-busy', busy ? 'true' : 'false');
      if (!captchaLoadStatus?.isConnected && captchaWidgetId === null) {
        captchaLoadStatus = document.createElement('span');
        captchaLoadStatus.className = 'captcha-load-status';
        captchaLoadStatus.dataset.hcaptchaLoadStatus = '';
        captchaLoadStatus.setAttribute('role', 'status');
        captchaLoadStatus.setAttribute('aria-live', 'polite');
        captchaWidget.replaceChildren(captchaLoadStatus);
      }
      if (captchaLoadStatus?.isConnected) captchaLoadStatus.textContent = message;
      if (busy) captchaWidget.querySelector('[data-captcha-retry]')?.remove();
    };

    const reportCaptchaLoadFailure = () => {
      const message = 'Verification could not load. Retry verification or email us directly.';
      setCaptchaLoadStatus(message);
      if (captchaError) captchaError.textContent = message;
      if (!captchaWidget || captchaWidget.querySelector('[data-captcha-retry]')) return;
      const retry = document.createElement('button');
      retry.type = 'button';
      retry.className = 'button button-secondary button-small';
      retry.dataset.captchaRetry = '';
      retry.textContent = 'Retry verification';
      retry.addEventListener('click', () => requestCaptchaLoad());
      captchaWidget.append(retry);
    };

    const renderHCaptcha = () => {
      if (!captchaWidget || captchaWidgetId !== null) return captchaWidgetId;
      if (!window.hcaptcha?.render || !captchaSitekey) {
        throw new Error('Verification could not initialize.');
      }

      const parent = captchaWidget.parentElement;
      const parentStyle = parent ? window.getComputedStyle(parent) : null;
      const parentWidth = parent
        ? parent.clientWidth - parseFloat(parentStyle.paddingLeft || 0) - parseFloat(parentStyle.paddingRight || 0)
        : 0;
      const measuredWidth = Math.min(
        captchaWidget.clientWidth || Infinity,
        parentWidth || Infinity
      );
      const availableWidth = Number.isFinite(measuredWidth) ? measuredWidth : 0;
      captchaWidget.replaceChildren();
      captchaWidget.setAttribute('aria-busy', 'false');
      captchaWidgetId = window.hcaptcha.render(captchaWidget, {
        sitekey: captchaSitekey,
        size: availableWidth >= 304 ? 'normal' : 'compact',
        theme: 'light',
        callback: () => {
          if (captchaError) captchaError.textContent = '';
        },
        'error-callback': () => {
          if (captchaError) captchaError.textContent = 'Verification encountered an error. Please retry or email us directly.';
        },
        'expired-callback': () => {
          if (captchaError) captchaError.textContent = 'Verification expired. Please complete it again.';
        }
      });
      if (captchaError) captchaError.textContent = '';
      return captchaWidgetId;
    };

    const loadHCaptcha = () => {
      if (!captchaWidget) return Promise.resolve(null);
      if (captchaWidgetId !== null) return Promise.resolve(captchaWidgetId);
      if (captchaLoadPromise) return captchaLoadPromise;

      setCaptchaLoadStatus('Loading verification…', true);
      const loading = window.hcaptcha?.render
        ? Promise.resolve().then(renderHCaptcha)
        : new Promise((resolve, reject) => {
        const callbackName = 'nexgenHCaptchaReady';
        // A failed prior attempt must not leave a promise waiting on a stale script.
        document.querySelector('script[data-nexgen-hcaptcha]')?.remove();
        const script = document.createElement('script');
        let settled = false;
        let timeoutId;

        const cleanup = () => {
          window.clearTimeout(timeoutId);
          script.onerror = null;
          if (window[callbackName] === ready) {
            try { delete window[callbackName]; } catch {}
          }
        };
        const fail = (error) => {
          if (settled) return;
          settled = true;
          cleanup();
          script.remove();
          reject(error);
        };

        const ready = () => {
          if (settled) return;
          try {
            const widgetId = renderHCaptcha();
            settled = true;
            cleanup();
            resolve(widgetId);
          } catch (error) {
            fail(error);
          }
        };
        window[callbackName] = ready;
        script.async = true;
        script.defer = true;
        script.dataset.nexgenHcaptcha = '';
        script.src = `https://js.hcaptcha.com/1/api.js?onload=${callbackName}&render=explicit&recaptchacompat=off`;
        script.onerror = () => fail(new Error('Verification could not load.'));
        timeoutId = window.setTimeout(() => fail(new Error('Verification timed out.')), 15000);
        document.head.append(script);
      });

      captchaLoadPromise = loading.catch((error) => {
        captchaLoadPromise = null;
        reportCaptchaLoadFailure();
        throw error;
      });
      return captchaLoadPromise;
    };

    const requestCaptchaLoad = () => {
      warmExternalOrigin('https://js.hcaptcha.com');
      loadHCaptcha().catch((error) => {
        console.error('hCaptcha failed to load:', error);
      });
    };

    if (captchaWidget) {
      if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
          if (!entries.some((entry) => entry.isIntersecting)) return;
          observer.disconnect();
          requestCaptchaLoad();
        }, { rootMargin: '650px 0px' });
        observer.observe(captchaWidget);
      } else {
        window.setTimeout(requestCaptchaLoad, 1200);
      }

      form.addEventListener('focusin', requestCaptchaLoad, { once: true });
      form.addEventListener('pointerdown', requestCaptchaLoad, { once: true, passive: true });
      form.addEventListener('touchstart', requestCaptchaLoad, { once: true, passive: true });
    }


    const setStatus = (message, type = 'neutral') => {
      if (!status) return;
      status.textContent = message;
      status.classList.remove('is-error', 'is-success', 'is-sending');
      if (type !== 'neutral') status.classList.add(`is-${type}`);
    };

    const errorElement = (field) => document.getElementById(`${field.id}-error`);
    const validateField = (field) => {
      const value = field.value.trim();
      let message = '';
      if (field.required && !value) message = `${field.dataset.label || 'This field'} is required.`;
      else if (field.type === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) message = 'Enter a valid email address.';
      const error = errorElement(field);
      field.setAttribute('aria-invalid', message ? 'true' : 'false');
      if (error) error.textContent = message;
      return !message;
    };

    requiredFields.forEach((field) => {
      field.addEventListener('blur', () => validateField(field));
      field.addEventListener('input', () => {
        if (field.getAttribute('aria-invalid') === 'true') validateField(field);
      });
    });

    let successReturnFocus = null;

    const successFocusable = () => successModal
      ? Array.from(
          successModal.querySelectorAll(
            'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
          )
        )
      : [];

    const openSuccess = () => {
      if (!successModal) return;
      successReturnFocus = submitButton || document.activeElement;
      successModal.classList.add('is-open');
      successModal.setAttribute('aria-hidden', 'false');
      successModal.setAttribute('aria-modal', 'true');
      if (nativeDialog(successModal)) successModal.showModal();
      else {
        successModal.setAttribute('open', '');
        isolateFallbackModal(successModal);
      }
      document.documentElement.classList.add('form-modal-open');
      document.body.classList.add('form-modal-open');
      window.setTimeout(() => successClose?.focus({ preventScroll: true }), 0);
    };

    const closeSuccess = (event) => {
      event?.preventDefault();
      if (!successModal?.classList.contains('is-open')) return;
      if (nativeDialog(successModal) && successModal.open) successModal.close();
      else successModal.removeAttribute('open');
      successModal.classList.remove('is-open');
      successModal.setAttribute('aria-hidden', 'true');
      successModal.removeAttribute('aria-modal');
      restoreFallbackModal(successModal);
      document.documentElement.classList.remove('form-modal-open');
      document.body.classList.remove('form-modal-open');

      const returnFocus = successReturnFocus;
      successReturnFocus = null;
      if (returnFocus instanceof HTMLElement && returnFocus.isConnected) {
        window.setTimeout(
          () => returnFocus.focus({ preventScroll: true }),
          0
        );
      }
    };

    successClose?.addEventListener('click', closeSuccess);
    successModal?.addEventListener('cancel', closeSuccess);
    successModal?.addEventListener('close', closeSuccess);
    successModal
      ?.querySelector('.form-success-backdrop')
      ?.addEventListener('click', closeSuccess);

    document.addEventListener('focusin', (event) => {
      if (!successModal?.classList.contains('is-open') || nativeDialog(successModal)) return;
      if (!successModal.contains(event.target)) successFocusable()[0]?.focus();
    });

    document.addEventListener('keydown', (event) => {
      if (!successModal?.classList.contains('is-open')) return;

      if (event.key === 'Escape') {
        event.preventDefault();
        closeSuccess();
        return;
      }

      if (nativeDialog(successModal)) return;
      if (event.key !== 'Tab') return;

      const focusable = successFocusable();
      if (!focusable.length) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });

    const parseFormspreeError = async (response) => {
      try {
        const data = await response.json();
        const messages = Array.isArray(data?.errors) ? data.errors.map((item) => item?.message).filter(Boolean) : [];
        if (typeof data?.error === 'string') messages.push(data.error);
        return messages.join(' ').trim();
      } catch {
        return '';
      }
    };

    let submissionInFlight = false;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (submissionInFlight) return;
      let firstInvalid = null;
      for (const field of requiredFields) {
        if (!validateField(field) && !firstInvalid) firstInvalid = field;
      }
      if (firstInvalid) {
        setStatus('Please correct the highlighted fields before sending.', 'error');
        firstInvalid.focus();
        return;
      }

      const honeypot = String(form.querySelector('[name="_gotcha"]')?.value || '').trim();
      if (honeypot) {
        form.reset();
        openSuccess();
        return;
      }

      submissionInFlight = true;
      const originalLabel = submitLabel?.textContent || 'Send Message';
      submitButton?.setAttribute('disabled', 'disabled');
      form.setAttribute('aria-busy', 'true');
      if (submitLabel) submitLabel.textContent = 'Checking…';
      let requestTimeoutId;
      let requestStarted = false;
      let requestTimedOut = false;

      try {
        let captchaToken = '';
        if (captchaWidget) {
          setStatus('Checking verification…', 'sending');
          try {
            await loadHCaptcha();
          } catch {
            setStatus('Verification could not load. Retry verification or email us directly.', 'error');
            scrollToElement(captchaWidget);
            return;
          }

          captchaToken = String(window.hcaptcha?.getResponse(captchaWidgetId) || '').trim();
          if (!captchaToken) {
            if (captchaError) captchaError.textContent = 'Complete the verification before sending.';
            setStatus('Please complete the verification before sending.', 'error');
            scrollToElement(captchaWidget);
            return;
          }
        }
        if (captchaError) captchaError.textContent = '';
        if (!endpoint) throw new Error('The message service is unavailable.');

        const data = new FormData(form);
        data.set('_replyto', String(data.get('email') || ''));
        data.set('_subject', 'New website message from NexGen Binary LLC');
        if (captchaWidget) data.set('h-captcha-response', captchaToken);

        if (submitLabel) submitLabel.textContent = 'Sending…';
        setStatus('Sending your message…', 'sending');
        const controller = typeof AbortController === 'function' ? new AbortController() : null;
        const deadline = new Promise((resolve, reject) => {
          requestTimeoutId = window.setTimeout(() => {
            requestTimedOut = true;
            controller?.abort();
            reject(new Error('The message request timed out.'));
          }, 20000);
        });
        requestStarted = true;
        const send = async () => {
          const response = await fetch(endpoint, {
            method: 'POST',
            headers: { Accept: 'application/json' },
            body: data,
            ...(controller ? { signal: controller.signal } : {})
          });
          if (!response.ok) {
            const detail = await parseFormspreeError(response);
            throw new Error(detail || `Request failed (${response.status}).`);
          }
        };
        await Promise.race([send(), deadline]);
        window.clearTimeout(requestTimeoutId);

        form.reset();
        requiredFields.forEach((field) => {
          field.setAttribute('aria-invalid', 'false');
          const error = errorElement(field);
          if (error) error.textContent = '';
        });
        if (window.hcaptcha?.reset) {
          try { window.hcaptcha.reset(captchaWidgetId); } catch {}
        }
        setStatus('', 'neutral');
        openSuccess();
        window.dispatchEvent(new CustomEvent('nexgen:contact-form-success'));
      } catch (error) {
        const detail = error instanceof Error ? error.message.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 180) : '';
        const message = requestTimedOut
          ? 'Delivery could not be confirmed because the request timed out. Please email or call us before resending.'
          : `Unable to send${detail ? `: ${detail}` : ' right now.'} Please try again or email us directly.`;
        setStatus(message, 'error');
        if (requestStarted && window.hcaptcha?.reset) {
          try { window.hcaptcha.reset(captchaWidgetId); } catch {}
        }
        window.dispatchEvent(new CustomEvent('nexgen:contact-form-error'));
        console.error('Contact form submission failed:', error);
      } finally {
        window.clearTimeout(requestTimeoutId);
        submissionInFlight = false;
        form.setAttribute('aria-busy', 'false');
        submitButton?.removeAttribute('disabled');
        if (submitLabel) submitLabel.textContent = originalLabel;
      }
    });
    // Keep native validation when JavaScript is unavailable; use linked inline
    // errors only after the complete enhanced submission handler is installed.
    form.noValidate = true;
  }

  const backToTop = document.querySelector('[data-back-to-top]');
  if (backToTop) {
    const updateBackToTop = () => {
      const visible = window.scrollY > 420;
      backToTop.classList.toggle('is-visible', visible);
      backToTop.tabIndex = visible ? 0 : -1;
      backToTop.setAttribute('aria-hidden', String(!visible));
    };
    backToTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: reducedMotion.matches ? 'auto' : 'smooth' });
    });
    updateBackToTop();
    window.addEventListener('scroll', updateBackToTop, { passive: true });
    window.addEventListener('pageshow', updateBackToTop);
  }
})();
