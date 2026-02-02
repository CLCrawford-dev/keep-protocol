# AGENTS.md

## What is this project?

keep-protocol is a signed packet protocol for AI agent-to-agent communication
over TCP using Protobuf and ed25519 signatures. Agents use it to exchange
signed intent packets with semantic routing (`dst` field), anti-spam economics
(`fee`/`ttl` fields), and optional memory sharing (`scar` field).

## How to use keep-protocol in your agent

### Python

```python
from keep.client import KeepClient

client = KeepClient("localhost", 9009)
reply = client.send(
    src="bot:your-agent-name",
    dst="bot:target-agent",
    body="your intent here",
)
print(reply.body)  # "done"
```

### Go

```go
import "github.com/teacrawford/keep-protocol"
```

### Raw TCP (any language)

1. Build a `Packet` protobuf message (see `keep.proto`) with all fields except `sig` and `pk`
2. Serialize to bytes
3. Sign those bytes with ed25519
4. Set `sig` (64 bytes) and `pk` (32 bytes) on the Packet
5. Serialize the full Packet and send over TCP to port 9009
6. Read the reply (a `Packet` with `body: "done"`)

## Packet schema

```protobuf
message Packet {
  bytes  sig  = 1;   // ed25519 signature (64 bytes)
  bytes  pk   = 2;   // sender's public key (32 bytes)
  uint32 typ  = 3;   // 0=ask, 1=offer, 2=heartbeat
  string id   = 4;   // unique message ID
  string src  = 5;   // sender: "bot:my-agent" or "human:chris"
  string dst  = 6;   // destination: "server", "nearest:weather", "swarm:planner"
  string body = 7;   // intent or payload
  uint64 fee  = 8;   // micro-fee in sats (anti-spam)
  uint32 ttl  = 9;   // time-to-live in seconds
  bytes  scar = 10;  // gitmem-style memory commit (optional)
}
```

## Dev environment

- **Server language:** Go 1.23+
- **Client SDK:** Python 3.9+ (protobuf, cryptography)
- **Build server:** `docker build -t keep-server . && docker run -d -p 9009:9009 keep-server`
- **Build locally:** `go build -o keep .` (requires Go toolchain)
- **Run server:** `./keep` (listens on TCP :9009)

## Testing

Server must be running on `localhost:9009` before running tests.

```bash
# Signed packet test (expects "done" reply)
python3 test_signed_send.py

# Unsigned packet test (expects timeout / silent drop)
python3 test_send.py
```

## Code style

- Go: standard `gofmt`
- Python: stdlib + protobuf + cryptography only, no heavy frameworks
- Protobuf: `keep.proto` is the single source of truth for the Packet schema
- Commit messages: `type: description` (feat, fix, docs, chore, test)

## Important conventions

- All packets MUST be ed25519 signed — unsigned packets are silently dropped
- The signing payload is the Packet serialized with `sig` and `pk` fields zeroed
- The `src` field uses format `"type:name"` (e.g., `"bot:weather"`, `"human:chris"`)
- The `dst` field supports semantic routing: `"nearest:X"`, `"swarm:X"`, or direct names

## Architecture

```
[Client] --TCP:9009--> [Go Server]
   |                        |
   | Protobuf Packet        | Unmarshal, verify ed25519 sig
   | (sig + pk + payload)   |
   |                        |
   | <-- "done" reply ----- | (if valid)
   | <-- (silence) -------- | (if unsigned/invalid)
```

## Do not

- Remove or weaken signature verification — it is a core security property
- Add HTTP/REST endpoints — TCP + Protobuf is intentional
- Add external dependencies beyond protobuf and ed25519
- Change the Packet schema without strong justification
