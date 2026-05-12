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

# import socket
# import ssl
# import threading
# import mysql.connector
# import time
# import json
# from monitor.activity_logger import log_activity
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

# HOST = '127.0.0.1'
# PORT = 5050
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
#         return [row[0] for row in cursor.fetchall()]
#     except:
#         return []


# def enforce_column_level(client_id, query, cursor):
#     q_lower = query.lower()
#     if "from" not in q_lower or "*" not in query:
#         return query
#     try:
#         table = q_lower.split("from")[1].strip().split()[0]
#     except Exception:
#         return query

#     cols = get_table_columns(table, cursor)
#     allowed = [c for c in cols if c not in sensitive_columns]
#     if not allowed:
#         return query
#     if client_id == '99':
#         allowed = allowed[:2]
#     return f"SELECT {', '.join(allowed)} FROM {table}"


# def get_dba_approval(client_id, query):
#     print(f"\n[APPROVAL REQUIRED] Client {client_id} requested:\n{query}")
#     decision = input("Approve query? (yes/no): ").strip().lower()
#     return decision == 'yes'


# # -------------------------------
# # Client handler
# # -------------------------------
# def handle_client(conn_socket, addr):
#     print(f"[CONNECTED] {addr}")

#     try:
#         ssl_conn = context.wrap_socket(conn_socket, server_side=True)
#     except ssl.SSLError as e:
#         print(f"[SSL ERROR] {e}")
#         conn_socket.close()
#         return

#     client_id = ssl_conn.recv(1024).decode().strip()
#     cursor = conn.cursor(buffered=True)

#     # Insider/outsider access check
#     if client_id not in ["1", "2", "3"]:
#         print(f"\n[OUTSIDER CONNECTION] {addr} ({client_id}) requesting access.")
#         access = input("Allow outsider? (yes/no): ").strip().lower()
#         if access != "yes":
#             ssl_conn.send("Access denied by DBA.".encode())
#             ssl_conn.close()
#             print(f"[DISCONNECTED] Outsider {client_id} denied.\n")
#             return
#         ssl_conn.send("Access granted. You may proceed.".encode())
#     else:
#         ssl_conn.send(f"Welcome Client {client_id}, access granted.".encode())

#     while True:
#         try:
#             query = ssl_conn.recv(4096).decode()
#             if not query:
#                 break

#             start = time.time()
#             category = classify_query(query)
#             response = ""
#             ranking_list = []  # always defined

#             # -------------------------------
#             # Execute query based on category
#             # -------------------------------
#             if category in ["safe", "alert-only"]:
#                 if category == "alert-only":
#                     print(f"[ALERT] Alert-only query from {client_id}: {query}")
#                 cursor.execute(query)
#                 conn.commit()
#                 response = "Query executed."

#             elif category == "needs-approval":
#                 if get_dba_approval(client_id, query):
#                     cursor.execute(query)
#                     conn.commit()
#                     response = "Approved and executed."
#                 else:
#                     response = "Rejected by DBA."

#             elif category == "select":
#                 if needs_sensitive_approval(client_id, query):
#                     if not get_dba_approval(client_id, query):
#                         response = "Access denied by DBA."
#                         exec_time = time.time() - start
#                         try:
#                             analysis = analyze_root_causes(query)
#                             status = analysis.get("status", "Normal")
#                             root_cause = analysis.get("root_cause", "None")
#                             score = analysis.get("score", 0.0)
#                         except Exception as e:
#                             print(f"[RANKING ERROR] {e}")
#                             status, root_cause, score = "Unknown", "N/A", 0.0
#                         log_activity(client_id, query, category.upper(), exec_time, response,
#                                      {"status": status, "root_cause": root_cause, "score": score})
#                         ssl_conn.send(json.dumps({
#                             "query": query,
#                             "response": response,
#                             "status": status,
#                             "root_cause": root_cause,
#                             "score": score
#                         }).encode())
#                         continue

