# gui/app.py
#1.Run python app.py in /backend
#2.npm start
from flask import Flask, jsonify, send_file
import pandas as pd
import os
import json
from flask_cors import CORS
from routes.clientProxy import client_bp
from monitor.slow_query_analyzer import analyze_root_causes

app = Flask(__name__)
CORS(app)
BASE_DIR = os.path.abspath(os.getcwd())
LOG_FILE_PATH = os.path.join(BASE_DIR, "logs", "activity_log.csv")

# LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'logs', 'activity_log.csv')
CONNECTED_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'connected_clients.json')

@app.route('/api/dashboard')
def dashboard():
    if not os.path.exists(LOG_FILE_PATH):
        return jsonify({"error": "Log file not found."}), 404

    try:
        df = pd.read_csv(LOG_FILE_PATH, dtype=str)

        if 'Result' not in df.columns:
            df['Result'] = ""

        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
            df = df.dropna(subset=['Timestamp'])
        else:
            df['Timestamp'] = pd.to_datetime('now')

        if 'ExecutionTime' in df.columns:
            df['ExecutionTime'] = pd.to_numeric(df['ExecutionTime'], errors='coerce').fillna(0)
        else:
            df['ExecutionTime'] = 0

        if 'SlowQuery' in df.columns:
            df['SlowQuery'] = df['SlowQuery'].astype(str).str.lower().isin(['true','1','yes'])
        else:
            df['SlowQuery'] = False

        total_unique_clients = int(df['ClientID'].nunique())
        
        # Convert client_counts to have string keys and int values, sorted by client ID
        client_counts_raw = df['ClientID'].value_counts().to_dict()
        client_counts = {str(k): int(v) for k, v in sorted(client_counts_raw.items(), key=lambda x: str(x[0]))}

        slow_counts = {
            'Slow': int(df['SlowQuery'].sum()),
            'Fast': int((~df['SlowQuery']).sum())
        }

        df_temp = df.copy()
        df_temp.set_index('Timestamp', inplace=True)
        five_min_counts_series = df_temp['Query'].resample('5min').count().sort_index()
        five_min_counts = {
            timestamp.strftime('%Y-%m-%d %H:%M'): int(count)
            for timestamp, count in five_min_counts_series.items()
        }

        # Calculate active clients (clients with queries in last 10 minutes)
        now = pd.Timestamp.now()
        ten_min_ago = now - pd.Timedelta(minutes=10)
        recent_clients = df[df['Timestamp'] >= ten_min_ago]['ClientID'].nunique()

        connected_clients = []
        if os.path.exists(CONNECTED_FILE):
            with open(CONNECTED_FILE, 'r', encoding='utf-8') as f:
                try:
                    connected_clients = json.load(f)
                except:
                    connected_clients = []

        print(f"[API /dashboard] Client counts: {client_counts}")
        print(f"[API /dashboard] Active clients (last 10 min): {recent_clients}")
        print(f"[API /dashboard] Currently connected: {len(connected_clients)}")
        print(f"[API /dashboard] Total unique clients: {total_unique_clients}")

        return jsonify({
            "total_clients": total_unique_clients,
            "current_connected": len(connected_clients),  # Only show actually connected clients
            "active_clients_10min": int(recent_clients),  # Keep this for reference
            "connected_clients": connected_clients,
            "client_counts": client_counts,
            "slow_counts": slow_counts,
            "five_min_counts": five_min_counts
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route('/api/client/<client_id>')
# def client_details(client_id):
#     if not os.path.exists(LOG_FILE_PATH):
#         return jsonify({"error": "Log file not found."}), 404

#     try:
#         df = pd.read_csv(LOG_FILE_PATH, dtype=str)
#         if 'Result' not in df.columns:
#             df['Result'] = ""

#         if 'Timestamp' in df.columns:
#             df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
#             df = df.dropna(subset=['Timestamp'])
#         else:
#             df['Timestamp'] = pd.to_datetime('now')

#         if 'SlowQuery' in df.columns:
#             df['SlowQuery'] = df['SlowQuery'].astype(str).str.lower().isin(['true','1','yes'])
#         else:
#             df['SlowQuery'] = False

#         df_client = df[df['ClientID'].astype(str) == str(client_id)].sort_values(by='Timestamp', ascending=False)

#         if df_client.empty:
#             return jsonify({"error": f"No data for client {client_id}"}), 404

#         total_queries = len(df_client)
#         slow_queries = int(df_client['SlowQuery'].sum())

#         change_mask = ~df_client['Query'].str.lower().str.strip().str.startswith(('select','show','desc','describe'))
#         change_count = int(change_mask.sum())
#         view_count = int((~change_mask).sum())

#         records = []
#         for _, row in df_client.iterrows():
#             records.append({
#                 'Timestamp': row.get('Timestamp').strftime('%Y-%m-%d %H:%M:%S') if not pd.isnull(row.get('Timestamp')) else '',
#                 'Query': row.get('Query', ''),
#                 'Result': row.get('Result', '')
#             })

#         return jsonify({
#             "client_id": client_id,
#             "total_queries": total_queries,
#             "slow_queries": slow_queries,
#             "change_count": change_count,
#             "view_count": view_count,
#             "queries": records
#         })
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
# @app.route('/api/client/<client_id>')
# def client_details(client_id):
#     if not os.path.exists(LOG_FILE_PATH):
#         return jsonify({"error": "Log file not found."}), 404

#     try:
#         df = pd.read_csv(LOG_FILE_PATH, dtype=str)
#         if 'Result' not in df.columns:
#             df['Result'] = ""

#         if 'Timestamp' in df.columns:
#             df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
#             df = df.dropna(subset=['Timestamp'])
#         else:
#             df['Timestamp'] = pd.to_datetime('now')

#         if 'SlowQuery' in df.columns:
#             df['SlowQuery'] = df['SlowQuery'].astype(str).str.lower().isin(['true','1','yes'])
#         else:
#             df['SlowQuery'] = False

#         df_client = df[df['ClientID'].astype(str) == str(client_id)].sort_values(by='Timestamp', ascending=False)

#         if df_client.empty:
#             return jsonify({"error": f"No data for client {client_id}"}), 404

#         total_queries = len(df_client)
#         slow_queries = int(df_client['SlowQuery'].sum())

#         change_mask = ~df_client['Query'].str.lower().str.strip().str.startswith(('select','show','desc','describe'))
#         change_count = int(change_mask.sum())
#         view_count = int((~change_mask).sum())

#         records = []
#         for _, row in df_client.iterrows():
#             query_text = row.get('Query', '')
#             # 🔹 Added ML root cause ranking
#             ranking = analyze_root_causes(query_text)  # returns list of causes with scores

#             records.append({
#                 'Timestamp': row.get('Timestamp').strftime('%Y-%m-%d %H:%M:%S') if not pd.isnull(row.get('Timestamp')) else '',
#                 'Query': query_text,
#                 'Result': row.get('Result', ''),
#                 'Ranking': ranking  # <-- new field added
#             })

#         return jsonify({
#             "client_id": client_id,
#             "total_queries": total_queries,
#             "slow_queries": slow_queries,
#             "change_count": change_count,
#             "view_count": view_count,
#             "queries": records
#         })
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# @app.route('/api/client/<client_id>')
# def client_details(client_id):
#     if not os.path.exists(LOG_FILE_PATH):
#         return jsonify({"error": "Log file not found."}), 404

#     try:
#         df = pd.read_csv(LOG_FILE_PATH, dtype=str)

#         # Ensure required columns exist
#         if 'Result' not in df.columns:
#             df['Result'] = ""

#         # Parse and clean timestamp
#         if 'Timestamp' in df.columns:
#             df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
#             df = df.dropna(subset=['Timestamp'])
#         else:
#             df['Timestamp'] = pd.to_datetime('now')

#         # Normalize slow query column
#         if 'SlowQuery' in df.columns:
#             df['SlowQuery'] = df['SlowQuery'].astype(str).str.lower().isin(['true', '1', 'yes'])
#         else:
#             df['SlowQuery'] = False

#         # Filter this client's data
#         df_client = df[df['ClientID'].astype(str) == str(client_id)].sort_values(by='Timestamp', ascending=False)
#         if df_client.empty:
#             return jsonify({"error": f"No data for client {client_id}"}), 404

#         # Metrics
#         total_queries = len(df_client)
#         slow_queries = int(df_client['SlowQuery'].sum())

#         # Identify data-changing vs view-only queries
#         change_mask = ~df_client['Query'].str.lower().str.strip().str.startswith(('select', 'show', 'desc', 'describe'))
#         change_count = int(change_mask.sum())
#         view_count = int((~change_mask).sum())

#         # Query-level analysis
#         records = []
#         alerts = []

#         for _, row in df_client.iterrows():
#             query_text = row.get('Query', '')
            
#             # 🔹 Use stored analysis from CSV instead of re-analyzing
#             ranking_data = row.get('Ranking', '')
            
#             # Try to parse the stored JSON ranking data
#             if ranking_data and isinstance(ranking_data, str):
#                 try:
#                     stored_analysis = json.loads(ranking_data)
#                     status = stored_analysis.get("status", "Normal")
#                     root_cause = stored_analysis.get("root_cause", "None")
#                     score = stored_analysis.get("score", 0.0)
                    
#                     # Format for frontend
#                     causes = [{"cause": root_cause, "score": score}] if root_cause != "None" else []
                    
#                     # Generate alert message
#                     if status == "Slow":
#                         alert = f"🚨 Slow query detected (score: {score:.4f})"
#                     elif status == "Near Slow":
#                         alert = f"⚠️ Query nearing slowness threshold (score: {score:.4f})"
#                     else:
#                         alert = ""
                        
#                 except (json.JSONDecodeError, Exception) as e:
#                     print(f"[RANKING PARSE ERROR] {e}")
#                     # Fallback to re-analysis if parsing fails
#                     analysis = analyze_root_causes(query_text)
#                     status = analysis.get("status", "Normal")
#                     root_cause = analysis.get("root_cause", "None")
#                     score = analysis.get("score", 0.0)
#                     causes = [{"cause": root_cause, "score": score}] if root_cause != "None" else []
#                     alert = ""
#             else:
#                 # No ranking data stored, re-analyze
#                 analysis = analyze_root_causes(query_text)
#                 status = analysis.get("status", "Normal")
#                 root_cause = analysis.get("root_cause", "None")
#                 score = analysis.get("score", 0.0)
#                 causes = [{"cause": root_cause, "score": score}] if root_cause != "None" else []
#                 alert = ""

#             # Collect alerts (only if meaningful)
#             if status in ["Slow", "Near Slow"] and alert:
#                 alerts.append(alert)

#             # records.append({
#             #     "Timestamp": row.get('Timestamp').strftime('%Y-%m-%d %H:%M:%S') if not pd.isnull(row.get('Timestamp')) else '',
#             #     "Query": query_text,
#             #     "Result": row.get('Result', ''),
#             #     "Status": status,
#             #     "Score": score,
#             #     "RootCauses": causes,   # list of {"cause":..., "score":...}
#             #     "Alert": alert
#             # })
#             records.append({
#                 "Timestamp": row.get('Timestamp').strftime('%Y-%m-%d %H:%M:%S') if not pd.isnull(row.get('Timestamp')) else '',
#                 "Query": query_text,
#                 "Result": row.get('Result', ''),
#                 "Status": status,
#                 "Score": score,
#                 "RootCauses": causes if isinstance(causes, list) else [],
#                 "Alert": alert
#             })

#         # Prepare final structured response
#         response = {
#             "client_id": client_id,
#             "total_queries": total_queries,
#             "slow_queries": slow_queries,
#             "change_count": change_count,
#             "view_count": view_count,
#             "queries": records,
#             "alerts": list(set(alerts))  # unique alerts
#         }

#         return jsonify(response)

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app.route('/api/client/<client_id>')
def client_details(client_id):
    if not os.path.exists(LOG_FILE_PATH):
        return jsonify({"error": "Log file not found."}), 404

    try:
        df = pd.read_csv(LOG_FILE_PATH, dtype=str)

        # Ensure required columns exist
        if 'Result' not in df.columns:
            df['Result'] = ""

        # Parse and clean timestamp
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
            df = df.dropna(subset=['Timestamp'])
        else:
            df['Timestamp'] = pd.to_datetime('now')

        # Normalize slow query column
        if 'SlowQuery' in df.columns:
            df['SlowQuery'] = df['SlowQuery'].astype(str).str.lower().isin(['true', '1', 'yes'])
        else:
            df['SlowQuery'] = False

        # Filter this client's data
        df_client = df[df['ClientID'].astype(str) == str(client_id)].sort_values(by='Timestamp', ascending=False)
        if df_client.empty:
            return jsonify({"error": f"No data for client {client_id}"}), 404

        # Metrics
        total_queries = len(df_client)
        slow_queries = int(df_client['SlowQuery'].sum())

        # Identify data-changing vs view-only queries
        change_mask = ~df_client['Query'].str.lower().str.strip().str.startswith(
            ('select', 'show', 'desc', 'describe')
        )
        change_count = int(change_mask.sum())
        view_count = int((~change_mask).sum())

        # Query-level analysis
        records = []
        alerts = []

        for _, row in df_client.iterrows():
            query_text = row.get('Query', '')

            # 🔹 Use stored analysis from CSV instead of re-analyzing
            ranking_data = row.get('Ranking', '')

            # Try to parse the stored JSON ranking data
            if ranking_data and isinstance(ranking_data, str):
                try:
                    stored_analysis = json.loads(ranking_data)
                    status = stored_analysis.get("status", "Normal")
                    root_cause = stored_analysis.get("root_cause", "None")
                    score = stored_analysis.get("score", 0.0)

                    # Format for frontend
                    causes = [{"cause": root_cause, "score": score}] if root_cause != "None" else []

                    # Generate alert message
                    if status == "Slow":
                        alert = f"🚨 Slow query detected (score: {score:.4f})"
                    elif status == "Near Slow":
                        alert = f"⚠️ Query nearing slowness threshold (score: {score:.4f})"
                    else:
                        alert = ""

                except (json.JSONDecodeError, Exception) as e:
                    print(f"[RANKING PARSE ERROR] {e}")

                    # Fallback to re-analysis if parsing fails
                    analysis = analyze_root_causes(query_text)
                    status = analysis.get("status", "Normal")
                    root_cause = analysis.get("root_cause", "None")
                    score = analysis.get("score", 0.0)
                    causes = [{"cause": root_cause, "score": score}] if root_cause != "None" else []
                    alert = ""

            else:
                # No ranking data stored, re-analyze
                analysis = analyze_root_causes(query_text)
                status = analysis.get("status", "Normal")
                root_cause = analysis.get("root_cause", "None")
                score = analysis.get("score", 0.0)
                causes = [{"cause": root_cause, "score": score}] if root_cause != "None" else []
                alert = ""

            # Collect alerts (only if meaningful)
            if status in ["Slow", "Near Slow"] and alert:
                alerts.append(alert)

            # --------------------------------------------------
            #   🔥🔥 NORMALIZATION BLOCK YOU REQUESTED 🔥🔥
            # --------------------------------------------------

            # Normalize score
            try:
                score_val = float(score) if score is not None and str(score) != "" else 0.0
            except:
                score_val = 0.0

            # Ensure causes is always a list
            if not isinstance(causes, list):
                causes = []

            # Causes cleanup
            normalized_causes = []
            for c in causes:
                if not isinstance(c, dict):
                    continue
                normalized_causes.append({
                    "cause": c.get("cause") or c.get("name") or "unknown",
                    "score": float(c.get("score")) if c.get("score") not in [None, "", "None"] else 0.0
                })

            # Add record safely
            records.append({
                "Timestamp": row.get('Timestamp').strftime('%Y-%m-%d %H:%M:%S')
                if not pd.isnull(row.get('Timestamp')) else '',

                "Query": query_text,
                "Result": row.get('Result', '') if row.get('Result') is not None else '',
                "Status": status or "Normal",
                "Score": score_val,
                "RootCauses": normalized_causes,
                "Alert": alert or ""
            })

        # Prepare final structured response
        response = {
            "client_id": client_id,
            "total_queries": total_queries,
            "slow_queries": slow_queries,
            "change_count": change_count,
            "view_count": view_count,
            "queries": records,
            "alerts": list(set(alerts))  # unique alerts
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/logs')
def logs():
    if not os.path.exists(LOG_FILE_PATH):
        return jsonify({"error": "Log file not found."}), 404

    try:
        # Read CSV with proper handling of multiline fields
        df = pd.read_csv(LOG_FILE_PATH, dtype=str, quoting=1)  # quoting=1 is csv.QUOTE_ALL
        if 'Result' not in df.columns:
            df['Result'] = ""
        
        # Clean up any NaN values
        df = df.fillna("")
        
        # Convert to records and return
        records = df.to_dict(orient='records')
        print(f"[API /logs] Returning {len(records)} log records")
        return jsonify(records)
    except Exception as e:
        print(f"[API /logs] Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/download')
def download():
    if not os.path.exists(LOG_FILE_PATH):
        return jsonify({"error": "Log file not found."}), 404
    return send_file(LOG_FILE_PATH, as_attachment=True)

app.register_blueprint(client_bp, url_prefix="/api")
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
