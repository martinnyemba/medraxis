import * as React from "react";

/** Debounce a rapidly-changing value (e.g. a search box) by `delay` ms. */
export function useDebounce<T>(value: T, delay = 350): T {
  const [debounced, setDebounced] = React.useState(value);
  React.useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(id);
  }, [value, delay]);
  return debounced;
}
