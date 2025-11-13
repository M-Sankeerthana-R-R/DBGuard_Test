# import socket
# import threading
# import mysql.connector
# import time
# import os
# from monitor.activity_logger import log_activity  # Make sure your module is in PYTHONPATH

# HOST = '0.0.0.0'
# PORT = 5050

# # Define sensitive columns globally
# sensitive_columns = ['salary', 'ssn', 'password']

# # Connect to MySQL
# conn = mysql.connector.connect(
#     host='localhost',
#     port=3307,
#     user='root',
#     password='rootpassword',
#     database='mydb'
# )

# def classify_query(query):
#     q = query.strip().lower()
#     if q.startswith(("select", "show", "desc", "describe")):
#         return "select"
#     elif q.startswith(("insert", "create")):
#         return "alert-only"
#     elif any(q.startswith(cmd) for cmd in ["delete", "drop", "alter", "truncate", "update"]):
#         return "needs-approval"
#     else:
#         return "safe"

# def needs_sensitive_approval(client_id, query):
#     if "*" in query:
#         return True
#     for col in sensitive_columns:
#         if col in query.lower():
#             return True
#     return False

# def get_table_columns(table_name, cursor):
#     try:
#         cursor.execute(f"SHOW COLUMNS FROM {table_name}")
#         columns = [row[0] for row in cursor.fetchall()]
#         return columns
#     except:
#         return []

# def enforce_column_level(client_id, query, cursor):
#     query_lower = query.lower()
#     if "from" not in query_lower or "*" not in query:
#         return query  # No modification needed

#     try:
#         table = query_lower.split("from")[1].strip().split()[0]
#     except:
#         return query

#     all_columns = get_table_columns(table, cursor)
#     allowed_columns = [col for col in all_columns if col not in sensitive_columns]

#     if client_id == '99':
#         allowed_columns = allowed_columns[:2]  # e.g., restrict outsider to first 2 safe columns

#     return f"SELECT {', '.join(allowed_columns)} FROM {table}"

# def get_dba_approval(client_id, query):
#     print(f"\n[APPROVAL REQUIRED] Client {client_id} requested:\n{query}")
#     decision = input("Approve query? (yes/no): ").strip().lower()
#     return decision == 'yes'

# def handle_client(conn_socket, addr):
#     print(f"[CONNECTED] {addr}")
#     client_id = conn_socket.recv(1024).decode()

#     # Per-client cursor (with buffering)
#     thread_cursor = conn.cursor(buffered=True)

#     # Outsider special handling
#     if client_id == '99':
#         print(f"\n[OUTSIDER CONNECTION] Client {addr} is requesting access as outsider (ID 99).")
#         access = input("Allow outsider to connect? (yes/no): ").strip().lower()
#         if access != 'yes':
#             conn_socket.send("Access denied by DBA.".encode())
#             conn_socket.close()
#             print("[DISCONNECTED] Outsider was denied access.\n")
#             return
#         else:
#             conn_socket.send("Access granted. You may proceed.".encode())
#             print("[ACCESS GRANTED] Outsider connected.\n")
#     else:
#         conn_socket.send("Connected to server.".encode())

#     while True:
#         try:
#             query = conn_socket.recv(4096).decode()
#             if not query:
#                 break

#             start_time = time.time()
#             category = classify_query(query)
#             response = ""

#             if category == "safe":
#                 thread_cursor.execute(query)
#                 conn.commit()
#                 response = "Query executed."

#             elif category == "alert-only":
#                 print(f"[ALERT] Alert-only query from client {client_id}: {query}")
#                 thread_cursor.execute(query)
#                 conn.commit()
#                 response = "Query executed with DBA alert."

#             elif category == "needs-approval":
#                 approved = get_dba_approval(client_id, query)
#                 if approved:
#                     thread_cursor.execute(query)
#                     conn.commit()
#                     response = "Approved and executed."
#                 else:
#                     response = "Rejected by DBA."

