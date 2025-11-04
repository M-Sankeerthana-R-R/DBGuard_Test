from flask import Blueprint, request, jsonify
import socket
import ssl
import time
import json
import os

client_bp = Blueprint("client_bp", __name__)

# Store active client connections
active_clients = {}

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5050
SENSITIVE_COLUMNS = ["salary", "ssn", "password"]

# Path to connected clients file
CONNECTED_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'connected_clients.json')

def update_connected_clients_file():
    """Update the connected_clients.json file with current active clients"""
    try:
        os.makedirs(os.path.dirname(CONNECTED_FILE), exist_ok=True)
        with open(CONNECTED_FILE, 'w', encoding='utf-8') as f:
            # Store list of connected client IDs
            connected_list = list(active_clients.keys())
            json.dump(connected_list, f, indent=2)
        print(f"[Connected Clients] Updated file: {connected_list}")
    except Exception as e:
        print(f"[Connected Clients] Error updating file: {e}")

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
        update_connected_clients_file()  # Update the file
        print(f"[Connect] Client {client_id} connected. Total active: {len(active_clients)}")
        return jsonify({"status": "connected", "message": msg})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@client_bp.route("/disconnect", methods=["POST"])
def disconnect():
    """Disconnect a client and update the connected clients file"""
    data = request.get_json()
    client_id = data.get("clientId")
    
    if not client_id:
        return jsonify({"status": "error", "message": "Client ID required"})
    
    try:
        if client_id in active_clients:
            # Close the socket connection
            try:
                active_clients[client_id].close()
            except:
                pass
            
            # Remove from active clients
            del active_clients[client_id]
            update_connected_clients_file()  # Update the file
            print(f"[Disconnect] Client {client_id} disconnected. Total active: {len(active_clients)}")
            return jsonify({"status": "disconnected", "message": f"Client {client_id} disconnected"})
        else:
            return jsonify({"status": "error", "message": "Client not connected"})
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
