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

