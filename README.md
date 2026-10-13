
# Python TCP File Transfer System

A client-server file transfer application built using Python TCP sockets.

## Features

- TCP communication on port 5000
- List files stored on the server
- Upload files from client to server
- Download files from server to client
- Supports binary files such as PDF, PPTX, PNG, ZIP, and CSV
- Uses message headers and file sizes to frame transfers

## Requirements

- Python 3
- No external Python packages required

## How to Run

### 1. Start the server

Open a terminal in the project directory:

```bash
python server.py
```

### 2. Start the client

Open a second terminal in the same directory:

```bash
python client.py
```

### 3. Use the menu

Choose one of these options:

1. List files
2. Upload file
3. Download file
4. Exit

## Storage

- Uploaded files are saved in `server_files/`.
- Downloaded files are saved in `downloads/`.

Both folders are created automatically when needed.

## Default Connection

- Protocol: TCP
- Host: 127.0.0.1
- Port: 5000
- Maximum upload size: 100 MB

## Limitations

This is an educational project. It is designed for trusted local testing and does not implement user authentication, encryption, or access control. Do not expose it directly to the public internet.

## Author

mh9310236-droid
