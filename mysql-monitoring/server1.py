import socket
import threading
import mysql.connector
import time
from monitor.activity_logger import log_activity  # your custom module

conn = mysql.connector.connect(
    host='localhost',
    port=3307,
    user='root',
    password='rootpassword',
    database='mydb'
)

HOST = '0.0.0.0'
PORT = 5050

sensitive_columns = ['salary', 'ssn', 'password']

def classify_query(query):
    q = query.strip().lower()
    if q.startswith(("select", "show", "desc", "describe")):
        return "select"
    elif q.startswith(("insert", "create")):
        return "alert-only"
    elif any(q.startswith(cmd) for cmd in ["delete", "drop", "alter", "truncate", "update"]):
        return "needs-approval"
    else:
        return "safe"

def needs_sensitive_approval(client_id, query):
    if "*" in query:
        return True
    for col in sensitive_columns:
        if col in query.lower():
            return True
    return False

def get_table_columns(table_name, cursor):
    try:
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = [row[0] for row in cursor.fetchall()]
        return columns
    except:
        return []

def enforce_column_level(client_id, query, cursor):
    query_lower = query.lower()
    if "from" not in query_lower or "*" not in query:
        return query

    try:
        table = query_lower.split("from")[1].strip().split()[0]
    except:
        return query

    all_columns = get_table_columns(table, cursor)
    allowed_columns = [col for col in all_columns if col not in sensitive_columns]

    if client_id == '99':
        allowed_columns = allowed_columns[:2]

    return f"SELECT {', '.join(allowed_columns)} FROM {table}"

def get_dba_approval(client_id, query):
    print(f"\n[APPROVAL REQUIRED] Client {client_id} requested:\n{query}")
    decision = input("Approve query? (yes/no): ").strip().lower()
    return decision == 'yes'

def handle_client(conn_socket, addr):
    print(f"[CONNECTED] {addr}")

    client_id = conn_socket.recv(1024).decode().strip()
    thread_cursor = conn.cursor(buffered=True)

    # Only 1,2,3 are insiders. Everyone else is outsider.
    if client_id not in ["1", "2", "3"]:
        print(f"\n[OUTSIDER CONNECTION] Client {addr} with ID {client_id} is requesting access.")
        access = input("Allow outsider to connect? (yes/no): ").strip().lower()
        if access != 'yes':
            conn_socket.send("Access denied by DBA.".encode())
            conn_socket.close()
            print(f"[DISCONNECTED] Outsider {client_id} was denied access.\n")
            return
        else:
            conn_socket.send("Access granted. You may proceed.".encode())
            print(f"[ACCESS GRANTED] Outsider {client_id} connected.\n")
    else:
        conn_socket.send(f"Welcome Client {client_id}, access granted.".encode())

    while True:
        try:
            query = conn_socket.recv(4096).decode()
            if not query:
                break

            start_time = time.time()
            category = classify_query(query)
            response = ""

            if category == "safe":
                thread_cursor.execute(query)
                conn.commit()
                response = "Query executed."

            elif category == "alert-only":
                print(f"[ALERT] Alert-only query from client {client_id}: {query}")
                thread_cursor.execute(query)
                conn.commit()
                response = "Query executed with DBA alert."

            elif category == "needs-approval":
                approved = get_dba_approval(client_id, query)
                if approved:
                    thread_cursor.execute(query)
                    conn.commit()
                    response = "Approved and executed."
                else:
                    response = "Rejected by DBA."

            elif category == "select":
                if needs_sensitive_approval(client_id, query):
                    approved = get_dba_approval(client_id, query)
                    if not approved:
                        response = "Access denied by DBA."
                        exec_time = time.time() - start_time
                        try:
                            log_activity(client_id, query, category.upper(), exec_time, response)
                        except Exception as e:
                            print(f"[LOG ERROR] {e}")
                        conn_socket.send(response.encode())
                        continue

                modified_query = enforce_column_level(client_id, query, thread_cursor)
                try:
                    thread_cursor.execute(modified_query)
                    results = thread_cursor.fetchall()
                    response = '\n'.join([str(row) for row in results]) or "No rows returned."
                except Exception as e:
                    response = f"Error executing select: {e}"

            exec_time = time.time() - start_time

            try:
                log_activity(client_id, query, category.upper(), exec_time, response)
            except Exception as e:
                print(f"[LOG ERROR] {e}")

            conn_socket.send(response.encode())

        except Exception as e:
            try:
                conn_socket.send(f"Error: {str(e)}".encode())
            except:
                pass
            print(f"[CLIENT HANDLER ERROR] {e}")
            break

    conn_socket.close()
    thread_cursor.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(5)
print("[SERVER STARTED] Listening on port", PORT)

while True:
    conn_socket, addr = s.accept()
    t = threading.Thread(target=handle_client, args=(conn_socket, addr))
    t.start()