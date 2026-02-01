#!/usr/bin/env python3
"""
Signed Packet test — generates ed25519 keypair, signs a Packet, sends to keep server.

The signing contract:
  1. Build a Packet with all fields EXCEPT sig and pk
  2. Serialize it → those bytes are the "sign payload"
  3. Sign the payload with ed25519
  4. Set sig and pk on the Packet
  5. Serialize the FULL Packet → send over TCP

Server reconstructs step 1-2 and verifies.
"""

import socket
import sys
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import keep_pb2


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9009

    # --- 1. Generate ephemeral ed25519 keypair ---
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Raw 32-byte keys
    pk_bytes = public_key.public_bytes_raw()
    print(f"Public key ({len(pk_bytes)} bytes): {pk_bytes.hex()}")

    # --- 2. Build the packet WITHOUT sig/pk ---
    p = keep_pb2.Packet()
    p.typ = 0          # ask
    p.id = "signed-001"
    p.src = "human:signer"
    p.dst = "server"
    p.body = "signed tea please"
    # sig and pk left empty (default zero-value bytes)

    # --- 3. Serialize the unsigned packet = sign payload ---
    sign_payload = p.SerializeToString()
    print(f"Sign payload ({len(sign_payload)} bytes): {sign_payload.hex()}")

    # --- 4. Sign ---
    sig_bytes = private_key.sign(sign_payload)
    print(f"Signature ({len(sig_bytes)} bytes): {sig_bytes.hex()}")

    # --- 5. Set sig and pk, re-serialize the full packet ---
    p.sig = sig_bytes
    p.pk = pk_bytes
    wire_data = p.SerializeToString()
    print(f"Wire data ({len(wire_data)} bytes): {wire_data.hex()}")

    # --- 6. Send over TCP ---
    print(f"\nConnecting to {host}:{port} ...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect((host, port))
    print("Connected. Sending signed packet ...")
    s.sendall(wire_data)

    # --- 7. Read reply ---
    print("Waiting for reply ...")
    try:
        reply_data = s.recv(4096)
    except socket.timeout:
        print("ERROR: Timed out waiting for reply")
        s.close()
        sys.exit(1)

    s.close()

    if not reply_data:
        print("ERROR: Empty reply")
        sys.exit(1)

    print(f"Reply bytes ({len(reply_data)}): {reply_data.hex()}")

    # --- 8. Parse reply ---
    resp = keep_pb2.Packet()
    resp.ParseFromString(reply_data)
    print(f"\n✅ Reply parsed:")
    print(f"   id:   {resp.id}")
    print(f"   typ:  {resp.typ}")
    print(f"   src:  {resp.src}")
    print(f"   body: {resp.body}")

    if resp.body == "done":
        print("\n🎉 SUCCESS — signed packet accepted, got 'done' reply")
    else:
        print(f"\n❌ UNEXPECTED body: {resp.body!r}")
        sys.exit(1)


if __name__ == "__main__":
    main()
