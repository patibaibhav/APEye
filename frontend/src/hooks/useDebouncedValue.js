import { useState, useEffect } from 'react';

/**
 * Hook to debounce value changes
 * @template T
 * @param {T} value
 * @param {number} delay
 * @returns {T}
 */
export function useDebouncedValue(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export default useDebouncedValue;
