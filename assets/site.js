(() => {
  'use strict';


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

  const currentHashId = () => decodeURIComponent(window.location.hash.slice(1));
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

  const closeNav = () => {
    if (!toggle || !nav) return;
    nav.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
  };

  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = !nav.classList.contains('is-open');
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
    });
    document.addEventListener('click', (event) => {
      if (!mobileBreakpoint.matches || !nav.classList.contains('is-open')) return;
      if (header && header.contains(event.target)) return;
      closeNav();
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeNav();
    });
    mobileBreakpoint.addEventListener?.('change', closeNav);
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
      link.classList.toggle('is-active', link.getAttribute('href') === `#${current}`);
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

    window.addEventListener('scroll', () => {
      if (mobileBreakpoint.matches && nav?.classList.contains('is-open')) closeNav();
      scheduleSectionUpdate();
    }, { passive: true });

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
    event.preventDefault();
    bookingReturnFocus = event.currentTarget || document.activeElement;
    if (!bookingFrame.src) bookingFrame.src = bookingFrame.dataset.src || '';
    closeNav();
    bookingModal.classList.add('is-open');
    bookingModal.setAttribute('aria-hidden', 'false');
    document.documentElement.classList.add('nb-modal-open');
    document.body.classList.add('nb-modal-open');
    window.setTimeout(() => bookingModal.querySelector('.nb-booking-close')?.focus({ preventScroll: true }), 0);
  };

  const closeBooking = (event) => {
    event?.preventDefault();
    if (!bookingModal) return;
    bookingModal.classList.remove('is-open');
    bookingModal.setAttribute('aria-hidden', 'true');
    document.documentElement.classList.remove('nb-modal-open');
    document.body.classList.remove('nb-modal-open');
    if (bookingReturnFocus instanceof HTMLElement) {
      window.setTimeout(() => bookingReturnFocus.focus({ preventScroll: true }), 0);
    }
  };

  bookingOpeners.forEach((opener) => opener.addEventListener('click', openBooking));
  bookingClosers.forEach((closer) => closer.addEventListener('click', closeBooking));

  document.addEventListener('keydown', (event) => {
    if (!bookingModal?.classList.contains('is-open')) return;
    if (event.key === 'Escape') {
      closeBooking(event);
      return;
    }
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
    const captchaLoadStatus = captchaWidget?.querySelector('[data-hcaptcha-load-status]');
    const captchaSitekey = captchaWidget?.dataset.sitekey || '';
    let captchaWidgetId = null;
    let captchaLoadPromise = null;

    const setCaptchaLoadStatus = (message, busy = false) => {
      if (captchaWidget) captchaWidget.setAttribute('aria-busy', busy ? 'true' : 'false');
      if (captchaLoadStatus?.isConnected) captchaLoadStatus.textContent = message;
    };

    const renderHCaptcha = () => {
      if (!captchaWidget || captchaWidgetId !== null) return captchaWidgetId;
      if (!window.hcaptcha?.render || !captchaSitekey) {
        throw new Error('Verification could not initialize.');
      }

      captchaWidget.replaceChildren();
      captchaWidget.setAttribute('aria-busy', 'false');
      captchaWidgetId = window.hcaptcha.render(captchaWidget, {
        sitekey: captchaSitekey,
        size: window.matchMedia('(max-width: 380px)').matches ? 'compact' : 'normal',
        theme: 'light',
        'error-callback': () => {
          if (captchaError) captchaError.textContent = 'Verification encountered an error. Please retry or email us directly.';
        },
        'expired-callback': () => {
          if (captchaError) captchaError.textContent = 'Verification expired. Please complete it again.';
        }
      });
      return captchaWidgetId;
    };

    const loadHCaptcha = () => {
      if (!captchaWidget) return Promise.resolve(null);
      if (captchaWidgetId !== null) return Promise.resolve(captchaWidgetId);
      if (window.hcaptcha?.render) return Promise.resolve(renderHCaptcha());
      if (captchaLoadPromise) return captchaLoadPromise;

      setCaptchaLoadStatus('Loading verification…', true);
      captchaLoadPromise = new Promise((resolve, reject) => {
        const callbackName = 'nexgenHCaptchaReady';
        const existingScript = document.querySelector('script[data-nexgen-hcaptcha]');

        window[callbackName] = () => {
          try {
            resolve(renderHCaptcha());
          } catch (error) {
            captchaLoadPromise = null;
            reject(error);
          } finally {
            try { delete window[callbackName]; } catch {}
          }
        };

        if (existingScript) return;

        const script = document.createElement('script');
        script.async = true;
        script.defer = true;
        script.dataset.nexgenHcaptcha = '';
        script.src = `https://js.hcaptcha.com/1/api.js?onload=${callbackName}&render=explicit&recaptchacompat=off`;
        script.onerror = () => {
          captchaLoadPromise = null;
          script.remove();
          setCaptchaLoadStatus('Verification could not load. Please retry or email us directly.', false);
          reject(new Error('Verification could not load.'));
        };
        document.head.append(script);
      });

      return captchaLoadPromise;
    };

    const requestCaptchaLoad = () => {
      loadHCaptcha().catch((error) => {
        console.error('hCaptcha failed to load:', error);
        if (captchaError) captchaError.textContent = 'Verification could not load. Please retry or email us directly.';
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
      document.documentElement.classList.add('form-modal-open');
      document.body.classList.add('form-modal-open');
      window.setTimeout(() => successClose?.focus({ preventScroll: true }), 0);
    };

    const closeSuccess = () => {
      if (!successModal) return;
      successModal.classList.remove('is-open');
      successModal.setAttribute('aria-hidden', 'true');
      document.documentElement.classList.remove('form-modal-open');
      document.body.classList.remove('form-modal-open');

      if (successReturnFocus instanceof HTMLElement) {
        window.setTimeout(
          () => successReturnFocus.focus({ preventScroll: true }),
          0
        );
      }
    };

    successClose?.addEventListener('click', closeSuccess);
    successModal
      ?.querySelector('.form-success-backdrop')
      ?.addEventListener('click', closeSuccess);

    document.addEventListener('keydown', (event) => {
      if (!successModal?.classList.contains('is-open')) return;

      if (event.key === 'Escape') {
        event.preventDefault();
        closeSuccess();
        return;
      }

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

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
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

      if (captchaWidget) {
        try {
          await loadHCaptcha();
        } catch {
          if (captchaError) captchaError.textContent = 'Verification could not load. Please retry or email us directly.';
          setStatus('Verification could not load. Please retry or email us directly.', 'error');
          captchaWidget.scrollIntoView({ behavior: 'smooth', block: 'center' });
          return;
        }

        const captchaToken = String(window.hcaptcha?.getResponse(captchaWidgetId) || '').trim();
        if (!captchaToken) {
          if (captchaError) captchaError.textContent = 'Complete the verification before sending.';
          setStatus('Please complete the verification before sending.', 'error');
          captchaWidget.scrollIntoView({ behavior: 'smooth', block: 'center' });
          return;
        }
      }
      if (captchaError) captchaError.textContent = '';

      const data = new FormData(form);
      data.set('_replyto', String(data.get('email') || ''));
      data.set('_subject', 'New website message from NexGen Binary LLC');

      const originalLabel = submitLabel?.textContent || 'Send Message';
      submitButton?.setAttribute('disabled', 'disabled');
      if (submitLabel) submitLabel.textContent = 'Sending…';
      setStatus('Sending your message…', 'sending');

      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { Accept: 'application/json' },
          body: data
        });
        if (!response.ok) {
          const detail = await parseFormspreeError(response);
          throw new Error(detail || `Request failed (${response.status}).`);
        }

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
        setStatus(detail ? `Unable to send: ${detail}` : 'Unable to send right now. Please try again or use the email link.', 'error');
        window.dispatchEvent(new CustomEvent('nexgen:contact-form-error'));
        console.error('Contact form submission failed:', error);
      } finally {
        submitButton?.removeAttribute('disabled');
        if (submitLabel) submitLabel.textContent = originalLabel;
      }
    });
  }

  const backToTop = document.querySelector('[data-back-to-top]');
  if (backToTop) {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
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
