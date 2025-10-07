# Audiobookbay Downloader

A modern web application for searching and downloading audiobooks from AudiobookBay. Features a clean web UI and REST API for automated audiobook management with support for multiple torrent clients and authentication systems.

## Features

- 🎧 **Audiobook Search**: Search AudiobookBay via Jackett integration
- 📥 **Multi-Client Downloads**: Support for Transmission and Decypharr torrent clients
- 🔐 **Flexible Authentication**: Support for Authentik SSO and no-auth modes
- 📚 **Beets Integration**: Optional music library management integration
- 🌐 **Web UI**: Clean, responsive interface for browsing and managing downloads
- 🔄 **Auto-Import**: Automated processing and cleanup of completed downloads
- 🏷️ **Label Management**: Organize torrents with custom labels

## Screenshots

![Search Interface](https://i.imgur.com/mwuvB5z.png)

![Download Management](https://i.imgur.com/ccUBle0.png)

## Environment Variables

### Required Configuration

#### Jackett Configuration (Required)
- Multiple URLs are supported when prefixed JACKETT_API_URL
```env
JACKETT_API_URL=https://jackett.example.com/api/v2.0/indexers/audiobookbay/results
JACKETT_API_URL1=https://jackett.example.com/api/v2.0/indexers/myanonamouse/results
JACKETT_API_KEY=your_jackett_api_key
```

#### Torrent Client Configuration (Choose One)

**Option 1: Transmission**
```env
TORRENT_CLIENT_TYPE=transmission
TRANSMISSION_URL=https://transmission.example.com/transmission/rpc
TRANSMISSION_USER=your_transmission_user
TRANSMISSION_PASS=your_transmission_password
```

**Option 2: Decypharr**
```env
TORRENT_CLIENT_TYPE=decypharr
DECYPHARR_URL=https://decypharr.example.com
DECYPHARR_API_KEY=your_decypharr_api_key
```

### Optional Configuration

#### Application Settings
```env
# App Configuration
TITLE="Audiobook Search"                    # Application title
SESSION_KEY="your_random_session_key"       # Session encryption key
AUTH_MODE=none                              # Authentication mode: authentik, none
LABEL=audiobook                             # Default torrent label

# Admin User (Legacy - only used in authentik mode)
ADMIN_USER=admin
ADMIN_PASS=YWRtaW4=                         # Base64 encoded password
ADMIN_ID=e0617896-4560-193c-cc34-653683f99c35
DB_PATH=/tmp                                # Path for user database
```

#### Cleanup Configuration
```env
DELETE_AFTER_DAYS=14                        # Days before marking torrents for deletion
STRICTLY_DELETE_AFTER_DAYS=30               # Days before force deletion
```

#### Beets Integration (Optional)
```env
USE_BEETS_IMPORT=false                      # Enable beets music library integration
BEETSDIR=/config                            # Beets configuration directory
BEETS_INPUT_PATH=/beetsinput                # Input path for beets processing
BEETS_COMPLETE_LABEL=beets                  # Label for beets-processed torrents
BEETS_ERROR_LABEL=beetserror                # Label for beets processing errors
```

## Authentication Modes

### None Mode (Default)
- **Description**: No authentication required
- **Use Case**: Private networks, development environments
- **Configuration**: `AUTH_MODE=none`
- **Access**: All users have admin privileges automatically

### Authentik Mode
- **Description**: Integration with Authentik SSO
- **Use Case**: Production environments with existing Authentik setup
- **Configuration**: `AUTH_MODE=authentik`
- **Headers Required**:
  - `X-authentik-username`: Username from Authentik
  - `X-authentik-uid`: User ID from Authentik  
  - `X-authentik-role`: User role (admin/user)

## Docker Compose Deployments

### Option 1: External Services (Recommended for existing setups)

Use this when you already have Jackett and Transmission/Decypharr running.

**📁 File:** [`docker-compose.external.yml`](./docker-compose.external.yml)

```bash
# Download and use the external services compose file
curl -O https://raw.githubusercontent.com/moonblade/audiobookbay-downloader/main/docker-compose.external.yml
docker-compose -f docker-compose.external.yml up -d
```

<details>
<summary>View docker-compose.external.yml content</summary>

```yaml
# See the complete file: docker-compose.external.yml
# This compose file includes:
# - Audiobookbay downloader service
# - Configuration for external Jackett and Transmission/Decypharr
# - Environment variables for connecting to existing services
# - Volume mapping for data persistence
```

</details>

### Option 2: Full Stack (Complete setup with all services)

Use this for a complete setup including Jackett and Transmission services.

**📁 File:** [`docker-compose.full.yml`](./docker-compose.full.yml)

```bash
# Download and use the full stack compose file
curl -O https://raw.githubusercontent.com/moonblade/audiobookbay-downloader/main/docker-compose.full.yml
docker-compose -f docker-compose.full.yml up -d
```

<details>
<summary>View docker-compose.full.yml content</summary>

```yaml
# See the complete file: docker-compose.full.yml  
# This compose file includes:
# - Audiobookbay downloader service
# - Jackett service with LinuxServer.io image
# - Transmission service with Flood UI
# - Shared volumes for downloads and configuration
# - Internal networking between services
```

</details>

## Initial Setup

### 1. Configure Jackett

1. Access Jackett at `http://localhost:9117`
2. Add the AudiobookBay indexer
3. Copy the API key from Jackett dashboard
4. Update your environment variables with the Jackett URL and API key

### 2. Configure Torrent Client

**For Transmission:**
1. Access Transmission at `http://localhost:9091`
2. Set up authentication if required
3. Update environment variables with credentials

**For Decypharr:**
1. Access Decypharr web interface
2. Generate an API key
3. Update environment variables

### 3. Start the Application

```bash
# Using Docker Compose
docker-compose up -d

# Or using Python directly
pip install -r requirements.txt
python main.py
```

### 4. Access the Application

- Web UI: `http://localhost:9000`
- API Documentation: `http://localhost:9000/docs`

## API Endpoints

- `GET /search?query=bookname` - Search for audiobooks
- `POST /add` - Add torrent to download queue
- `GET /list` - List all torrents
- `DELETE /torrent/{id}` - Delete torrent
- `POST /torrent/{id}/pause` - Pause torrent
- `POST /torrent/{id}/play` - Resume torrent
- `POST /autoimport` - Trigger auto-import process

## Development

```bash
# Clone the repository
git clone <repository-url>
cd audiobookbay-downloader

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AUTH_MODE=none
export JACKETT_API_URL=...
export JACKETT_API_URL2=...
export JACKETT_API_KEY=...
# ... other variables

# Run the application
python main.py
```

## Troubleshooting

### Common Issues

1. **Jackett Connection Failed**
   - Verify JACKETT_API_URL and JACKETT_API_KEY
   - Ensure AudiobookBay indexer is configured in Jackett
   - Check network connectivity between services

2. **Torrent Client Connection Failed**
   - Verify torrent client URL and credentials
   - Check if the torrent client is accessible
   - Ensure correct TORRENT_CLIENT_TYPE is set

3. **Authentication Issues**
   - Verify AUTH_MODE setting
   - For Authentik mode, check header configuration
   - For none mode, no additional setup required

### Logs

Check application logs for detailed error information:

```bash
docker-compose logs audiobookbay-downloader
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
