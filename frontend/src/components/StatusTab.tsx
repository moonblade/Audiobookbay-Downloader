import { useTorrentStatus } from '@/hooks';
import { Button } from '@/components/ui/button';
import { CandidateDialog } from '@/components/CandidateDialog';
import { DeleteConfirmDialog } from '@/components/DeleteConfirmDialog';
import type { TorrentStatus } from '@/types';

interface StatusTabProps {
  isActive: boolean;
  torrentClientType: string | null;
}

function formatEta(seconds?: number): string {
  if (!seconds || seconds < 0) return 'Unknown';
  if (seconds < 60) return seconds + ' sec';
  if (seconds < 3600) return Math.floor(seconds / 60) + ' min';
  return Math.floor(seconds / 3600) + ' hr ' + Math.floor((seconds % 3600) / 60) + ' min';
}

function formatSize(bytes: number): string {
  return (bytes / 1024 / 1024).toFixed(2) + ' MB';
}

function getProgressBarStyle(torrent: TorrentStatus) {
  const isStopped = torrent.status === 'Stopped';

  let width: string;
  let backgroundColor: string;

  if (isStopped) {
    width = `${torrent.percent_done}%`;
    backgroundColor = '#a0aec0';
  } else if (torrent.upload_ratio > 0) {
    width = `${torrent.upload_ratio * 100}%`;
    backgroundColor = '#065f46';
  } else {
    width = `${torrent.percent_done}%`;
    backgroundColor = '#4ade80';
  }

  return { width, backgroundColor };
}

export function StatusTab({ isActive, torrentClientType }: StatusTabProps) {
  const {
    torrents,
    loading,
    deletingTorrent,
    deleteError,
    confirmDelete,
    showCandidateDialog,
    candidates,
    promptDelete,
    cancelDelete,
    confirmDeleteTorrent,
    toggleTorrent,
    showCandidates,
    selectCandidate,
    closeCandidateDialog,
  } = useTorrentStatus(isActive);

  return (
    <div className="max-w-3xl mx-auto mt-6 px-2">
      <h2 className="text-2xl font-bold mb-4">Torrent Status</h2>

      {torrents.map((torrent) => (
        <div key={torrent.id} className="bg-gray-700 p-4 rounded-lg shadow-md mb-3">
          <div className="flex justify-between items-start mb-2">
            <div className="flex items-center gap-2 flex-1">
              <div className="flex-shrink-0">
                {torrent.status === 'Seeding' && (
                  <i className="fas fa-arrow-up text-green-500" />
                )}
                {torrent.status === 'Downloading' && (
                  <i className="fas fa-arrow-down text-blue-500" />
                )}
                {torrent.status === 'Stopped' && (
                  <i className="fas fa-pause text-gray-500" />
                )}
              </div>
              <h3 className="font-bold text-sm sm:text-base break-words pr-2">
                {torrent.name}
              </h3>
            </div>
            {torrent.use_beets_import && (
              <div className="flex items-center gap-2">
                {torrent.status === 'Seeding' && torrent.importError && (
                  <i
                    className="fas fa-exclamation-circle text-red-500 cursor-pointer"
                    title="Import Error"
                    onClick={() => showCandidates(torrent)}
                  />
                )}
                {torrent.status === 'Seeding' && !torrent.imported && !torrent.importError && (
                  <i className="fas fa-question-circle text-yellow-500" title="Not Imported" />
                )}
                {torrent.status === 'Seeding' && torrent.imported && !torrent.importError && (
                  <i className="fas fa-check-circle text-green-500" title="Imported" />
                )}
              </div>
            )}
          </div>

          <div
            className="h-4 w-full rounded-full overflow-hidden mb-3"
            style={{
              backgroundColor: torrent.status === 'Seeding' ? '#4ade80' : '#e2e8f0',
            }}
          >
            <div
              className="h-full rounded-full"
              style={getProgressBarStyle(torrent)}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-400 flex-1 mr-2">
              <div>Size: {formatSize(torrent.total_size)}</div>
              {torrent.added_by && (
                <div>
                  Added: {torrent.added_by.charAt(0).toUpperCase() + torrent.added_by.slice(1)}
                </div>
              )}
              {torrent.upload_ratio > 0 && (
                <div>Ratio: {torrent.upload_ratio.toFixed(2)}</div>
              )}
              {torrent.percent_done > 0 && torrent.percent_done < 100 && (
                <div>Progress: {torrent.percent_done.toFixed(1)}%</div>
              )}
              {torrent.status === 'Downloading' && torrent.eta && (
                <div>ETA: {formatEta(torrent.eta)}</div>
              )}
            </div>

            <div className="flex items-center gap-2 flex-shrink-0">
              {torrentClientType !== 'decypharr' && (
                <Button
                  onClick={() => toggleTorrent(torrent.id, torrent.status)}
                  disabled={deletingTorrent === torrent.id}
                  variant="secondary"
                  size="icon"
                  className="bg-gray-600 hover:bg-gray-500 text-gray-300 h-8 w-8"
                >
                  <i className={torrent.status === 'Stopped' ? 'fas fa-play' : 'fas fa-pause'} />
                </Button>
              )}
              <Button
                onClick={() => promptDelete(torrent.id)}
                disabled={deletingTorrent === torrent.id}
                variant="secondary"
                size="icon"
                className="bg-gray-600 hover:bg-gray-500 text-gray-300 h-8 w-8"
              >
                {deletingTorrent === torrent.id ? (
                  <span className="animate-spin border-2 border-white border-t-transparent rounded-full w-4 h-4" />
                ) : (
                  <i className="fas fa-trash-alt" />
                )}
              </Button>
            </div>
          </div>
        </div>
      ))}

      {loading && (
        <p className="text-center text-gray-400">Loading torrent status...</p>
      )}

      {deleteError && (
        <p className="text-red-500 mt-2">{deleteError}</p>
      )}

      <DeleteConfirmDialog
        isOpen={confirmDelete}
        isDeleting={!!deletingTorrent}
        onConfirm={confirmDeleteTorrent}
        onCancel={cancelDelete}
      />

      <CandidateDialog
        isOpen={showCandidateDialog}
        candidates={candidates}
        onSelect={selectCandidate}
        onClose={closeCandidateDialog}
      />
    </div>
  );
}
