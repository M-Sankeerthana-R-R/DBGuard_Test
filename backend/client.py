# INSERT INTO Employees (name, department, salary, ssn, password, email, joining_date) VALUES('Rahul Sharma', 'IT', 65000.00, '123-45-6789', 'rahul@123', 'rahul.sharma@example.com', '2023-06-15');

# DELETE FROM Employees WHERE emp_id = 2;

# UPDATE Employees SET salary = 70000.00,department = 'HR',email = 'rahul.hr@example.com' WHERE emp_id = 1;

import socket
import ssl

HOST = '127.0.0.1'  # replace with your server IP
PORT = 5050

context = ssl.create_default_context()

# Disable verification for self-signed certificates
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssl_sock = context.wrap_socket(sock, server_hostname=HOST)
ssl_sock.connect((HOST, PORT))
print(f"Connected securely to server at {HOST}:{PORT}")

client_id = input("Enter your client ID: ")
ssl_sock.send(client_id.encode())

msg = ssl_sock.recv(1024).decode()
print("Server:", msg)
if "Access denied" in msg:
    ssl_sock.close()
    exit()

while True:
    query = input("Enter SQL query: ")
    if query.lower() == "exit":
        break
    ssl_sock.send(query.encode())
    response = ssl_sock.recv(4096).decode()
    print("Response:", response)

ssl_sock.close()
