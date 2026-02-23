import { useSearch } from '@/hooks';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface SearchTabProps {
  title: string;
}

export function SearchTab({ title }: SearchTabProps) {
  const {
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
  } = useSearch();

  const handleKeyDown = (e: React.KeyboardEvent) => {
    resetSearch();
    if (e.key === 'Enter') {
      search();
    }
  };

  const formatSize = (bytes: number) => {
    return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB';
  };

  const getUrl = (result: { MagnetUri?: string; Link?: string }) => {
    return result.MagnetUri || result.Link || '';
  };

  return (
    <div className="max-w-3xl mx-auto mt-6">
      <h2 className="text-2xl font-bold mb-4">{title}</h2>

      <div className="flex gap-2">
        <Input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          autoComplete="off"
          className="flex-grow bg-gray-600 text-white border-gray-600"
          placeholder="Search..."
        />
        <Button
          onClick={search}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          {loading && (
            <span className="animate-spin border-2 border-white border-t-transparent rounded-full w-4 h-4 mr-2" />
          )}
          Search
        </Button>
      </div>

      {error && (
        <p className={error === 'Successfully added torrent!' ? 'text-green-500 mt-2' : 'text-red-500 mt-2'}>
          {error}
        </p>
      )}

      {loading && currentFunnyMessage && (
        <p className="text-gray-400 mt-2 italic">{currentFunnyMessage}</p>
      )}

      {results.length > 0 && (
        <div className="max-w-3xl mx-auto mt-6">
          {results.map((result) => {
            const url = getUrl(result);
            return (
              <div key={result.Guid}>
                <div className="bg-gray-700 p-4 rounded shadow mb-2 flex items-center gap-4">
                  {result.Poster && (
                    <img
                      src={result.Poster}
                      alt=""
                      className="w-16 h-16 object-cover rounded"
                    />
                  )}
                  <div className="flex-grow w-3/4">
                    <h2 className="font-bold break-words">{result.Title}</h2>
                    <p className="text-sm text-gray-400">
                      Size: {formatSize(result.Size)}
                    </p>
                  </div>
                  <Button
                    onClick={() => add(url)}
                    disabled={loadingAdd[url]}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    {loadingAdd[url] && (
                      <span className="animate-spin border-2 border-white border-t-transparent rounded-full w-4 h-4 mr-2" />
                    )}
                    Add
                  </Button>
                </div>
                {addError[url] && (
                  <p className="text-red-500 text-sm mt-1">{addError[url]}</p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {complete && results.length === 0 && query && (
        <p className="max-w-xl mx-auto mt-6 text-center text-gray-400">
          No results found. Try a different search term!
        </p>
      )}
    </div>
  );
}
