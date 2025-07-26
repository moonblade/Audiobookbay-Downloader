# Audiobookbay downloader

Download audiobooks from audiobookbay with wrapper ui and api. Deployed on a cluster and downloads on transmission deployed on same cluster.

Requires jackett with audiobookbay indexer in it. It uses jackett to search and transmission to download.

Added in homelab k8s

#### Environment Variables
The app uses environment variables to configure its behavior. Below are the required variables:

```env
JACKETT_API_URL=https://myjackett.myendpoint.com/api/v2.0/indexers/audiobookbay/results         # Jackett api url
JACKETT_API_KEY=xxx                                                                             # Key to interact with jackett
TRANSMISSION_URL=https://transmission.myendpoint.com/transmission/rpc                           # torrent endpoint
TRANSMISSION_USER=user                                                                          # torrent user
TRANSMISSION_PASS=pass                                                                          # torrent pass
```

---

![](https://i.imgur.com/mwuvB5z.png)

---

![](https://i.imgur.com/ccUBle0.png)


### Docker compose deployment

```yaml
version: '3.8'

services:
  jackett:
    image: lscr.io/linuxserver/jackett:latest
    container_name: jackett
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Etc/UTC
      - AUTO_UPDATE=true
      - RUN_OPTS= --ApiKey=asdf
    volumes:
      - /tmp/config:/config
      - /tmp:/downloads
    ports:
      - 9117:9117
    restart: unless-stopped
```

## Authentik

I ended up adding authentik on the k8s cluster to handle auth for everything, that makes local development a bitch. So right now its setup in proxy mode and then the headers are passed to this app as username.
`X-authentik-username`. Unfortunately, this means local dev is crap now. Need to find something else I can do for this, but thats a problem for tomorrow me.

Fixed issue with authentik, now it only comes up if AUTH_MODE variable is authentik, by default its local and will follow old behaviour
