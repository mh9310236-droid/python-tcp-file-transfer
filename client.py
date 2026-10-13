
import json
import socket
from pathlib import Path

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000
BUFFER_SIZE = 64 * 1024
MAX_FILE_SIZE = 100 * 1024 * 1024
DOWNLOADS = Path(__file__).parent / "downloads"


def send_json(sock, data):
    sock.sendall(json.dumps(data).encode("utf-8") + b"\n")


def recv_line(sock):
    data = bytearray()

    while True:
        char = sock.recv(1)

        if not char:
            raise ConnectionError("Server disconnected.")

        if char == b"\n":
            break

        data.extend(char)

        if len(data) > 65536:
            raise ValueError("Response header too large.")

    return json.loads(data.decode("utf-8"))


def receive_file(sock, path, size):
    remaining = size

    with path.open("wb") as file:
        while remaining:
            chunk = sock.recv(min(BUFFER_SIZE, remaining))

            if not chunk:
                raise ConnectionError("Transfer interrupted.")

            file.write(chunk)
            remaining -= len(chunk)


def upload(sock):
    path_text = input("Enter the full path of the file to upload: ").strip()
    path = Path(path_text.strip('"')).expanduser()

    if not path.is_file():
        print("Error: file not found.")
        return

    size = path.stat().st_size

    if size > MAX_FILE_SIZE:
        print("Error: maximum upload size is 100 MB.")
        return

    send_json(sock, {
        "cmd": "UPLOAD",
        "name": path.name,
        "size": size
    })

    with path.open("rb") as file:
        while True:
            chunk = file.read(BUFFER_SIZE)

            if not chunk:
                break

            sock.sendall(chunk)

    response = recv_line(sock)
    print(response.get("message", response))


def list_files(sock):
    send_json(sock, {"cmd": "LIST"})
    response = recv_line(sock)

    if response.get("status") == "OK":
        files = response.get("files", [])

        print("\nFiles available on server:")
        if files:
            for name in files:
                print(" -", name)
        else:
            print("No files uploaded yet.")
    else:
        print(response.get("message", "Request failed."))


def download(sock):
    name = input("Enter the server filename to download: ").strip()

    if not name or name in (".", "..") or "/" in name or "\\" in name:
        print("Error: enter a valid filename only.")
        return

    send_json(sock, {"cmd": "DOWNLOAD", "name": name})
    response = recv_line(sock)

    if response.get("status") != "OK":
        print(response.get("message", "Download failed."))
        return

    size = response.get("size")

    if type(size) is not int or size < 0:
        raise ValueError("Invalid file size from server.")

    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    destination = DOWNLOADS / name

    receive_file(sock, destination, size)
    print(f"Downloaded successfully: {destination} ({size} bytes)")


def main():
    print("=== TCP File Transfer Client ===")
    print(f"Connecting to {SERVER_HOST}:{SERVER_PORT} ...")

    try:
        with socket.create_connection(
            (SERVER_HOST, SERVER_PORT), timeout=10
        ) as sock:
            sock.settimeout(None)
            print("Connected successfully!")

            while True:
                print("\n1. List files")
                print("2. Upload file")
                print("3. Download file")
                print("4. Exit")

                choice = input("Choose an option (1-4): ").strip()

                try:
                    if choice == "1":
                        list_files(sock)
                    elif choice == "2":
                        upload(sock)
                    elif choice == "3":
                        download(sock)
                    elif choice == "4":
                        send_json(sock, {"cmd": "QUIT"})
                        recv_line(sock)
                        print("Disconnected.")
                        break
                    else:
                        print("Invalid choice. Select 1, 2, 3, or 4.")

                except (OSError, ConnectionError, ValueError, json.JSONDecodeError) as exc:
                    print(f"Operation failed: {exc}")
                    break

    except (OSError, ConnectionError) as exc:
        print(f"Could not connect to server: {exc}")
        print("Check that server.py is running on port 5000.")


if __name__ == "__main__":
    main()
