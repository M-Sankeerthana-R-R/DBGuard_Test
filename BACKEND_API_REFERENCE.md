# Backend API Reference for DB Guard Frontend

## Overview

This document outlines the API endpoints that the frontend expects from the backend. The backend should return data in the formats specified below for the UI to work correctly.

## API Endpoints

### 1. Dashboard Metrics

**Endpoint**: `GET /api/dashboard`

**Expected Response**:

```json
{
  "client_counts": {
    "1": 10,
    "2": 5,
    "3": 15
  },
  "timeline": [
    {
      "timestamp": "16:28:30",
      "client": "1",
      "slow": false
    },
    {
      "timestamp": "16:29:15",
      "client": "1",
      "slow": true
    }
  ],
  "alerts": [
    {
      "timestamp": "16:30:00",
      "client": "1",
      "message": "Highly slow query detected"
    }
  ],
  "total_queries": 1,
  "slow_queries": 0,
  "avg_execution_time": 298.33,
  "active_clients": 1
}
```

**Used In**: DBA Dashboard
**Purpose**: Provides metrics, charts data, and alerts for the main dashboard

---

### 2. Activity Logs

**Endpoint**: `GET /api/logs`

**Expected Response**:

```json
[
  {
    "Timestamp": "2025-01-03 16:28:30",
    "ClientID": "1",
    "QueryType": "SELECT",
    "Query": "select * from test;",
    "ExecutionTime": "298.33ms",
    "SlowQuery": false,
    "Result": "44606 rows",
    "Ranking": "[{\"cause\":\"Missing indexes\",\"score\":0.95}]"
  }
]
```

**Used In**: DBA Dashboard
**Purpose**: Displays all query activity in a table format

---

### 3. All Queries

**Endpoint**: `GET /api/all_queries`

**Expected Response**:

```json
[
  {
    "Query": "select * from test;",
    "QueryType": "SELECT",
    "ExecutionTime": "298.33ms",
    "SlowQuery": false,
    "Result": "44606 rows"
  }
]
```

**Used In**: DBA Dashboard (All Queries section)
**Purpose**: Shows preview of recent queries from all clients

---

### 4. Client Connection

**Endpoint**: `POST /api/connect`

**Request Body**:

```json
{
  "clientId": "1"
}
```

**Expected Response**:

```json
{
  "status": "connected",
  "message": "Successfully connected to database"
}
```

**Used In**: Client Dashboard
**Purpose**: Establishes connection between client and server

---

### 5. Execute Query

**Endpoint**: `POST /api/execute_query`

**Request Body**:

```json
{
  "clientId": "1",
  "query": "SELECT * FROM users;"
}
```

**Expected Response**:

```json
{
  "response": "Query executed successfully",
  "status": "SUCCESS",
  "execution_time": "298.33ms",
  "rows_affected": "44606",
  "ranking": [
    {
      "cause": "Missing indexes",
      "score": 0.95
    },
    {
      "cause": "Full table scan",
      "score": 0.87
    }
  ],
  "alert": "Highly slow query detected! Consider optimization."
}
```

**Used In**: Client Dashboard
**Purpose**: Executes SQL query and returns results with analysis

**Note**:

- `ranking` should only be included for slow queries
- `alert` is optional and shown as a warning banner
- `status` can be: "SUCCESS", "SLOW", "NEAR SLOW", "ERROR"

---

### 6. Client Details

**Endpoint**: `GET /api/client/:clientId`

**Expected Response**:

```json
{
  "total_queries": 1,
  "slow_queries": 0,
  "change_count": 0,
  "view_count": 1,
  "queries": [
    {
      "Timestamp": "2025-01-03 16:28:30",
      "Query": "select * from test;",
      "Result": "44606 rows",
      "Status": "SUCCESS",
      "Score": 0.298,
      "RootCauses": [
        {
          "cause": "Missing indexes",
          "score": 0.95
        }
      ],
      "Alert": ""
    }
  ]
}
```

**Used In**: Client Details Page
**Purpose**: Shows detailed information for a specific client

---

## Data Type Specifications

### Status Values

