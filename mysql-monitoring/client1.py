import socket

HOST = '10.208.18.195'  # replace with your server IP
PORT = 5050

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
print(f"Connected to server at {HOST}:{PORT}")

client_id = input("Enter your client ID: ")
sock.send(client_id.encode())

msg = sock.recv(1024).decode()
print("Server:", msg)
if "Access denied" in msg:
    sock.close()
    exit()

while True:
    query = input("Enter SQL query: ")
    if query.lower() == "exit":
        break
    sock.send(query.encode())
    response = sock.recv(4096).decode()
    print("Response:", response)

sock.close()