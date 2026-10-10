"use client";

import { useCallback, useEffect, useState } from "react";
import { asFailure, type Failure } from "./api";

export interface Resource<T> {
  data: T | null;
  failure: Failure | null;
  loading: boolean;
  reload: () => void;
}

/**
 * One read, three honest states.
 *
 * Deliberately not a data-fetching library: five endpoints, no shared cache and
 * no invalidation graph (research R3). What it does buy is that every view is
 * forced to handle loading, failure and loaded — no view can accidentally render
 * emptiness as success.
 */
export function useResource<T>(load: () => Promise<T>, deps: unknown[] = []): Resource<T> {
  const [data, setData] = useState<T | null>(null);
  const [failure, setFailure] = useState<Failure | null>(null);
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(load, deps);

  useEffect(() => {
    let current = true;
    setLoading(true);
    run()
      .then((value) => {
        if (!current) return;
        setData(value);
        setFailure(null);
      })
      .catch((error) => {
        if (!current) return;
        setData(null);
        setFailure(asFailure(error));
      })
      .finally(() => {
        if (current) setLoading(false);
      });
    return () => {
      current = false;
    };
  }, [run, attempt]);

  const reload = useCallback(() => setAttempt((n) => n + 1), []);

  return { data, failure, loading, reload };
}