- `"SUCCESS"` - Query executed successfully (< 500ms)
- `"SLOW"` - Slow query (> 500ms)
- `"NEAR SLOW"` - Near slow threshold (400-500ms)
- `"ERROR"` - Query execution failed

### Query Types

Common query types to track:

- `"SELECT"`
- `"INSERT"`
- `"UPDATE"`
- `"DELETE"`
- `"CREATE"`
- `"DROP"`
- `"ALTER"`

### Root Cause Categories

Suggested root causes for slow queries:

- "Missing indexes"
- "Full table scan"
- "Inefficient join"
- "Large dataset"
- "No WHERE clause"
- "Suboptimal query structure"
- "Network latency"
- "Lock contention"

---

## CORS Configuration

The backend should allow CORS requests from the frontend origin:

```python
# Flask example
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
```

---

## Error Handling

All endpoints should return errors in this format:

```json
{
  "error": "Error message here",
  "status": "error"
}
```

Example error responses:

### Connection Failed

```json
{
  "status": "error",
  "message": "Unable to connect to database"
}
```

### Query Execution Failed

```json
{
  "status": "ERROR",
  "response": "Syntax error in SQL query",
  "error": "Invalid SQL syntax near 'SELCT'"
}
```

---

## Optional Enhancements

### Real-time Updates

Consider implementing WebSocket for real-time updates:

- Alert notifications
- Live query execution updates
- Client connection/disconnection events

### Query Caching

For better performance:

- Cache dashboard metrics (update every 5-10 seconds)
- Cache client statistics
- Invalidate cache on new queries

### Pagination

For large datasets:

```json
{
  "data": [...],
  "page": 1,
  "per_page": 10,
  "total": 100
}
```

---

## Testing the API

You can test the API endpoints using curl:

```bash
# Test dashboard endpoint
curl http://localhost:5000/api/dashboard

# Test client connection
curl -X POST http://localhost:5000/api/connect \
  -H "Content-Type: application/json" \
  -d '{"clientId": "1"}'

# Test query execution
curl -X POST http://localhost:5000/api/execute_query \
  -H "Content-Type: application/json" \
  -d '{"clientId": "1", "query": "SELECT * FROM users;"}'

# Test logs
curl http://localhost:5000/api/logs

# Test client details
curl http://localhost:5000/api/client/1
```

---

## Sample Backend Implementation (Flask)

```python
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    return jsonify({
        "client_counts": {"1": 10, "2": 5},
        "timeline": [],
        "alerts": [],
        "total_queries": 15,
        "slow_queries": 2,
        "avg_execution_time": 298.33,
        "active_clients": 2
    })

@app.route('/api/connect', methods=['POST'])
def connect():
    data = request.json
    client_id = data.get('clientId')

    # Your connection logic here

    return jsonify({
        "status": "connected",
        "message": f"Client {client_id} connected successfully"
    })

@app.route('/api/execute_query', methods=['POST'])
def execute_query():
    data = request.json
    client_id = data.get('clientId')
    query = data.get('query')

    # Your query execution logic here

    return jsonify({
        "response": "Query executed successfully",
        "status": "SUCCESS",
        "execution_time": "298.33ms",
        "rows_affected": "100"
    })

@app.route('/api/logs', methods=['GET'])
def logs():
    # Your logs logic here
    return jsonify([])

@app.route('/api/all_queries', methods=['GET'])
def all_queries():
    # Your queries logic here
    return jsonify([])

@app.route('/api/client/<client_id>', methods=['GET'])
def client_details(client_id):
    # Your client details logic here
    return jsonify({
        "total_queries": 0,
        "slow_queries": 0,
        "change_count": 0,
        "view_count": 0,
        "queries": []
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

## Notes

1. All timestamps should be in a consistent format: `YYYY-MM-DD HH:MM:SS` or ISO 8601
2. Execution times should include units (e.g., "298.33ms")
3. Row counts should be formatted as strings with "rows" suffix (e.g., "44606 rows")
4. Ensure all JSON keys match exactly as shown (case-sensitive)
5. The frontend expects consistent data structures - missing fields may cause errors
