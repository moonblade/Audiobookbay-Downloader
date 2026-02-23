import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { ActiveTab } from '@/types';
import { SearchTab } from '@/components/SearchTab';
import { StatusTab } from '@/components/StatusTab';
import { GoodreadsTab } from '@/components/GoodreadsTab';

export default function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('search');
  const [title, setTitle] = useState('Search');
  const [goodreadsEnabled, setGoodreadsEnabled] = useState(false);
  const [torrentClientType, setTorrentClientType] = useState<string | null>(null);

  useEffect(() => {
    const init = async () => {
      try {
        const [titleRes, goodreadsRes, clientRes, roleRes] = await Promise.all([
          api.getTitle(),
          api.getGoodreadsEnabled(),
          api.getTorrentClientType(),
          api.getRole(),
        ]);

        setTitle(titleRes.title);
        document.title = titleRes.title;
        setGoodreadsEnabled(goodreadsRes.enabled);
        setTorrentClientType(clientRes.torrent_client_type);

        if (roleRes.role === null) {
          window.location.href = '/login';
        }
      } catch {
        window.location.href = '/login';
      }
    };

    init();
  }, []);

  const tabClasses = (tab: ActiveTab) =>
    activeTab === tab
      ? 'bg-gray-700 text-white px-4 py-2'
      : 'text-gray-400 px-4 py-2 hover:bg-gray-700 hover:text-white';
  return (
    <div className="bg-gray-800 text-white p-6 min-h-screen">
      <div className="max-w-3xl mx-auto mb-6 flex justify-center">
        <button
          onClick={() => setActiveTab('search')}
          className={`${tabClasses('search')} rounded-l`}
        >
          Search
        </button>
        <button
          onClick={() => setActiveTab('status')}
          className={tabClasses('status')}
        >
          Status
        </button>
        {goodreadsEnabled && (
          <button
            onClick={() => setActiveTab('goodreads')}
            className={`${tabClasses('goodreads')} rounded-r`}
          >
            Goodreads
          </button>
        )}
    </div>
      {activeTab === 'search' && <SearchTab title={title} />}
      {activeTab === 'status' && (
        <StatusTab
          isActive={activeTab === 'status'}
          torrentClientType={torrentClientType}
        />
      )}
      {activeTab === 'goodreads' && goodreadsEnabled && (
        <GoodreadsTab isActive={activeTab === 'goodreads'} />
      )}
    </div>
  );
}