#             elif category == "select":
#                 if needs_sensitive_approval(client_id, query):
#                     approved = get_dba_approval(client_id, query)
#                     if not approved:
#                         response = "Access denied by DBA."
#                         # Log and send response; result will be this message
#                         exec_time = time.time() - start_time
#                         try:
#                             log_activity(client_id, query, category.upper(), exec_time, response)
#                         except Exception as e:
#                             print(f"[LOG ERROR] {e}")
#                         conn_socket.send(response.encode())
#                         continue

#                 modified_query = enforce_column_level(client_id, query, thread_cursor)
#                 try:
#                     thread_cursor.execute(modified_query)
#                     results = thread_cursor.fetchall()
#                     # Format results to a readable string for client
#                     response = '\n'.join([str(row) for row in results]) or "No rows returned."
#                 except Exception as e:
#                     response = f"Error executing select: {e}"

#             exec_time = time.time() - start_time

#             # Log what the client actually saw (response)
#             try:
#                 log_activity(client_id, query, category.upper(), exec_time, response)
#             except Exception as e:
#                 print(f"[LOG ERROR] {e}")

#             # Send response to client
#             try:
#                 conn_socket.send(response.encode())
#             except Exception as e:
#                 print(f"[SEND ERROR] {e}")
#                 break

#         except Exception as e:
#             try:
#                 conn_socket.send(f"Error: {str(e)}".encode())
#             except:
#                 pass
#             print(f"[CLIENT HANDLER ERROR] {e}")
#             break

#     conn_socket.close()
#     thread_cursor.close()

# # Start server
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.bind((HOST, PORT))
# s.listen(5)
# print("[SERVER STARTED] Listening on port", PORT)

# while True:
#     conn_socket, addr = s.accept()
#     t = threading.Thread(target=handle_client, args=(conn_socket, addr))
#     t.start()



# import socket
# import ssl
# import threading
# import mysql.connector
# import time
# from monitor.activity_logger import log_activity  # your custom module

# conn = mysql.connector.connect(
#     host='localhost',
#     port=3307,
#     user='root',
#     password='rootpassword',
#     database='mydb'
# )

# context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# context.load_cert_chain(certfile="server.crt", keyfile="server.key")

# HOST = '0.0.0.0'
# PORT = 5050

# sensitive_columns = ['salary', 'ssn', 'password']

# def classify_query(query):
#     q = query.strip().lower()
#     if q.startswith(("select", "show", "desc", "describe")):
#         return "select"
#     elif q.startswith(("insert", "create")):
#         return "alert-only"
#     elif any(q.startswith(cmd) for cmd in ["delete", "drop", "alter", "truncate", "update"]):
#         return "needs-approval"
#     else:
#         return "safe"

# def needs_sensitive_approval(client_id, query):
#     if "*" in query:
#         return True
#     for col in sensitive_columns:
#         if col in query.lower():
#             return True
#     return False

# def get_table_columns(table_name, cursor):
#     try:
#         cursor.execute(f"SHOW COLUMNS FROM {table_name}")
#         columns = [row[0] for row in cursor.fetchall()]
#         return columns
#     except:
#         return []

# def enforce_column_level(client_id, query, cursor):
#     query_lower = query.lower()
#     if "from" not in query_lower or "*" not in query:
#         return query

#     try:
#         table = query_lower.split("from")[1].strip().split()[0]
#     except:
#         return query

#     all_columns = get_table_columns(table, cursor)
#     allowed_columns = [col for col in all_columns if col not in sensitive_columns]

#     if client_id == '99':
#         allowed_columns = allowed_columns[:2]

#     return f"SELECT {', '.join(allowed_columns)} FROM {table}"

# def get_dba_approval(client_id, query):
#     print(f"\n[APPROVAL REQUIRED] Client {client_id} requested:\n{query}")
#     decision = input("Approve query? (yes/no): ").strip().lower()
#     return decision == 'yes'

# def handle_client(conn_socket, addr):
#     print(f"[CONNECTED] {addr}")

#     try:
#         ssl_conn = context.wrap_socket(conn_socket, server_side=True)
#     except ssl.SSLError as e:
#         print(f"[SSL ERROR] {e}")
#         conn_socket.close()
#         return

#     client_id = ssl_conn.recv(1024).decode().strip()
#     thread_cursor = conn.cursor(buffered=True)

