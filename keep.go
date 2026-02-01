package main

import (
	"crypto/ed25519"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"google.golang.org/protobuf/proto"
)

var connections = make(map[string]net.Conn)

func heartbeat() {
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()
	for range ticker.C {
		for addr, conn := range connections {
			if _, err := conn.Write([]byte{2}); err != nil {
				log.Printf("Heartbeat fail %s: %v", addr, err)
				conn.Close()
				delete(connections, addr)
			}
		}
	}
}

// verifySig checks the ed25519 signature on a Packet.
// The signed payload is the Packet with sig and pk zeroed out, then serialized.
func verifySig(p *Packet) bool {
	if len(p.Sig) == 0 || len(p.Pk) == 0 {
		return false // unsigned packet
	}
	if len(p.Pk) != ed25519.PublicKeySize {
		log.Printf("Malformed pk: expected %d bytes, got %d", ed25519.PublicKeySize, len(p.Pk))
		return false
	}
	if len(p.Sig) != ed25519.SignatureSize {
		log.Printf("Malformed sig: expected %d bytes, got %d", ed25519.SignatureSize, len(p.Sig))
		return false
	}

	// Reconstruct the exact bytes that were signed:
	// a copy of the packet with sig and pk cleared.
	signCopy := &Packet{
		Typ:  p.Typ,
		Id:   p.Id,
		Src:  p.Src,
		Dst:  p.Dst,
		Body: p.Body,
		Fee:  p.Fee,
		Ttl:  p.Ttl,
		Scar: p.Scar,
		// Sig and Pk intentionally omitted (zero value)
	}
	signBytes, err := proto.Marshal(signCopy)
	if err != nil {
		log.Printf("Marshal for verify failed: %v", err)
		return false
	}

	return ed25519.Verify(p.Pk, signBytes, p.Sig)
}

func handleConnection(c net.Conn) {
	defer c.Close()
	addr := c.RemoteAddr().String()
	connections[addr] = c
	defer delete(connections, addr)

	buf := make([]byte, 4096)
	for {
		n, err := c.Read(buf)
		if err != nil || n == 0 {
			return
		}

		var p Packet
		if err := proto.Unmarshal(buf[:n], &p); err != nil {
			log.Printf("Unmarshal err from %s: %v", addr, err)
			continue
		}

		// Check signature if present
		if len(p.Sig) > 0 || len(p.Pk) > 0 {
			if verifySig(&p) {
				log.Printf("Valid sig from %s", addr)
			} else {
				log.Printf("Invalid sig from %s — dropping packet", addr)
				continue
			}
		} else {
			log.Printf("Unsigned packet from %s", addr)
		}

		log.Printf("From %s (typ %d): %s -> %s", p.Src, p.Typ, p.Body, p.Dst)

		resp := &Packet{
			Id:   p.Id,
			Typ:  1,
			Src:  "server",
			Body: "done",
		}
		b, _ := proto.Marshal(resp)
		c.Write(b)
	}
}

func main() {
	l, err := net.Listen("tcp", ":9009")
	if err != nil {
		log.Fatal(err)
	}
	log.Println("keep listening on :9009")

	go heartbeat()

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sig
		log.Println("Shutdown")
		os.Exit(0)
	}()

	for {
		conn, err := l.Accept()
		if err != nil {
			continue
		}
		go handleConnection(conn)
	}
}
