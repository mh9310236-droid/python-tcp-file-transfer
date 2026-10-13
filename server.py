
import json
import socket
from pathlib import Path

HOST = "0.0.0.0"
PORT = 5000
BUFFER_SIZE = 64 * 1024
STORAGE = Path(__file__).parent / "server_files"


def send_json(conn, data):
    message = json.dumps(data).encode("utf-8") + b"\n"
    conn.sendall(message)


def recv_line(conn):
    data = bytearray()

    while True:
        char = conn.recv(1)

        if not char:
            raise ConnectionError("Client disconnected.")

        if char == b"\n":
            break

        data.extend(char)

        if len(data) > 65536:
            raise ValueError("Request header too large.")

    return json.loads(data.decode("utf-8"))


def recv_exact(conn, size):
    data = bytearray()

    while len(data) < size:
        chunk = conn.recv(min(BUFFER_SIZE, size - len(data)))

        if not chunk:
            raise ConnectionError("Connection lost during transfer.")

        data.extend(chunk)

    return data


def safe_name(name):
    if not isinstance(name, str) or not name:
        raise ValueError("A filename is required.")

    if name in (".", "..") or Path(name).name != name:
        raise ValueError("Invalid filename.")

    if "/" in name or "\\" in name:
        raise ValueError("Invalid filename.")

    return name


def handle_client(conn, address):
    print(f"[CONNECTED] {address}")

    with conn:
        while True:
            try:
                request = recv_line(conn)
                command = request.get("cmd")

                if command == "LIST":
                    files = sorted(
                        item.name
                        for item in STORAGE.iterdir()
                        if item.is_file()
                    )
                    send_json(conn, {"status": "OK", "files": files})

                elif command == "UPLOAD":
                    name = safe_name(request.get("name"))
                    size = request.get("size")

                    if type(size) is not int or not 0 <= size <= 100 * 1024 * 1024:
                        send_json(conn, {
                            "status": "ERROR",
                            "message": "File size must be between 0 and 100 MB."
                        })
                        continue

                    target = STORAGE / name
                    remaining = size

                    with target.open("wb") as file:
                        while remaining:
                            chunk = conn.recv(min(BUFFER_SIZE, remaining))

                            if not chunk:
                                raise ConnectionError(
                                    "Connection lost during upload."
                                )

                            file.write(chunk)
                            remaining -= len(chunk)

                    send_json(conn, {
                        "status": "OK",
                        "message": f"Uploaded {name} ({size} bytes)."
                    })

                elif command == "DOWNLOAD":
                    name = safe_name(request.get("name"))
                    target = STORAGE / name

                    if not target.is_file():
                        send_json(conn, {
                            "status": "ERROR",
                            "message": "File not found."
                        })
                        continue

                    size = target.stat().st_size
                    send_json(conn, {
                        "status": "OK",
                        "name": name,
                        "size": size
                    })

                    with target.open("rb") as file:
                        while True:
                            chunk = file.read(BUFFER_SIZE)

                            if not chunk:
                                break

                            conn.sendall(chunk)

                elif command == "QUIT":
                    send_json(conn, {"status": "OK", "message": "Goodbye."})
                    break

                else:
                    send_json(conn, {
                        "status": "ERROR",
                        "message": "Unknown command."
                    })

            except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                send_json(conn, {"status": "ERROR", "message": str(exc)})

            except (ConnectionError, OSError) as exc:
                print(f"[DISCONNECTED] {address}: {exc}")
                break

    print(f"[CLOSED] {address}")


def main():
    STORAGE.mkdir(parents=True, exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()

        print(f"TCP File Transfer Server running on port {PORT}")
        print(f"Shared folder: {STORAGE}")
        print("Press Ctrl+C to stop.")

        try:
            while True:
                conn, address = server.accept()
                handle_client(conn, address)
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