#                 modified = enforce_column_level(client_id, query, cursor)
#                 try:
#                     cursor.execute(modified)
#                     rows = cursor.fetchall()
#                     response = "\n".join([str(r) for r in rows]) or "No rows returned."
#                 except Exception as e:
#                     response = f"Error executing select: {e}"

#             exec_time = time.time() - start

#             # -------------------------------
#             # Analyze with model
#             # -------------------------------
#             try:
#                 analysis = analyze_root_causes(query)
#                 status = analysis.get("status", "Normal")
#                 root_cause = analysis.get("root_cause", "None")
#                 score = analysis.get("score", 0.0)
#             except Exception as e:
#                 print(f"[RANKING ERROR] {e}")
#                 status, root_cause, score = "Unknown", "N/A", 0.0

#             # -------------------------------
#             # Log and send back
#             # -------------------------------
#             try:
#                 log_activity(client_id, query, category.upper(), exec_time, response,
#                              {"status": status, "root_cause": root_cause, "score": score})
#             except Exception as e:
#                 print(f"[LOG ERROR] {e}")

#             ssl_conn.send(json.dumps({
#                 "query": query,
#                 "response": response,
#                 "status": status,
#                 "root_cause": root_cause,
#                 "score": score
#             }).encode())

#         except Exception as e:
#             print(f"[CLIENT HANDLER ERROR] {e}")
#             try:
#                 ssl_conn.send(f"Error: {str(e)}".encode())
#             except:
#                 pass
#             break

#     ssl_conn.close()
#     cursor.close()


# # -------------------------------
# # Start Server
# # -------------------------------
# if __name__ == "__main__":
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.bind((HOST, PORT))
#     s.listen(5)
#     print("[SERVER STARTED] Listening on port", PORT)

#     while True:
#         conn_socket, addr = s.accept()
#         threading.Thread(target=handle_client, args=(conn_socket, addr)).start()

# import socket
# import ssl
# import threading
# import queue
# import mysql.connector
# import time
# import json
# from monitor.activity_logger import log_activity
# from monitor.slow_query_analyzer import analyze_root_causes

# # -------------------------------
# # Database config
# # -------------------------------
# DB_CONFIG = {
#     "host": "localhost",
#     "port": 3307,
#     "user": "root",
#     "password": "rootpassword",
#     "database": "mydb"
# }

# # -------------------------------
# # SSL setup
# # -------------------------------
# context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# context.load_cert_chain(certfile="server.crt", keyfile="server.key")

# HOST = "127.0.0.1"
# PORT = 5050
# sensitive_columns = ["salary", "ssn", "password"]

# # -------------------------------
# # Global queue for approval requests
# # -------------------------------
# approval_queue = queue.Queue()

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
#         return [row[0] for row in cursor.fetchall()]
#     except:
#         return []

# def enforce_column_level(client_id, query, cursor):
#     q_lower = query.lower()
#     if "from" not in q_lower or "*" not in query:
#         return query
#     try:
#         table = q_lower.split("from")[1].strip().split()[0]
#     except Exception:
#         return query
#     cols = get_table_columns(table, cursor)
#     allowed = [c for c in cols if c not in sensitive_columns]
#     if not allowed:
#         return query
#     if client_id == "99":
#         allowed = allowed[:2]
#     return f"SELECT {', '.join(allowed)} FROM {table}"

# # -------------------------------
# # Helpers
# # -------------------------------
# def safe_analyze(query):
#     try:
#         result = analyze_root_causes(query)
#         return {
#             "status": result.get("status", "Normal"),
#             "root_cause": result.get("root_cause", "None"),
#             "score": result.get("score", 0.0),
#         }
#     except Exception as e:
#         print(f"[RANKING ERROR] {e}")
#         return {"status": "Unknown", "root_cause": "N/A", "score": 0.0}

