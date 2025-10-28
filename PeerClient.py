# PeerClient.py
import socket
import os

def send_file_to_peer(peer_ip, peer_port, file_path):
    """Send file directly to another peer via TCP"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    filename = os.path.basename(file_path)
    print(f"[P2P Client] Connecting to {peer_ip}:{peer_port} ...")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((peer_ip, peer_port))

    # Gửi tên file trước
    client_socket.send(filename.encode())
    with open(file_path, "rb") as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            client_socket.sendall(data)
    client_socket.close()
    print(f"[P2P Client] File sent successfully: {filename}")

if __name__ == "__main__":
    peer_ip = input("Enter peer IP (e.g., 127.0.0.1): ")
    file_path = input("Enter file to send (e.g., movie.Mjpeg): ")
    send_file_to_peer(peer_ip, 8888, file_path)
