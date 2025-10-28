# PeerServer.py
import socket
import os

def start_peer_server(host='0.0.0.0', port=8888, save_folder='received_files'):
    """Peer-to-peer server: receive file from another peer"""
    os.makedirs(save_folder, exist_ok=True)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"[P2P Server] Listening on {host}:{port}")

    while True:
        conn, addr = server_socket.accept()
        print(f"[P2P Server] Connected by {addr}")
        filename = conn.recv(1024).decode()
        if not filename:
            conn.close()
            continue
        filepath = os.path.join(save_folder, filename)
        with open(filepath, "wb") as f:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                f.write(data)
        conn.close()
        print(f"[P2P Server] Received file: {filepath}\n")

if __name__ == "__main__":
    start_peer_server()
