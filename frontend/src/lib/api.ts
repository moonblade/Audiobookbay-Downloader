import type {
  SearchResponse,
  TorrentStatus,
  TitleResponse,
  RoleResponse,
  TorrentClientTypeResponse,
  GoodreadsEnabledResponse,
  GoodreadsConfig,
  ProcessedBook,
  ValidationResult,
  AddTorrentResponse,
  DeleteTorrentResponse,
  PollResponse,
  SelectCandidateResponse,
  AutoimportResponse,
  GoodreadsConfigRequest,
  GoodreadsValidateRequest,
} from '@/types';

const BASE_URL = '';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function search(query: string): Promise<SearchResponse> {
  return fetchJson<SearchResponse>(`/search?query=${encodeURIComponent(query)}`);
}

export async function getTitle(): Promise<TitleResponse> {
  return fetchJson<TitleResponse>('/title');
}

export async function getRole(): Promise<RoleResponse> {
  return fetchJson<RoleResponse>('/role');
}

export async function getTorrentClientType(): Promise<TorrentClientTypeResponse> {
  return fetchJson<TorrentClientTypeResponse>('/torrent-client-type');
}

export async function getGoodreadsEnabled(): Promise<GoodreadsEnabledResponse> {
  return fetchJson<GoodreadsEnabledResponse>('/goodreads-enabled');
}

export async function listTorrents(): Promise<TorrentStatus[]> {
  return fetchJson<TorrentStatus[]>('/list');
}

export async function addTorrent(url: string): Promise<AddTorrentResponse> {
  return fetchJson<AddTorrentResponse>('/add', {
    method: 'POST',
    body: JSON.stringify({ url }),
  });
}

export async function deleteTorrent(
  torrentId: string,
  deleteData: boolean = true
): Promise<DeleteTorrentResponse> {
  return fetchJson<DeleteTorrentResponse>(
    `/torrent/${torrentId}?delete_data=${deleteData}`,
    { method: 'DELETE' }
  );
}

export async function pauseTorrent(torrentId: string): Promise<{ status: string; message: string }> {
  return fetchJson(`/torrent/${torrentId}/pause`, { method: 'POST' });
}

export async function resumeTorrent(torrentId: string): Promise<{ status: string; message: string }> {
  return fetchJson(`/torrent/${torrentId}/play`, { method: 'POST' });
}

export async function selectCandidate(
  hashString: string,
  candidateId: string
): Promise<SelectCandidateResponse> {
  return fetchJson<SelectCandidateResponse>(
    `/selectCandidate/${hashString}/${candidateId}`,
    { method: 'POST' }
  );
}

export async function triggerAutoimport(): Promise<AutoimportResponse> {
  return fetchJson<AutoimportResponse>('/autoimport', { method: 'POST' });
}

export async function getGoodreadsConfig(): Promise<GoodreadsConfig> {
  return fetchJson<GoodreadsConfig>('/goodreads/config');
}

export async function saveGoodreadsConfig(
  config: GoodreadsConfigRequest
): Promise<GoodreadsConfig> {
  return fetchJson<GoodreadsConfig>('/goodreads/config', {
    method: 'POST',
    body: JSON.stringify(config),
  });
}

export async function validateGoodreadsConfig(
  config: GoodreadsValidateRequest
): Promise<ValidationResult> {
  return fetchJson<ValidationResult>('/goodreads/validate', {
    method: 'POST',
    body: JSON.stringify(config),
  });
}

export async function triggerGoodreadsPoll(): Promise<PollResponse> {
  return fetchJson<PollResponse>('/goodreads/poll', { method: 'POST' });
}

export async function getProcessedBooks(): Promise<ProcessedBook[]> {
  return fetchJson<ProcessedBook[]>('/goodreads/books');
}

export async function deleteProcessedBook(
  bookId: string
): Promise<{ status: string; message: string }> {
  return fetchJson(`/goodreads/books/${bookId}`, { method: 'DELETE' });
}

export async function clearAllProcessedBooks(): Promise<{ status: string; message: string }> {
  return fetchJson('/goodreads/books', { method: 'DELETE' });
}

export const api = {
  search,
  getTitle,
  getRole,
  getTorrentClientType,
  getGoodreadsEnabled,
  listTorrents,
  addTorrent,
  deleteTorrent,
  pauseTorrent,
  resumeTorrent,
  selectCandidate,
  triggerAutoimport,
  getGoodreadsConfig,
  saveGoodreadsConfig,
  validateGoodreadsConfig,
  triggerGoodreadsPoll,
  getProcessedBooks,
  deleteProcessedBook,
  clearAllProcessedBooks,
};