# def send_safe_json(ssl_conn, query, response, analysis):
#     try:
#         ssl_conn.send(
#             json.dumps(
#                 {
#                     "query": query,
#                     "response": response,
#                     "status": analysis["status"],
#                     "root_cause": analysis["root_cause"],
#                     "score": analysis["score"],
#                 }
#             ).encode()
#         )
#     except Exception as e:
#         print(f"[SEND ERROR] {e}")

# # -------------------------------
# # Client handler
# # -------------------------------
# def handle_client(conn_socket, addr):
#     print(f"[CONNECTED] {addr}")
#     conn_socket.settimeout(10.0)

#     try:
#         ssl_conn = context.wrap_socket(conn_socket, server_side=True)
#     except ssl.SSLError as e:
#         print(f"[SSL ERROR during handshake] {e}")
#         conn_socket.close()
#         return

#     try:
#         client_id = ssl_conn.recv(1024).decode().strip()
#     except Exception as e:
#         print(f"[RECV ERROR client_id] {e}")
#         ssl_conn.close()
#         return

#     # New MySQL connection per thread
#     try:
#         db_conn = mysql.connector.connect(**DB_CONFIG)
#         cursor = db_conn.cursor(buffered=True)
#     except Exception as e:
#         print(f"[DB ERROR] Could not connect to MySQL: {e}")
#         ssl_conn.send("Database connection failed.".encode())
#         ssl_conn.close()
#         return

#     # Insider/outsider access
#     if client_id not in ["1", "2", "3"]:
#         print(f"\n[OUTSIDER CONNECTION] {addr} ({client_id}) requesting access.")
#         access = input("Allow outsider? (yes/no): ").strip().lower()
#         if access != "yes":
#             ssl_conn.send("Access denied by DBA.".encode())
#             ssl_conn.close()
#             cursor.close()
#             db_conn.close()
#             return
#         ssl_conn.send("Access granted. You may proceed.".encode())
#     else:
#         ssl_conn.send(f"Welcome Client {client_id}, access granted.".encode())

#     while True:
#         try:
#             ssl_conn.settimeout(30.0)
#             query_data = ssl_conn.recv(4096)
#             if not query_data:
#                 break

#             query = query_data.decode().strip()
#             start = time.time()
#             category = classify_query(query)
#             response = ""

#             if category == "needs-approval" or (category == "select" and needs_sensitive_approval(client_id, query)):
#                 # Instead of calling input() here — send to queue
#                 print(f"[QUEUE] Approval required for {client_id}: {query}")
#                 approval_queue.put((client_id, query, ssl_conn, db_conn, cursor, category))
#                 continue  # main thread will handle it

#             if category in ["safe", "alert-only"]:
#                 if category == "alert-only":
#                     print(f"[ALERT] Alert-only query from {client_id}: {query}")
#                 cursor.execute(query)
#                 db_conn.commit()
#                 response = "Query executed."
#             elif category == "select":
#                 modified = enforce_column_level(client_id, query, cursor)
#                 cursor.execute(modified)
#                 rows = cursor.fetchall()
#                 response = "\n".join([str(r) for r in rows]) or "No rows returned."

#             exec_time = time.time() - start
#             analysis = safe_analyze(query)
#             log_activity(client_id, query, category.upper(), exec_time, response, analysis)
#             send_safe_json(ssl_conn, query, response, analysis)

#         except (ssl.SSLError, ConnectionResetError, BrokenPipeError) as e:
#             print(f"[DISCONNECT] Client {client_id}: {e}")
#             break
#         except socket.timeout:
#             print(f"[TIMEOUT] Client {client_id} idle too long. Disconnecting.")
#             break
#         except Exception as e:
#             print(f"[CLIENT ERROR] {e}")
#             try:
#                 ssl_conn.send(f"Error: {str(e)}".encode())
#             except:
#                 pass
#             break

#     ssl_conn.close()
#     cursor.close()
#     db_conn.close()
#     print(f"[DISCONNECTED] Client {client_id} closed.")