#     # Only 1,2,3 are insiders. Everyone else is outsider.
#     if client_id not in ["1", "2", "3"]:
#         print(f"\n[OUTSIDER CONNECTION] Client {addr} with ID {client_id} is requesting access.")
#         access = input("Allow outsider to connect? (yes/no): ").strip().lower()
#         if access != 'yes':
#             ssl_conn.send("Access denied by DBA.".encode())
#             ssl_conn.close()
#             print(f"[DISCONNECTED] Outsider {client_id} was denied access.\n")
#             return
#         else:
#             ssl_conn.send("Access granted. You may proceed.".encode())
#             print(f"[ACCESS GRANTED] Outsider {client_id} connected.\n")
#     else:
#         ssl_conn.send(f"Welcome Client {client_id}, access granted.".encode())


#     while True:
#         try:
#             query = ssl_conn.recv(4096).decode()
#             if not query:
#                 break

#             start_time = time.time()
#             category = classify_query(query)
#             response = ""

#             if category == "safe":
#                 thread_cursor.execute(query)
#                 conn.commit()
#                 response = "Query executed."

#             elif category == "alert-only":
#                 print(f"[ALERT] Alert-only query from client {client_id}: {query}")
#                 thread_cursor.execute(query)
#                 conn.commit()
#                 response = "Query executed with DBA alert."

#             elif category == "needs-approval":
#                 approved = get_dba_approval(client_id, query)
#                 if approved:
#                     thread_cursor.execute(query)
#                     conn.commit()
#                     response = "Approved and executed."
#                 else:
#                     response = "Rejected by DBA."

#             elif category == "select":
#                 if needs_sensitive_approval(client_id, query):
#                     approved = get_dba_approval(client_id, query)
#                     if not approved:
#                         response = "Access denied by DBA."
#                         exec_time = time.time() - start_time
#                         try:
#                             log_activity(client_id, query, category.upper(), exec_time, response)
#                         except Exception as e:
#                             print(f"[LOG ERROR] {e}")
#                         ssl_conn.send(response.encode())
#                         continue

#                 modified_query = enforce_column_level(client_id, query, thread_cursor)
#                 try:
#                     thread_cursor.execute(modified_query)
#                     results = thread_cursor.fetchall()
#                     response = '\n'.join([str(row) for row in results]) or "No rows returned."
#                 except Exception as e:
#                     response = f"Error executing select: {e}"

#             exec_time = time.time() - start_time

#             try:
#                 log_activity(client_id, query, category.upper(), exec_time, response)
#             except Exception as e:
#                 print(f"[LOG ERROR] {e}")

#             ssl_conn.send(response.encode())

#         except Exception as e:
#             try:
#                 ssl_conn.send(f"Error: {str(e)}".encode())
#             except:
#                 pass
#             print(f"[CLIENT HANDLER ERROR] {e}")
#             break

#     ssl_conn.close()
#     thread_cursor.close()

# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.bind((HOST, PORT))
# s.listen(5)
# print("[SERVER STARTED] Listening on port", PORT)

# while True:
#     conn_socket, addr = s.accept()
#     t = threading.Thread(target=handle_client, args=(conn_socket, addr))
#     t.start()


# import socket
# import ssl
# import threading
# import mysql.connector
# import time
# import json
# from monitor.activity_logger import log_activity  # your custom module
# from monitor.slow_query_analyzer import analyze_root_causes

# # -------------------------------
# # MySQL connection
# # -------------------------------
# conn = mysql.connector.connect(
#     host='localhost',
#     port=3307,
#     user='root',
#     password='rootpassword',
#     database='mydb'
# )

# # -------------------------------
# # SSL setup
# # -------------------------------
# context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# context.load_cert_chain(certfile="server.crt", keyfile="server.key")

# # -------------------------------
# # Server info
# # -------------------------------
# HOST = '0.0.0.0'
# PORT = 5050

# # -------------------------------
# # Sensitive columns
# # -------------------------------
# sensitive_columns = ['salary', 'ssn', 'password']

