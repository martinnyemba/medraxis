const ACCESS_KEY = "medraxis.access";
const REFRESH_KEY = "medraxis.refresh";
const ORG_KEY = "medraxis.org";

export const tokenStore = {
  getAccess(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  },
  getRefresh(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  },
  setTokens(access: string, refresh: string) {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  setAccess(access: string) {
    localStorage.setItem(ACCESS_KEY, access);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export const orgStore = {
  get(): string | null {
    return localStorage.getItem(ORG_KEY);
  },
  set(slug: string | null) {
    if (slug) {
      localStorage.setItem(ORG_KEY, slug);
    } else {
      localStorage.removeItem(ORG_KEY);
    }
  },
};
