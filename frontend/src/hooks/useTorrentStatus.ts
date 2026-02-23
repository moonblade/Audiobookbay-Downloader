import { useState, useCallback, useEffect, useRef } from 'react';
import { api } from '@/lib/api';
import type { TorrentStatus, Candidate } from '@/types';
import { REFRESH_INTERVAL } from '@/types';

export function useTorrentStatus(isActive: boolean) {
  const [torrents, setTorrents] = useState<TorrentStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [deletingTorrent, setDeletingTorrent] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [torrentToDelete, setTorrentToDelete] = useState<string | null>(null);
  const [showCandidateDialog, setShowCandidateDialog] = useState(false);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedTorrent, setSelectedTorrent] = useState<TorrentStatus | null>(null);

  const timeoutRef = useRef<number | null>(null);

  const fetchTorrents = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listTorrents();
      setTorrents(data);
    } catch (err) {
      console.error('Failed to fetch torrents:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const scheduleRefresh = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    if (isActive) {
      timeoutRef.current = window.setTimeout(() => {
        fetchTorrents().then(() => scheduleRefresh());
      }, REFRESH_INTERVAL);
    }
  }, [isActive, fetchTorrents]);

  useEffect(() => {
    if (isActive) {
      fetchTorrents().then(() => scheduleRefresh());
    }
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [isActive, fetchTorrents, scheduleRefresh]);

  const promptDelete = useCallback((torrentId: string) => {
    setTorrentToDelete(torrentId);
    setConfirmDelete(true);
    setDeleteError(null);
  }, []);

  const cancelDelete = useCallback(() => {
    setConfirmDelete(false);
    setTorrentToDelete(null);
    setDeleteError(null);
  }, []);

  const confirmDeleteTorrent = useCallback(async () => {
    if (!torrentToDelete) return;

    setDeletingTorrent(torrentToDelete);
    setDeleteError(null);

    try {
      const response = await api.deleteTorrent(torrentToDelete, true);
      if (response.status !== 'ok') {
        throw new Error(response.message);
      }
      await fetchTorrents();
      setConfirmDelete(false);
      setTorrentToDelete(null);
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete');
    } finally {
      setDeletingTorrent(null);
    }
  }, [torrentToDelete, fetchTorrents]);

  const toggleTorrent = useCallback(
    async (torrentId: string, status: string) => {
      try {
        if (status === 'Stopped') {
          await api.resumeTorrent(torrentId);
        } else {
          await api.pauseTorrent(torrentId);
        }
        await fetchTorrents();
      } catch (err) {
        console.error('Failed to toggle torrent:', err);
      }
    },
    [fetchTorrents]
  );

  const showCandidates = useCallback((torrent: TorrentStatus) => {
    let torrentCandidates = torrent.candidates || [];
    if (torrentCandidates.length === 0) {
      torrentCandidates = [
        {
          match: 0,
          artist: '',
          album: 'Use as is',
          cover: '',
          id: 'asis',
          length: '',
        },
      ];
    }
    setCandidates(torrentCandidates);
    setSelectedTorrent(torrent);
    setShowCandidateDialog(true);
  }, []);

  const selectCandidate = useCallback(
    async (candidate: Candidate) => {
      if (!selectedTorrent) return;

      try {
        await api.selectCandidate(selectedTorrent.hash_string, candidate.id);
        await api.triggerAutoimport();
        await fetchTorrents();
      } catch (err) {
        console.error('Failed to select candidate:', err);
      } finally {
        setShowCandidateDialog(false);
      }
    },
    [selectedTorrent, fetchTorrents]
  );

  const closeCandidateDialog = useCallback(() => {
    setShowCandidateDialog(false);
  }, []);

  return {
    torrents,
    loading,
    deletingTorrent,
    deleteError,
    confirmDelete,
    torrentToDelete,
    showCandidateDialog,
    candidates,
    selectedTorrent,
    fetchTorrents,
    promptDelete,
    cancelDelete,
    confirmDeleteTorrent,
    toggleTorrent,
    showCandidates,
    selectCandidate,
    closeCandidateDialog,
  };
}
