import { useState, useCallback, useEffect } from 'react';
import { api } from '@/lib/api';
import type { GoodreadsConfig, ProcessedBook, ValidationResult } from '@/types';

const DEFAULT_CONFIG: GoodreadsConfig = {
  user_id: '',
  shelf: 'to-read',
  poll_interval: 60,
  enabled: false,
  last_poll: null,
  last_poll_status: null,
  last_poll_message: null,
};

export function useGoodreads(isActive: boolean) {
  const [config, setConfig] = useState<GoodreadsConfig>(DEFAULT_CONFIG);
  const [processedBooks, setProcessedBooks] = useState<ProcessedBook[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [pollingNow, setPollingNow] = useState(false);

  const fetchConfig = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getGoodreadsConfig();
      setConfig(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch config');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchProcessedBooks = useCallback(async () => {
    try {
      const books = await api.getProcessedBooks();
      setProcessedBooks(books);
    } catch (err) {
      console.error('Error fetching processed books:', err);
    }
  }, []);

  useEffect(() => {
    if (isActive) {
      fetchConfig();
      fetchProcessedBooks();
    }
  }, [isActive, fetchConfig, fetchProcessedBooks]);

  const saveConfig = useCallback(async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const result = await api.saveGoodreadsConfig({
        user_id: config.user_id,
        shelf: config.shelf,
        poll_interval: config.poll_interval,
        enabled: config.enabled,
      });
      setConfig(result);
      setSuccess('Configuration saved successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save config');
    } finally {
      setLoading(false);
    }
  }, [config]);

  const validateConfig = useCallback(async () => {
    setLoading(true);
    setValidationResult(null);
    setError('');
    try {
      const result = await api.validateGoodreadsConfig({
        user_id: config.user_id,
        shelf: config.shelf,
      });
      setValidationResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Validation failed');
    } finally {
      setLoading(false);
    }
  }, [config.user_id, config.shelf]);

  const triggerPoll = useCallback(async () => {
    setPollingNow(true);
    setError('');
    setSuccess('');
    try {
      const result = await api.triggerGoodreadsPoll();
      setSuccess(result.message || 'Poll completed');
      await fetchConfig();
      await fetchProcessedBooks();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Poll failed');
    } finally {
      setPollingNow(false);
    }
  }, [fetchConfig, fetchProcessedBooks]);

  const deleteBook = useCallback(
    async (bookId: string) => {
      try {
        await api.deleteProcessedBook(bookId);
        await fetchProcessedBooks();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete book');
      }
    },
    [fetchProcessedBooks]
  );

  const clearAllBooks = useCallback(async () => {
    try {
      await api.clearAllProcessedBooks();
      await fetchProcessedBooks();
      setSuccess('All processed books cleared');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clear books');
    }
  }, [fetchProcessedBooks]);

  const updateConfig = useCallback((updates: Partial<GoodreadsConfig>) => {
    setConfig((prev) => ({ ...prev, ...updates }));
  }, []);

  return {
    config,
    processedBooks,
    loading,
    error,
    success,
    validationResult,
    pollingNow,
    saveConfig,
    validateConfig,
    triggerPoll,
    deleteBook,
    clearAllBooks,
    updateConfig,
  };
}
