from flask import Blueprint, request, jsonify
import socket
import ssl
import time

client_bp = Blueprint("client_bp", __name__)

# Store active client connections
active_clients = {}

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5050
SENSITIVE_COLUMNS = ["salary", "ssn", "password"]

@client_bp.route("/connect", methods=["POST"])
def connect():
    data = request.get_json()
    client_id = data.get("clientId")
    if not client_id:
        return jsonify({"status": "error", "message": "Client ID required"})

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        ssl_sock = context.wrap_socket(sock, server_hostname=SERVER_HOST)
        ssl_sock.connect((SERVER_HOST, SERVER_PORT))
        ssl_sock.send(client_id.encode())
        msg = ssl_sock.recv(1024).decode()
        active_clients[client_id] = ssl_sock
        return jsonify({"status": "connected", "message": msg})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@client_bp.route("/execute_query", methods=["POST"])
def execute_query():
    data = request.get_json()
    client_id = data.get("clientId")
    query = data.get("query")
    ssl_sock = active_clients.get(client_id)
    if not ssl_sock:
        return jsonify({"status": "error", "response": "Not connected"})

    try:
        ssl_sock.send(query.encode())
        response = ssl_sock.recv(4096).decode()
        # Here, optionally, call teammate backend for ranking
        ranking = None  # replace with call to ranking backend when ready
        return jsonify({"status": "success", "response": response, "ranking": ranking})
    except Exception as e:
        return jsonify({"status": "error", "response": str(e)})