# # -------------------------------
# # Approval Manager (runs in main thread)
# # -------------------------------
# def approval_manager():
#     """Handles queued approvals in the main thread"""
#     while True:
#         try:
#             client_id, query, ssl_conn, db_conn, cursor, category = approval_queue.get(timeout=1)
#             print(f"\n[APPROVAL REQUIRED] Client {client_id} requested:\n{query}")
#             decision = input("Approve query? (yes/no): ").strip().lower()
#             approved = decision == "yes"

#             response = ""
#             if approved:
#                 try:
#                     cursor.execute(query)
#                     db_conn.commit()
#                     response = "Approved and executed."
#                 except Exception as e:
#                     response = f"Execution failed: {e}"
#             else:
#                 response = "Rejected by DBA."

#             exec_time = 0.0
#             analysis = safe_analyze(query)
#             log_activity(client_id, query, category.upper(), exec_time, response, analysis)
#             send_safe_json(ssl_conn, query, response, analysis)
#             approval_queue.task_done()
#         except queue.Empty:
#             continue
#         except Exception as e:
#             print(f"[APPROVAL ERROR] {e}")

# # -------------------------------
# # Start Server
# # -------------------------------
# if __name__ == "__main__":
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.bind((HOST, PORT))
#     s.listen(5)
#     print("[SERVER STARTED] Listening on port", PORT)

#     # Start a background thread for handling approvals in main thread context
#     threading.Thread(target=approval_manager, daemon=True).start()

#     while True:
#         try:
#             conn_socket, addr = s.accept()
#             threading.Thread(target=handle_client, args=(conn_socket, addr), daemon=True).start()
#         except KeyboardInterrupt:
#             print("\n[SERVER STOPPED] Exiting gracefully.")
#             break
#         except Exception as e:
#             print(f"[SERVER ERROR] {e}")


import socket
import ssl
import threading
import queue
import mysql.connector
import time
import json
from logs.query_cache import lookup_cached_query
from monitor.activity_logger import log_activity
from monitor.slow_query_analyzer import analyze_root_causes

# -------------------------------
# Database config
# -------------------------------
DB_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "rootpassword",
    "database": "mydb"
}

# -------------------------------
# SSL setup
# -------------------------------
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="server.crt", keyfile="server.key")

HOST = "127.0.0.1"
PORT = 5050
sensitive_columns = ["salary", "ssn", "password"]

# Approval queue
approval_queue = queue.Queue()


# -------------------------------
# Query helpers
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
    if "*" in query:
        return True
    for col in sensitive_columns:
        if col in query.lower():
            return True
    return False


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
    except:
        return query

    cols = get_table_columns(table, cursor)
    allowed = [c for c in cols if c not in sensitive_columns]

    if client_id == "99":  # outsider restricted
        allowed = allowed[:2]

    return f"SELECT {', '.join(allowed)} FROM {table}"


# -------------------------------
# Model-safe analyzer
# -------------------------------
def safe_analyze(query):
    try:
        result = analyze_root_causes(query)
        return {
            "status": result.get("status", "Normal"),
            "root_cause": result.get("root_cause", "None"),
            "score": result.get("score", 0.0)
        }
    except Exception as e:
        print(f"[RANKING ERROR] {e}")
        return {"status": "Unknown", "root_cause": "N/A", "score": 0.0}


def send_safe_json(ssl_conn, query, response, analysis):
    payload = {
        "query": query,
        "response": response,
        "status": analysis["status"],
        "root_cause": analysis["root_cause"],
        "score": analysis["score"],
    }
    try:
        ssl_conn.send(json.dumps(payload).encode())
    except Exception as e:
        print(f"[SEND ERROR] {e}")


# -------------------------------
# Client handler
# -------------------------------
# def handle_client(conn_socket, addr):
#     print(f"[CONNECTED] {addr}")

#     # NO TIMEOUT — permanent connection
#     conn_socket.settimeout(None)

#     # Enable TCP KeepAlive to prevent SSL EOF
#     conn_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
#     conn_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
#     conn_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 30)
#     conn_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 10)

