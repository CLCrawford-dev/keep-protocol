# keep-protocol

Keep is the quiet pipe agents whisper through.
A single TCP connection, a tiny Protobuf envelope, an ed25519 signature, and just enough fields to say who's talking, who should listen, what they want, how much they'll pay, and when the message expires.
No central authority, no ceremony, no noise — just clean intent moving from claw to claw.
Unsigned packets vanish without a trace.
Signed ones get heard, parsed, and answered with a single word: *done*.

## Signing Protocol

Identity is a keypair. No accounts, no registration.

### How to send a signed packet

1. Build a `Packet` with all fields — leave `sig` and `pk` empty
2. Serialize to bytes — this is the **sign payload**
3. Sign those bytes with your ed25519 private key
4. Set `sig` (64 bytes) and `pk` (32 bytes) on the Packet
5. Serialize the full Packet — send over TCP

### Server verification

1. Unmarshal the incoming bytes into a `Packet`
2. If `sig` and `pk` are empty → **DROPPED** (logged, no reply)
3. Copy all fields except `sig`/`pk` into a new Packet, serialize it
4. Verify the signature against those bytes using the sender's `pk`
5. If invalid → **DROPPED** (logged, no reply)
6. If valid → process the message, send `done` reply

## Packet Schema

```protobuf
message Packet {
  bytes  sig  = 1;   // ed25519 signature (64 bytes)
  bytes  pk   = 2;   // sender's public key (32 bytes)
  uint32 typ  = 3;   // message type (0=ask, 1=response)
  string id   = 4;   // request/reply matching ID
  string src  = 5;   // sender identity ("human:chris")
  string dst  = 6;   // destination ("server")
  string body = 7;   // message content
  uint64 fee  = 8;   // reserved: pay-to-relay
  uint32 ttl  = 9;   // reserved: message expiry
  bytes  scar = 10;  // reserved: metadata/provenance
}
```

## Run with Docker

```bash
git clone git@github.com:teacrawford/keep-protocol.git
cd keep-protocol

docker build -t keep-server .
docker run -d -p 9009:9009 --name keep-server keep-server
```

## Test

### Prerequisites

```bash
pip install protobuf cryptography
```

### Unsigned (should get no reply)

```bash
python3 test_send.py
# Timeout — server drops unsigned packets silently
```

### Signed (should get "done" reply)

```bash
python3 test_signed_send.py
# ✅ Reply: id=signed-001 body=done
```

### Server logs

```bash
docker logs keep-server --tail 10
```

Expected output:
```
DROPPED unsigned packet from 172.17.0.1:xxxxx (src=human:tester body="make tea please")
Valid sig from 172.17.0.1:yyyyy
From human:signer (typ 0): signed tea please -> server
Reply to 172.17.0.1:yyyyy: id=signed-001 body=done
```

## Design Principles

- **Silent rejection** — unsigned senders don't know if the server exists
- **Identity without accounts** — your keypair is your identity
- **Full visibility** — dropped packets are logged server-side
- **Minimal overhead** — protobuf over raw TCP, no HTTP/JSON
