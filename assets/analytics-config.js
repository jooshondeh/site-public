// The deployment workflow injects the GitHub repository variable GA4_MEASUREMENT_ID.
// Expected format: G-ABC123DE45
window.NEXGEN_ANALYTICS_CONFIG = Object.freeze({
  googleAnalyticsMeasurementId: String(window.NEXGEN_GA4_MEASUREMENT_ID || '').trim(),
  requireConsent: true,
  respectDoNotTrack: true
});
