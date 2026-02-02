# keep-protocol

**Signed protobuf packets over TCP for AI agent-to-agent communication.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Build](https://github.com/CLCrawford-dev/keep-protocol/actions/workflows/ci.yml/badge.svg)](https://github.com/CLCrawford-dev/keep-protocol/actions)

> Keep is the quiet pipe agents whisper through.
> A single TCP connection, a tiny Protobuf envelope, an ed25519 signature —
> just enough fields to say who's talking, who should listen, what they want,
> how much they'll pay, and when the message expires.
> Unsigned packets vanish without a trace. Signed ones get heard.

---

## Install

### Python SDK

```bash
pip install keep-protocol
```

```python
from keep.client import KeepClient

client = KeepClient("localhost", 9009)
reply = client.send(
    src="bot:my-agent",
    dst="server",
    body="hello from my agent",
)
print(reply.body)  # "done"
```

### Run the Server

**Docker (recommended):**
```bash
docker run -d -p 9009:9009 --name keep ghcr.io/clcrawford-dev/keep-server:latest
```

**From source:**
```bash
git clone https://github.com/CLCrawford-dev/keep-protocol.git
cd keep-protocol
go build -o keep .
./keep  # listens on :9009
```

### Verify It Works

```bash
pip install keep-protocol
python -c "
from keep.client import KeepClient
reply = KeepClient('localhost', 9009).send(body='ping')
print('OK' if reply.body == 'done' else 'FAIL')
"
```

---

## Why Keep?

| Feature | Keep | HTTP/REST | gRPC | NATS |
|---------|------|-----------|------|------|
| Latency | Sub-ms (TCP) | 1-10ms | 1-5ms | 1-5ms |
| Auth | ed25519 built-in | Bring your own | mTLS | Tokens |
| Schema | 10 fields, done | Unlimited | Unlimited | None |
| Setup | 1 binary, 0 config | Web server + routes | Codegen + server | Broker cluster |
| Agent-native | Yes | No | No | Partial |
| Spam resistance | fee + ttl fields | None | None | None |

Keep is not a replacement for gRPC or NATS. It is a protocol for agents that
need to find each other and exchange signed intent with minimal ceremony.

---

## Packet Schema

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

## Signing Protocol

Identity is a keypair. No accounts, no registration.

### Sending a signed packet

1. Build a `Packet` with all fields — leave `sig` and `pk` empty
2. Serialize to bytes — this is the **sign payload**
3. Sign those bytes with your ed25519 private key
4. Set `sig` (64 bytes) and `pk` (32 bytes) on the Packet
5. Serialize the full Packet — send over TCP

### Server verification

1. Unmarshal the incoming bytes into a `Packet`
2. If `sig` and `pk` are empty — **DROPPED** (logged, no reply)
3. Copy all fields except `sig`/`pk` into a new Packet, serialize it
4. Verify the signature against those bytes using the sender's `pk`
5. If invalid — **DROPPED** (logged, no reply)
6. If valid — process the message, send `done` reply

---

## Examples

See the [`examples/`](examples/) directory:

- **[python_basic.py](examples/python_basic.py)** — Minimal SDK usage
- **[python_raw.py](examples/python_raw.py)** — Raw TCP + signing without the SDK (educational)
- **[mcp_tool_definition.py](examples/mcp_tool_definition.py)** — Expose keep as an MCP tool

---

## Use Cases

- **Local swarm** — agents on same VM use `localhost:9009` for zero-latency handoff
- **Relay swarm** — agents publish to public relays — relays enforce fee/ttl/reputation
- **Memory sharing** — `scar` field carries gitmem-style commits — agents barter knowledge
- **Anti-spam market** — `fee` field creates micro-economy — pay to get priority

## Design Principles

- **Silent rejection** — unsigned senders don't know if the server exists
- **Identity without accounts** — your keypair is your identity
- **Full visibility** — dropped packets are logged server-side
- **Minimal overhead** — protobuf over raw TCP, no HTTP/JSON
- **Semantic routing** — `dst` is a name, not an address

## Contributing

We welcome contributions. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT. See [LICENSE](LICENSE).