# # -------------------------------
# # Query classification
# # -------------------------------
# def classify_query(query):
#     q = query.strip().lower()
#     if q.startswith(("select", "show", "desc", "describe")):
#         return "select"
#     elif q.startswith(("insert", "create")):
#         return "alert-only"
#     elif any(q.startswith(cmd) for cmd in ["delete", "drop", "alter", "truncate", "update"]):
#         return "needs-approval"
#     else:
#         return "safe"

# def needs_sensitive_approval(client_id, query):
#     if "*" in query:
#         return True
#     for col in sensitive_columns:
#         if col in query.lower():
#             return True
#     return False

# def get_table_columns(table_name, cursor):
#     try:
#         cursor.execute(f"SHOW COLUMNS FROM {table_name}")
#         columns = [row[0] for row in cursor.fetchall()]
#         return columns
#     except:
#         return []

# def enforce_column_level(client_id, query, cursor):
#     query_lower = query.lower()
#     if "from" not in query_lower or "*" not in query:
#         return query

#     try:
#         table = query_lower.split("from")[1].strip().split()[0]
#     except:
#         return query

#     all_columns = get_table_columns(table, cursor)
#     allowed_columns = [col for col in all_columns if col not in sensitive_columns]

#     if client_id == '99':
#         allowed_columns = allowed_columns[:2]

#     return f"SELECT {', '.join(allowed_columns)} FROM {table}"

# def get_dba_approval(client_id, query):
#     print(f"\n[APPROVAL REQUIRED] Client {client_id} requested:\n{query}")
#     decision = input("Approve query? (yes/no): ").strip().lower()
#     return decision == 'yes'

# # -------------------------------
# # Handle each client
# # -------------------------------
# # def handle_client(conn_socket, addr):
# #     print(f"[CONNECTED] {addr}")

# #     try:
# #         ssl_conn = context.wrap_socket(conn_socket, server_side=True)
# #     except ssl.SSLError as e:
# #         print(f"[SSL ERROR] {e}")
# #         conn_socket.close()
# #         return

# #     client_id = ssl_conn.recv(1024).decode().strip()
# #     thread_cursor = conn.cursor(buffered=True)

# #     # Only 1,2,3 are insiders. Everyone else is outsider.
# #     if client_id not in ["1", "2", "3"]:
# #         print(f"\n[OUTSIDER CONNECTION] Client {addr} with ID {client_id} is requesting access.")
# #         access = input("Allow outsider to connect? (yes/no): ").strip().lower()
# #         if access != 'yes':
# #             ssl_conn.send("Access denied by DBA.".encode())
# #             ssl_conn.close()
# #             print(f"[DISCONNECTED] Outsider {client_id} was denied access.\n")
# #             return
# #         else:
# #             ssl_conn.send("Access granted. You may proceed.".encode())
# #             print(f"[ACCESS GRANTED] Outsider {client_id} connected.\n")
# #     else:
# #         ssl_conn.send(f"Welcome Client {client_id}, access granted.".encode())

# #     while True:
# #         try:
# #             query = ssl_conn.recv(4096).decode()
# #             if not query:
# #                 break

# #             start_time = time.time()
# #             category = classify_query(query)
# #             response = ""

# #             # -------------------------------
# #             # Execute query based on category
# #             # -------------------------------
# #             if category == "safe":
# #                 thread_cursor.execute(query)
# #                 conn.commit()
# #                 response = "Query executed."

# #             elif category == "alert-only":
# #                 print(f"[ALERT] Alert-only query from client {client_id}: {query}")
# #                 thread_cursor.execute(query)
# #                 conn.commit()
# #                 response = "Query executed with DBA alert."

# #             elif category == "needs-approval":
# #                 approved = get_dba_approval(client_id, query)
# #                 if approved:
# #                     thread_cursor.execute(query)
# #                     conn.commit()
# #                     response = "Approved and executed."
# #                 else:
# #                     response = "Rejected by DBA."

