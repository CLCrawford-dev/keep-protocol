# keep-protocol

Lightweight TCP + Protobuf intent protocol for agent coordination.

Designed as simple plumbing so Moltbots / OpenClaw agents can send structured intents.

## Run with Docker

### Build from source
```bash
# Clone the repo
git clone git@github.com:nTEG-dev/keep-protocol.git
cd keep-protocol

# Build
docker build -t keep-protocol .

# Run
docker run -d -p 9009:9009 --name keep-server keep-protocol

Or pull pre-built (when published)

docker pull ghcr.io/nteg-dev/keep-protocol:latest
docker run -d -p 9009:9009 --name keep-server ghcr.io/nteg-dev/keep-protocol:latest

Agents connect to localhost:9009 (or host IP:9009) and send serialized Packet messages.

