/**
 * Clean query params by removing undefined, null, and empty string fields
 * @param {Record<string, any>} params
 * @returns {Record<string, any>}
 */
export function cleanQueryParams(params) {
  if (!params) return {};
  const clean = {};
  for (const [key, val] of Object.entries(params)) {
    if (val !== undefined && val !== null && val !== '') {
      clean[key] = val;
    }
  }
  return clean;
}

/**
 * Returns default date range in ISO-8601 UTC with 'Z'
 * @param {number} hours
 * @returns {{ from: string, to: string }}
 */
export function getDefaultDateRange(hours = 24) {
  const now = new Date();
  const past = new Date(now.getTime() - hours * 60 * 60 * 1000);
  return {
    from: past.toISOString(),
    to: now.toISOString(),
  };
}
