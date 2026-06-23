/** Persisted auth/tenant state. localStorage keeps the session across reloads;
 *  swap for an httpOnly-cookie scheme if the threat model requires it. */

const ACCESS_KEY = "medraxis.access";
const REFRESH_KEY = "medraxis.refresh";
const ORG_KEY = "medraxis.org";

export const tokenStore = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  setTokens(access: string, refresh?: string) {
    localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export const orgStore = {
  get: () => localStorage.getItem(ORG_KEY),
  set: (slug: string | null) => {
    if (slug) localStorage.setItem(ORG_KEY, slug);
    else localStorage.removeItem(ORG_KEY);
  },
};
