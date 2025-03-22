mkdir -p jackett/Jackett/Indexers || true
mkdir -p transmission/config || true
mkdir -p transmission/complete || true
mkdir -p transmission/incomplete || true

# sudo chown -R 1000:1000 jackett
sudo chmod -R 777 jackett

# sudo chown -R 1000:1000 transmission
sudo chmod -R 777 transmission

docker compose up
