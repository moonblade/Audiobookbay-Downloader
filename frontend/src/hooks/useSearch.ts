import { useState, useCallback, useRef, useEffect } from 'react';
import { api } from '@/lib/api';
import type { SearchResult } from '@/types';
import { FUNNY_MESSAGES, FUNNY_MESSAGE_INTERVAL } from '@/types';

export function useSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [complete, setComplete] = useState(false);
  const [error, setError] = useState('');
  const [currentFunnyMessage, setCurrentFunnyMessage] = useState('');
  const [loadingAdd, setLoadingAdd] = useState<Record<string, boolean>>({});
  const [addError, setAddError] = useState<Record<string, string>>({});
  
  const messageIntervalRef = useRef<number | null>(null);

  const clearMessageInterval = useCallback(() => {
    if (messageIntervalRef.current) {
      clearInterval(messageIntervalRef.current);
      messageIntervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => clearMessageInterval();
  }, [clearMessageInterval]);

  const search = useCallback(async () => {
    if (!query.trim()) return;

    setLoading(true);
    setComplete(false);
    setError('');
    setResults([]);

    const shuffled = [...FUNNY_MESSAGES].sort(() => Math.random() - 0.5);
    let index = 0;
    setCurrentFunnyMessage(shuffled[0]);

    messageIntervalRef.current = window.setInterval(() => {
      index++;
      setCurrentFunnyMessage(shuffled[index % shuffled.length]);
    }, FUNNY_MESSAGE_INTERVAL);

    try {
      const data = await api.search(query);
      setResults(data.results || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setComplete(true);
      setLoading(false);
      clearMessageInterval();
      setCurrentFunnyMessage('');
    }
  }, [query, clearMessageInterval]);

  const add = useCallback(async (url: string) => {
    setLoadingAdd((prev) => ({ ...prev, [url]: true }));
    setAddError((prev) => ({ ...prev, [url]: '' }));
    setError('');

    try {
      const data = await api.addTorrent(url);
      if (data.status !== 'ok') {
        throw new Error(data.message || 'Error adding torrent');
      }
      setComplete(false);
      setError('Successfully added torrent!');
    } catch (err) {
      setAddError((prev) => ({
        ...prev,
        [url]: err instanceof Error ? err.message : 'Failed to add',
      }));
    } finally {
      setLoadingAdd((prev) => ({ ...prev, [url]: false }));
    }
  }, []);

  const resetSearch = useCallback(() => {
    setComplete(false);
  }, []);

  return {
    query,
    setQuery,
    results,
    loading,
    complete,
    error,
    currentFunnyMessage,
    loadingAdd,
    addError,
    search,
    add,
    resetSearch,
  };
}
