import socket

HOST = '192.168.29.85'  # Replace with server IP
PORT = 5050

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
print(f"Connected to server at {HOST}:{PORT}")

client_id = input("Enter your client ID: ")
s.send(client_id.encode())

# Receive welcome / access status
msg = s.recv(1024).decode()
print("Server:", msg)
if "Access denied" in msg:
    s.close()
    exit()

while True:
    query = input("Enter SQL query: ")
    if query.lower() == "exit":
        break
    s.send(query.encode())

    response = s.recv(4096).decode()
    print("Response:", response)

s.close()
