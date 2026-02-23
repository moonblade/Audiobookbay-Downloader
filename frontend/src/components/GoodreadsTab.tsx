import { useGoodreads } from '@/hooks';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface GoodreadsTabProps {
  isActive: boolean;
}

export function GoodreadsTab({ isActive }: GoodreadsTabProps) {
  const {
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
  } = useGoodreads(isActive);

  const handleClearAllBooks = () => {
    if (confirm('Are you sure you want to clear all processed books? This will allow re-downloading.')) {
      clearAllBooks();
    }
  };

  return (
    <div className="max-w-3xl mx-auto mt-6 px-2">
      <h2 className="text-2xl font-bold mb-4">Goodreads Integration</h2>

      {error && <p className="text-red-500 mb-4">{error}</p>}
      {success && <p className="text-green-500 mb-4">{success}</p>}

      {/* Configuration Section */}
      <div className="bg-gray-700 p-4 rounded-lg mb-4">
        <h3 className="text-lg font-semibold mb-3">Configuration</h3>

        <div className="space-y-3">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Goodreads User ID</label>
            <Input
              type="text"
              value={config.user_id}
              onChange={(e) => updateConfig({ user_id: e.target.value })}
              className="w-full p-2 rounded bg-gray-600 text-white border-gray-500"
              placeholder="e.g., 54722780"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Shelf Name</label>
            <Input
              type="text"
              value={config.shelf}
              onChange={(e) => updateConfig({ shelf: e.target.value })}
              className="w-full p-2 rounded bg-gray-600 text-white border-gray-500"
              placeholder="to-read"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Poll Interval (minutes)</label>
            <Input
              type="number"
              value={config.poll_interval}
              onChange={(e) => updateConfig({ poll_interval: parseInt(e.target.value) || 60 })}
              min={1}
              className="w-full p-2 rounded bg-gray-600 text-white border-gray-500"
              placeholder="60"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={config.enabled}
              onChange={(e) => updateConfig({ enabled: e.target.checked })}
              id="goodreads-enabled"
              className="w-4 h-4"
            />
            <label htmlFor="goodreads-enabled" className="text-sm">
              Enable automatic polling
            </label>
          </div>
        </div>

        <div className="flex gap-2 mt-4">
          <Button
            onClick={validateConfig}
            disabled={loading}
            className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 disabled:opacity-50"
          >
            {loading && !pollingNow && (
              <span className="animate-spin border-2 border-white border-t-transparent rounded-full w-4 h-4 mr-2" />
            )}
            Validate
          </Button>
          <Button
            onClick={saveConfig}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 disabled:opacity-50"
          >
            {loading && !pollingNow && (
              <span className="animate-spin border-2 border-white border-t-transparent rounded-full w-4 h-4 mr-2" />
            )}
            Save
          </Button>
          <Button
            onClick={triggerPoll}
            disabled={pollingNow || !config.user_id}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 disabled:opacity-50"
          >
            {pollingNow && (
              <span className="animate-spin border-2 border-white border-t-transparent rounded-full w-4 h-4 mr-2" />
            )}
            Poll Now
          </Button>
        </div>

        {validationResult && (
          <div
            className={`mt-3 p-3 rounded ${
              validationResult.valid ? 'bg-green-900' : 'bg-red-900'
            }`}
          >
            <p>{validationResult.message}</p>
            {validationResult.book_count !== undefined && (
              <p className="text-sm text-gray-300">
                Books found: {validationResult.book_count}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Last Poll Status Section */}
      {config.last_poll && (
        <div className="bg-gray-700 p-4 rounded-lg mb-4">
          <h3 className="text-lg font-semibold mb-2">Last Poll Status</h3>
          <div className="text-sm text-gray-400 space-y-1">
            <p>
              Time:{' '}
              <span className="text-white">
                {new Date(config.last_poll).toLocaleString()}
              </span>
            </p>
            <p>
              Status:{' '}
              <span
                className={
                  config.last_poll_status === 'success'
                    ? 'text-green-400'
                    : 'text-red-400'
                }
              >
                {config.last_poll_status}
              </span>
            </p>
            {config.last_poll_message && (
              <p>
                Message: <span className="text-white">{config.last_poll_message}</span>
              </p>
            )}
          </div>
        </div>
      )}

      {/* Processed Books Section */}
      <div className="bg-gray-700 p-4 rounded-lg">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-lg font-semibold">
            Processed Books ({processedBooks.length})
          </h3>
          {processedBooks.length > 0 && (
            <Button
              onClick={handleClearAllBooks}
              className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 text-sm"
            >
              Clear All
            </Button>
          )}
        </div>

        {processedBooks.length === 0 && (
          <p className="text-gray-400 text-sm">No books processed yet.</p>
        )}

        <div className="space-y-2 max-h-96 overflow-y-auto">
          {processedBooks.map((book) => (
            <div
              key={book.book_id}
              className="flex items-center justify-between bg-gray-600 p-3 rounded"
            >
              <div className="flex-1">
                <p className="font-semibold">{book.title}</p>
                <p className="text-sm text-gray-400">{book.author}</p>
                <p
                  className={`text-xs ${
                    book.status === 'downloaded' ? 'text-green-400' : 'text-yellow-400'
                  }`}
                >
                  {book.status === 'downloaded' ? '✓ Downloaded' : '⚠ No results'}
                  {book.torrent_name && (
                    <span className="text-gray-500"> - {book.torrent_name}</span>
                  )}
                </p>
              </div>
              <Button
                onClick={() => deleteBook(book.book_id)}
                className="bg-gray-500 hover:bg-gray-400 text-white px-2 py-1 text-sm ml-2"
                title="Remove (allows re-download)"
              >
                <i className="fas fa-redo" />
              </Button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