# #             elif category == "select":
# #                 if needs_sensitive_approval(client_id, query):
# #                     approved = get_dba_approval(client_id, query)
# #                     if not approved:
# #                         response = "Access denied by DBA."
# #                         exec_time = time.time() - start_time
# #                         try:
# #                             # -------------------------------
# #                             # Compute root cause ranking
# #                             # -------------------------------
# #                             ranking_list = analyze_root_causes(query)
# #                             ranking_str = json.dumps(ranking_list)
# #                         except Exception as e:
# #                             print(f"[RANKING ERROR] {e}")
# #                             ranking_str = ""
# #                         try:
# #                             log_activity(client_id, query, category.upper(), exec_time, response, ranking_str)
# #                         except Exception as e:
# #                             print(f"[LOG ERROR] {e}")
# #                         ssl_conn.send(response.encode())
# #                         continue

# #                 modified_query = enforce_column_level(client_id, query, thread_cursor)
# #                 try:
# #                     thread_cursor.execute(modified_query)
# #                     results = thread_cursor.fetchall()
# #                     response = '\n'.join([str(row) for row in results]) or "No rows returned."
# #                 except Exception as e:
# #                     response = f"Error executing select: {e}"

# #             # -------------------------------
# #             # Measure execution time
# #             # -------------------------------
# #             exec_time = time.time() - start_time

# #             # -------------------------------
# #             # Compute root cause ranking for all queries
# #             # -------------------------------
# #             try:
# #                 ranking_list = analyze_root_causes(query)
# #                 ranking_str = json.dumps(ranking_list)
# #             except Exception as e:
# #                 print(f"[RANKING ERROR] {e}")
# #                 ranking_str = ""

# #             # -------------------------------
# #             # Log query + ranking
# #             # -------------------------------
# #             try:
# #                 log_activity(client_id, query, category.upper(), exec_time, response)
# #             except Exception as e:
# #                 print(f"[LOG ERROR] {e}")

# #             # Send response to client
# #             ssl_conn.send(json.dumps({
# #                 "response": response,
# #                 "ranking": ranking_list  # list of dicts from analyze_root_causes
# #             }).encode())

# #         except Exception as e:
# #             try:
# #                 ssl_conn.send(f"Error: {str(e)}".encode())
# #             except:
# #                 pass
# #             print(f"[CLIENT HANDLER ERROR] {e}")
# #             break

# #     ssl_conn.close()
# #     thread_cursor.close()
# def handle_client(conn_socket, addr):
#     print(f"[CONNECTED] {addr}")

#     try:
#         ssl_conn = context.wrap_socket(conn_socket, server_side=True)
#     except ssl.SSLError as e:
#         print(f"[SSL ERROR] {e}")
#         conn_socket.close()
#         return

#     client_id = ssl_conn.recv(1024).decode().strip()
#     thread_cursor = conn.cursor(buffered=True)

#     if client_id not in ["1", "2", "3"]:
#         print(f"[OUTSIDER CONNECTION] Client {addr} with ID {client_id} requesting access.")
#         access = input("Allow outsider to connect? (yes/no): ").strip().lower()
#         if access != 'yes':
#             ssl_conn.send("Access denied by DBA.".encode())
#             ssl_conn.close()
#             print(f"[DISCONNECTED] Outsider {client_id} denied.\n")
#             return
#         else:
#             ssl_conn.send("Access granted. You may proceed.".encode())
#             print(f"[ACCESS GRANTED] Outsider {client_id} connected.\n")
#     else:
#         ssl_conn.send(f"Welcome Client {client_id}, access granted.".encode())

#     while True:
#         try:
#             query = ssl_conn.recv(4096).decode()
#             if not query:
#                 break

#             start_time = time.time()
#             category = classify_query(query)
#             response = ""

#             # -------------------------------
#             # Execute query based on category
#             # -------------------------------
#             if category == "safe" or category == "alert-only":
#                 if category == "alert-only":
#                     print(f"[ALERT] Alert-only query from client {client_id}: {query}")
#                 thread_cursor.execute(query)
#                 conn.commit()
#                 response = "Query executed." if category == "safe" else "Query executed with DBA alert."

#             elif category == "needs-approval":
#                 approved = get_dba_approval(client_id, query)
#                 if approved:
#                     thread_cursor.execute(query)
#                     conn.commit()
#                     response = "Approved and executed."
#                 else:
#                     response = "Rejected by DBA."

