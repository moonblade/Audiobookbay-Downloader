// API Response Types

export interface SearchResult {
  Guid: string;
  Title: string;
  Size: number;
  Poster?: string;
  MagnetUri?: string;
  Link?: string;
}

export interface SearchResponse {
  results: SearchResult[];
}

export interface Candidate {
  id: string;
  match: number;
  artist: string;
  album: string;
  cover: string;
  length: string;
}

export interface TorrentStatus {
  id: string;
  name: string;
  status: 'Seeding' | 'Downloading' | 'Stopped';
  percent_done: number;
  total_size: number;
  upload_ratio: number;
  eta?: number;
  added_by: string;
  hash_string: string;
  use_beets_import: boolean;
  imported: boolean;
  importError: boolean;
  candidates?: Candidate[];
}

export interface GoodreadsConfig {
  user_id: string;
  shelf: string;
  poll_interval: number;
  enabled: boolean;
  last_poll: string | null;
  last_poll_status: 'success' | 'error' | null;
  last_poll_message: string | null;
}

export interface ProcessedBook {
  book_id: string;
  title: string;
  author: string;
  status: 'downloaded' | 'no_results';
  torrent_name?: string;
}

export interface ValidationResult {
  valid: boolean;
  message: string;
  book_count?: number;
}

// API Request Types

export interface TorrentRequest {
  url: string;
}

export interface GoodreadsConfigRequest {
  user_id: string;
  shelf: string;
  poll_interval: number;
  enabled: boolean;
}

export interface GoodreadsValidateRequest {
  user_id: string;
  shelf: string;
}

// API Response Types

export interface TitleResponse {
  title: string;
}

export interface RoleResponse {
  role: string | null;
}

export interface TorrentClientTypeResponse {
  torrent_client_type: 'transmission' | 'decypharr' | 'qbittorrent';
}

export interface GoodreadsEnabledResponse {
  enabled: boolean;
}

export interface AddTorrentResponse {
  status: 'ok' | 'error';
  message: string;
}

export interface DeleteTorrentResponse {
  status: 'ok' | 'error';
  message: string;
}

export interface PollResponse {
  status?: string;
  message: string;
}

export interface SelectCandidateResponse {
  status: 'ok' | 'error';
  message: string;
}

export interface AutoimportResponse {
  status: 'ok' | 'error';
  message: string;
}

// UI State Types (matching Alpine.js app state)

export type ActiveTab = 'search' | 'status' | 'goodreads';

export interface AppState {
  // Search state
  query: string;
  results: SearchResult[];
  loadingSearch: boolean;
  searchComplete: boolean;
  searchError: string;
  currentFunnyMessage: string;
  loadingAdd: Record<string, boolean>;
  addError: Record<string, string>;

  // User/Auth state
  username: string | null;
  role: string | null;
  id: string | null;
  title: string;

  // Torrent client state
  torrentClientType: 'transmission' | 'decypharr' | 'qbittorrent' | null;

  // Torrent status state
  torrentStatus: TorrentStatus[];
  loadingTorrentStatus: boolean;
  deletingTorrent: string | null;
  deleteTorrentError: string | null;
  confirmDelete: boolean;
  torrentToDelete: string | null;

  // Candidate dialog state
  showCandidateDialog: boolean;
  selectedCandidate: Candidate | null;
  selectedTorrent: TorrentStatus | null;
  candidates: Candidate[];

  // Goodreads state
  goodreadsEnabled: boolean;
  goodreadsConfig: GoodreadsConfig;
  processedBooks: ProcessedBook[];
  loadingGoodreads: boolean;
  goodreadsError: string;
  goodreadsSuccess: string;
  validationResult: ValidationResult | null;
  pollingNow: boolean;

  // Navigation
  activeTab: ActiveTab;
}

// Funny loading messages (from Alpine.js)
export const FUNNY_MESSAGES: string[] = [
  'Searching... This better be worth it!',
  'Hold on, this takes a while...',
  'Still searching... Maybe grab a snack?',
  'Patience, young grasshopper...',
  'Wow, this is taking a minute!',
  "Don't worry, I got this!",
  'Maybe go for a walk?',
  'Still thinking... Almost there!',
  'Finding the best results for you!',
  'Hang tight! Searching magic happening!',
  'One moment... while I consult the ancients.',
  'Beep boop... processing... please wait...',
  'My hamsters are running on a wheel, almost there!',
  'Just gathering some pixie dust, be right back!',
  'Is it lunchtime yet? Oh, searching... right.',
  'Please remain calm, the search is in progress.',
  'Warning: Search may cause extreme awesomeness.',
  'Calculating the optimal route to your results...',
  'Almost there... just defragmenting my brain.',
  'Searching... because the internet is a big place!',
  'Polishing the search results for your viewing pleasure.',
  'The search is strong with this one.',
  'Please wait while I summon the search demons.',
  'Searching in hyperspace... almost there!',
  'My coffee is kicking in... search commencing!',
  'Just a few more gigabytes to process...',
  "Rome wasn't built in a day.",
  "Don't blame me, the internet is slow today.",
  'Almost there... just need to find the right key...',
];

// Constants
export const REFRESH_INTERVAL = 4000; // ms
export const FUNNY_MESSAGE_INTERVAL = 5000; // ms