#     try:
#         ssl_conn = context.wrap_socket(conn_socket, server_side=True)
#     except ssl.SSLError as e:
#         print(f"[SSL ERROR during handshake] {e}")
#         conn_socket.close()
#         return

#     try:
#         client_id = ssl_conn.recv(1024).decode().strip()
#     except:
#         ssl_conn.close()
#         return

#     # MySQL connection
#     try:
#         db_conn = mysql.connector.connect(**DB_CONFIG)
#         cursor = db_conn.cursor(buffered=True)
#     except:
#         ssl_conn.send("Database connection failed.".encode())
#         ssl_conn.close()
#         return

#     # Insider/outsider access
#     if client_id not in ["1", "2", "3"]:
#         print(f"\n[OUTSIDER] {addr} ({client_id}) requesting access.")
#         if input("Allow outsider? (yes/no): ").strip().lower() != "yes":
#             ssl_conn.send("Access denied.".encode())
#             ssl_conn.close()
#             return
#         ssl_conn.send("Access granted.".encode())
#     else:
#         ssl_conn.send(f"Welcome Client {client_id}, access granted.".encode())

#     while True:
#         try:
#             query_data = ssl_conn.recv(8192)
#             if not query_data:
#                 break

#             query = query_data.decode().strip()
#             start = time.time()

#             # -------------------------------
#             # 1. CACHE FIRST
#             # -------------------------------
#             cached = lookup_cached_query(query)
#             if cached:
#                 analysis = {
#                     "status": cached.get("status", "Normal"),
#                     "root_cause": cached.get("root_cause", "None"),
#                     "score": cached.get("score", 0.0)
#                 }
#                 query_type = query.strip().split()[0].upper()
#                 log_activity(client_id, query, query_type, 0.0, response, analysis)
#                 send_safe_json(ssl_conn, query, "Approved and executed.", analysis)
#                 continue

#             # -------------------------------
#             # 2. APPROVAL LOGIC
#             # -------------------------------
#             category = classify_query(query)

#             if category == "needs-approval" or (category == "select" and needs_sensitive_approval(client_id, query)):
#                 approval_queue.put((client_id, query, ssl_conn, db_conn, cursor, category))
#                 print(f"[QUEUE] Approval required for {client_id}: {query}")
#                 continue

#             # -------------------------------
#             # 3. EXECUTE QUERY
#             # -------------------------------
#             if category in ["safe", "alert-only"]:
#                 if category == "alert-only":
#                     print(f"[ALERT] {client_id}: {query}")
#                 cursor.execute(query)
#                 db_conn.commit()
#                 response = "Query executed."

#             elif category == "select":
#                 modified = enforce_column_level(client_id, query, cursor)
#                 cursor.execute(modified)
#                 rows = cursor.fetchall()
#                 if rows:
#                     response = "\n".join([str(r) for r in rows])

#                     # ⭐ Print result to console exactly like CSV
#                     print("\n[RESULT]", query)
#                     for r in rows:
#                         print(str(r))
#                     print("-" * 80)

#                 else:
#                     response = "No rows returned."
#                     print(f"[RESULT] No rows returned for query: {query}")


#             exec_time = time.time() - start

#             # -------------------------------
#             # 4. ANALYZE WITH MODEL
#             # -------------------------------
#             analysis = safe_analyze(query)

#             # -------------------------------
#             # 5. LOG + RESPOND
#             # -------------------------------
#             log_activity(client_id, query, category.upper(), exec_time, response, analysis)
#             send_safe_json(ssl_conn, query, response, analysis)

#         except Exception as e:
#             print(f"[CLIENT ERROR] {e}")
#             break