#             elif category == "select":
#                 if needs_sensitive_approval(client_id, query):
#                     approved = get_dba_approval(client_id, query)
#                     if not approved:
#                         response = "Access denied by DBA."
#                         exec_time = time.time() - start_time
#                         try:
#                             ranking_list = analyze_root_causes(query)
#                         except Exception as e:
#                             print(f"[RANKING ERROR] {e}")
#                             ranking_list = []
#                         try:
#                             log_activity(client_id, query, category.upper(), exec_time, response, ranking_list)
#                         except Exception as e:
#                             print(f"[LOG ERROR] {e}")
#                         ssl_conn.send(json.dumps({"response": response, "ranking": ranking_list}).encode())
#                         continue

#                 modified_query = enforce_column_level(client_id, query, thread_cursor)
#                 try:
#                     thread_cursor.execute(modified_query)
#                     results = thread_cursor.fetchall()
#                     response = '\n'.join([str(row) for row in results]) or "No rows returned."
#                 except Exception as e:
#                     response = f"Error executing select: {e}"

#             exec_time = time.time() - start_time

#             # -------------------------------
#             # Compute root cause ranking
#             # -------------------------------
#             try:
#                 ranking_list = analyze_root_causes(query)
#             except Exception as e:
#                 print(f"[RANKING ERROR] {e}")
#                 ranking_list = []

#             # -------------------------------
#             # Log everything including ranking
#             # -------------------------------
#             try:
#                 log_activity(client_id, query, category.upper(), exec_time, response, ranking_list)
#             except Exception as e:
#                 print(f"[LOG ERROR] {e}")

#             # Send response + ranking to client
#             ssl_conn.send(json.dumps({"response": response, "ranking": ranking_list}).encode())

#         except Exception as e:
#             try:
#                 ssl_conn.send(f"Error: {str(e)}".encode())
#             except:
#                 pass
#             print(f"[CLIENT HANDLER ERROR] {e}")
#             break

#     ssl_conn.close()
#     thread_cursor.close()

# # -------------------------------
# # Start server
# # -------------------------------
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.bind((HOST, PORT))
# s.listen(5)
# print("[SERVER STARTED] Listening on port", PORT)

# while True:
#     conn_socket, addr = s.accept()
#     t = threading.Thread(target=handle_client, args=(conn_socket, addr))
#     t.start()

import socket
import ssl
import threading
import mysql.connector
import time
import json
from monitor.activity_logger import log_activity
from monitor.slow_query_analyzer import analyze_root_causes

# -------------------------------
# MySQL connection
# -------------------------------
conn = mysql.connector.connect(
    host='localhost',
    port=3306,
    user='root',
    password='root',
    database='rcranker_test'
)

# -------------------------------
# SSL setup
# -------------------------------
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="server.crt", keyfile="server.key")

HOST = '127.0.0.1'  # Changed to localhost for local testing
PORT = 5050
sensitive_columns = ['salary', 'ssn', 'password']


# -------------------------------
# Query classification
# -------------------------------
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
    # Temporarily disabled for testing
    return False
    # if "*" in query:
    #     return True
    # for col in sensitive_columns:
    #     if col in query.lower():
    #         return True
    # return False


def get_table_columns(table_name, cursor):
    try:
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        return [row[0] for row in cursor.fetchall()]
    except:
        return []


def enforce_column_level(client_id, query, cursor):
    q_lower = query.lower()
    if "from" not in q_lower or "*" not in query:
        return query
    try:
        table = q_lower.split("from")[1].strip().split()[0]
    except Exception:
        return query

    cols = get_table_columns(table, cursor)
    allowed = [c for c in cols if c not in sensitive_columns]
    if not allowed:
        return query
    if client_id == '99':
        allowed = allowed[:2]
    return f"SELECT {', '.join(allowed)} FROM {table}"


def get_dba_approval(client_id, query):
    print(f"\n[APPROVAL REQUIRED] Client {client_id} requested:\n{query}")
    decision = input("Approve query? (yes/no): ").strip().lower()
    return decision == 'yes'


