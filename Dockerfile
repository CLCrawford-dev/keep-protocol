FROM golang:1.23-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY keep.proto keep.go keep.pb.go ./

RUN go build -o keep .

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/keep .
EXPOSE 9009
CMD ["./keep"]