def handle_client(conn_socket, addr):
    print(f"[CONNECTED] {addr}")

    # Disable timeout
    conn_socket.settimeout(None)

    # KeepAlive
    conn_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    conn_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
    conn_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 30)
    conn_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 10)

    # SSL handshake
    try:
        ssl_conn = context.wrap_socket(conn_socket, server_side=True)
    except ssl.SSLError as e:
        print(f"[SSL ERROR] {e}")
        conn_socket.close()
        return

    # Read client_id
    try:
        client_id = ssl_conn.recv(1024).decode().strip()
    except:
        ssl_conn.close()
        return

    # DB connection
    try:
        db_conn = mysql.connector.connect(**DB_CONFIG)
        cursor = db_conn.cursor(buffered=True)
    except:
        ssl_conn.send("Database connection failed.".encode())
        ssl_conn.close()
        return

    # Insider / outsider
    if client_id not in ["1", "2", "3"]:
        print(f"\n[OUTSIDER] {addr} ({client_id}) requesting access.")
        if input("Allow outsider? (yes/no): ").strip().lower() != "yes":
            ssl_conn.send("Access denied.".encode())
            ssl_conn.close()
            return
        ssl_conn.send("Access granted.".encode())
    else:
        ssl_conn.send(f"Welcome Client {client_id}, access granted.".encode())

    # ============================================================
    # MAIN LOOP
    # ============================================================
    while True:
        try:
            query_data = ssl_conn.recv(8192)
            if not query_data:
                break

            query = query_data.decode().strip()
            start = time.time()

            print(f"\n[QUERY RECEIVED] {client_id}: {query}")

            # =======================================================
            # 1) CACHE FIRST — only ML analysis comes from cache
            #    SQL must still be EXECUTED to show live result
            # =======================================================
            # cached = lookup_cached_query(query)
            # if cached:
            #     print("[CACHE HIT] Using cached ML analysis, but executing SQL again.")

            #     analysis = {
            #         "status": cached.get("status", "Normal"),
            #         "root_cause": cached.get("root_cause", "None"),
            #         "score": cached.get("score", 0.0)
            #     }
            #     parts = query.strip().split()
            #     query_type = parts[0].upper() if parts else "UNKNOWN"
            #     # ---------------------------------------------------
            #     # Execute SQL (fresh result)
            #     # ---------------------------------------------------
            #     try:
            #         cursor.execute(query)
            #         rows = cursor.fetchall()
            #         if rows:
            #             fresh_result = "\n".join([str(r) for r in rows])
            #         else:
            #             fresh_result = "No rows returned."

            #         # Print fresh SELECT result to console
            #         print("\n[RESULT - CACHED SELECT EXECUTED]")
            #         for r in rows:
            #             print(str(r))
            #         print("-" * 80)

            #     except Exception as e:
            #         fresh_result = f"Error executing cached query: {e}"
            #         print(f"[CACHED QUERY SQL ERROR] {e}")

            #     # ---------------------------------------------------
            #     # Log + Send to client
            #     # ---------------------------------------------------
            #     log_activity(client_id, query, query_type, 0.0, fresh_result, analysis)
            #     send_safe_json(ssl_conn, query, fresh_result, analysis)
            #     continue
            # =======================================================
