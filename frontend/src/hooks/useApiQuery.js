import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook for data fetching with loading, error, success states, and abort on unmount.
 * @template T
 * @param {() => Promise<T>} queryFn - Async function returning data
 * @param {Array<any>} deps - Dependencies array triggering refetch
 * @param {{ enabled?: boolean }} options - Options
 * @returns {{ data: T | null, error: any, isLoading: boolean, refetch: () => Promise<void> }}
 */
export function useApiQuery(queryFn, deps = [], options = { enabled: true }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(Boolean(options.enabled !== false));

  // Ref to track component mount status
  const isMountedRef = useRef(true);
  const queryFnRef = useRef(queryFn);
  queryFnRef.current = queryFn;

  const execute = useCallback(async () => {
    if (options.enabled === false) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await queryFnRef.current();
      if (isMountedRef.current) {
        setData(result);
        setError(null);
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err);
      }
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [options.enabled]);

  useEffect(() => {
    isMountedRef.current = true;
    if (options.enabled !== false) {
      execute();
    }
    return () => {
      isMountedRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [execute, ...deps]);

  const refetch = useCallback(() => execute(), [execute]);

  return { data, error, isLoading, refetch };
}

export default useApiQuery;