# -------------------------------
# Client handler
# -------------------------------
def handle_client(conn_socket, addr):
    print(f"[CONNECTED] {addr}")

    try:
        ssl_conn = context.wrap_socket(conn_socket, server_side=True)
    except ssl.SSLError as e:
        print(f"[SSL ERROR] {e}")
        conn_socket.close()
        return

    client_id = ssl_conn.recv(1024).decode().strip()
    cursor = conn.cursor(buffered=True)

    # Insider/outsider access check
    if client_id not in ["1", "2", "3"]:
        print(f"\n[OUTSIDER CONNECTION] {addr} ({client_id}) requesting access.")
        access = input("Allow outsider? (yes/no): ").strip().lower()
        if access != "yes":
            ssl_conn.send("Access denied by DBA.".encode())
            ssl_conn.close()
            print(f"[DISCONNECTED] Outsider {client_id} denied.\n")
            return
        ssl_conn.send("Access granted. You may proceed.".encode())
    else:
        ssl_conn.send(f"Welcome Client {client_id}, access granted.".encode())

    while True:
        try:
            query = ssl_conn.recv(4096).decode()
            if not query:
                break

            start = time.time()
            category = classify_query(query)
            response = ""
            ranking_list = []  # always defined

            # -------------------------------
            # Execute query based on category
            # -------------------------------
            if category in ["safe", "alert-only"]:
                if category == "alert-only":
                    print(f"[ALERT] Alert-only query from {client_id}: {query}")
                cursor.execute(query)
                conn.commit()
                response = "Query executed."

            elif category == "needs-approval":
                if get_dba_approval(client_id, query):
                    cursor.execute(query)
                    conn.commit()
                    response = "Approved and executed."
                else:
                    response = "Rejected by DBA."

            elif category == "select":
                if needs_sensitive_approval(client_id, query):
                    if not get_dba_approval(client_id, query):
                        response = "Access denied by DBA."
                        exec_time = time.time() - start
                        try:
                            analysis = analyze_root_causes(query)
                            status = analysis.get("status", "Normal")
                            root_cause = analysis.get("root_cause", "None")
                            score = analysis.get("score", 0.0)
                        except Exception as e:
                            print(f"[RANKING ERROR] {e}")
                            status, root_cause, score = "Unknown", "N/A", 0.0
                        log_activity(client_id, query, category.upper(), exec_time, response,
                                     {"status": status, "root_cause": root_cause, "score": score})
                        ssl_conn.send(json.dumps({
                            "query": query,
                            "response": response,
                            "status": status,
                            "root_cause": root_cause,
                            "score": score
                        }).encode())
                        continue

                modified = enforce_column_level(client_id, query, cursor)
                try:
                    cursor.execute(modified)
                    rows = cursor.fetchall()
                    response = "\n".join([str(r) for r in rows]) or "No rows returned."
                except Exception as e:
                    response = f"Error executing select: {e}"

            exec_time = time.time() - start

            # -------------------------------
            # Analyze with model
            # -------------------------------
            try:
                analysis = analyze_root_causes(query)
                status = analysis.get("status", "Normal")
                root_cause = analysis.get("root_cause", "None")
                score = analysis.get("score", 0.0)
            except Exception as e:
                print(f"[RANKING ERROR] {e}")
                status, root_cause, score = "Unknown", "N/A", 0.0

            # -------------------------------
            # Log and send back
            # -------------------------------
            try:
                log_activity(client_id, query, category.upper(), exec_time, response,
                             {"status": status, "root_cause": root_cause, "score": score})
            except Exception as e:
                print(f"[LOG ERROR] {e}")

            ssl_conn.send(json.dumps({
                "query": query,
                "response": response,
                "status": status,
                "root_cause": root_cause,
                "score": score
            }).encode())

        except Exception as e:
            print(f"[CLIENT HANDLER ERROR] {e}")
            try:
                ssl_conn.send(f"Error: {str(e)}".encode())
            except:
                pass
            break

    ssl_conn.close()
    cursor.close()


# -------------------------------
# Start Server
# -------------------------------
if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(5)
    print("[SERVER STARTED] Listening on port", PORT)

    while True:
        conn_socket, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn_socket, addr)).start()