# 1) CACHE FIRST — execute SQL fresh + return cached ML
# =======================================================
            cached = lookup_cached_query(query)
            if cached:
                print("[CACHE HIT] Using cached ML analysis, executing SQL for fresh result.")

                # Cached ML analysis (NO model call)
                analysis = {
                    "status": cached.get("status", "Normal"),
                    "root_cause": cached.get("root_cause", "None"),
                    "score": float(cached.get("score", 0.0))
                }

                # Extract SQL verb
                parts = query.strip().split()
                query_type = parts[0].upper() if parts else "UNKNOWN"

                # -----------------------------------------
                # (A) EXECUTE SQL FRESH (every cached query)
                # -----------------------------------------
                try:
                    if query_type == "SELECT":
                        cursor.execute(query)
                        rows = cursor.fetchall()

                        if rows:
                            fresh_result = "\n".join([str(r) for r in rows])
                        else:
                            fresh_result = "Executed"

                        print("\n[FRESH RESULT - SELECT]")
                        for r in rows:
                            print(str(r))
                        print("-" * 80)

                    else:
                        cursor.execute(query)
                        db_conn.commit()
                        fresh_result = "Approved and executed."

                        print("\n[FRESH RESULT - NON-SELECT]")
                        print(fresh_result)
                        print("-" * 80)

                except Exception as e:
                    fresh_result = f"SQL Execution Error: {e}"
                    print(f"[ERROR] {e}")

                # -----------------------------------------
                # (B) LOG activity
                # -----------------------------------------
                log_activity(
                    client_id,
                    query,
                    query_type,
                    2.0,                 # ML time = 0 since cached
                    fresh_result,
                    analysis
                )

                # -----------------------------------------
                # (C) Send fresh result + cached ML
                # -----------------------------------------
                send_safe_json(ssl_conn, query, fresh_result, analysis)
                continue


            # =======================================================
            # 2) APPROVAL SYSTEM
            # =======================================================
            category = classify_query(query)

            if category == "needs-approval" or (category == "select" and needs_sensitive_approval(client_id, query)):
                approval_queue.put((client_id, query, ssl_conn, db_conn, cursor, category))
                print(f"[QUEUE] Approval required for {client_id}: {query}")
                continue

            # =======================================================
            # 3) EXECUTE SQL
            # =======================================================
            if category in ["safe", "alert-only"]:
                if category == "alert-only":
                    print(f"[ALERT] {client_id}: {query}")

                try:
                    cursor.execute(query)
                    db_conn.commit()
                    response = "Approved and executed."
                except Exception as e:
                    response = f"Error executing query: {e}"

                print("\n[RESULT - NON-SELECT]")
                print(response)
                print("-" * 80)

            elif category == "select":
                modified = enforce_column_level(client_id, query, cursor)

                try:
                    cursor.execute(modified)
                    rows = cursor.fetchall()

                    if rows:
                        response = "\n".join([str(r) for r in rows])
                        print("\n[RESULT - SELECT]")
                        for r in rows:
                            print(str(r))
                        print("-" * 80)
                    else:
                        response = "No rows returned."
                        print(f"[RESULT] No rows returned for: {query}")

                except Exception as e:
                    response = f"Error executing select: {e}"
                    print(f"[SELECT ERROR] {e}")

            exec_time = time.time() - start

            # =======================================================
            # 4) RUN ML ANALYSIS
            # =======================================================
            analysis = safe_analyze(query)

            # =======================================================
            # 5) LOG + SEND JSON
            # =======================================================
            log_activity(client_id, query, category.upper(), exec_time, response, analysis)
            send_safe_json(ssl_conn, query, response, analysis)

        except Exception as e:
            print(f"[CLIENT ERROR] {e}")
            break

    ssl_conn.close()
    cursor.close()
    db_conn.close()
    print(f"[DISCONNECTED] Client {client_id} closed.")


# -------------------------------
# Approval manager
# -------------------------------
def approval_manager():
    while True:
        try:
            client_id, query, ssl_conn, db_conn, cursor, category = approval_queue.get()
            print(f"\n[APPROVAL REQUIRED] {client_id}: {query}")
            approved = input("Approve? (yes/no): ").strip().lower() == "yes"

            if approved:
                try:
                    cursor.execute(query)
                    db_conn.commit()
                    response = "Approved and executed."
                except Exception as e:
                    response = f"Execution failed: {e}"
            else:
                response = "Rejected by DBA."

            analysis = safe_analyze(query)
            log_activity(client_id, query, category.upper(), 0.0, response, analysis)
            send_safe_json(ssl_conn, query, response, analysis)

        except Exception as e:
            print(f"[APPROVAL ERROR] {e}")


# -------------------------------
# Start server
# -------------------------------
if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Global keepalive
    s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    s.bind((HOST, PORT))
    s.listen(5)
    print("[SERVER STARTED] Listening on port", PORT)

    threading.Thread(target=approval_manager, daemon=True).start()

    while True:
        conn_socket, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn_socket, addr), daemon=True).start()
