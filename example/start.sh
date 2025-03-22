mkdir -p jackett || true
mkdir -p transmission/config || true
mkdir -p transmission/complete || true
mkdir -p transmission/incomplete || true

sudo chown -R 1000:1000 jackett

docker compose up
