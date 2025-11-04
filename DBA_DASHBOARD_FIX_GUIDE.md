# DBA Dashboard Activity Logs Fix - Implementation Guide

## Problem Summary

The DBA Dashboard was not displaying:

- Activity Logs table (showing "No logs available")
- Recent Alerts (showing "No alerts")
- Recent Queries (showing "No queries executed yet")
- Average Execution Time (showing "N/A")

## Root Cause Analysis

1. **CSV Parsing Issues**: Multi-line Result fields in activity_log.csv weren't being parsed correctly
2. **Data Flow**: Logs were being fetched but state wasn't updating properly
3. **Missing Error Handling**: No debugging output to identify fetch failures
4. **SlowQuery Parsing**: Inconsistent boolean parsing (True vs "True" vs true)

## Changes Made

### Backend Changes (`backend/app.py`)

#### 1. Improved `/api/logs` Endpoint

```python
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
```

**Key Improvements:**

- Added `quoting=1` parameter for proper CSV parsing with multi-line fields
- Added `fillna("")` to handle missing values
- Added debug logging to track record count
- Better error handling with logging

### Frontend Changes (`src/components/DBADashboard.jsx`)

#### 1. Enhanced Data Fetching with Debugging

```javascript
const fetchAllData = () => {
  // Fetch logs first to calculate everything from it
  fetch("/api/logs")
    .then((res) => {
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      return res.json();
    })
    .then((data) => {
      console.log("[DBA Dashboard] Fetched logs:", data);

      // Handle both array and error object responses
      if (data.error) {
        console.error("[DBA Dashboard] API error:", data.error);
        setLogs([]);
        setAllQueries([]);
        setAlerts([]);
        return;
      }

      const allLogs = Array.isArray(data) ? data : [];
      console.log("[DBA Dashboard] Processed logs count:", allLogs.length);

      // Sort by timestamp descending (most recent first)
      allLogs.sort((a, b) => {
        const dateA = new Date(a.Timestamp);
        const dateB = new Date(b.Timestamp);
        return dateB - dateA;
      });

      setLogs(allLogs);
      setAllQueries(allLogs);
      // ... rest of processing
    });
};
```

**Key Improvements:**

- Added comprehensive console logging for debugging
- Added error response handling
- Added data validation (Array.isArray check)
- Sort logs by timestamp (most recent first)
- Better error state management

#### 2. Fixed Average Execution Time Calculation

```javascript
// Calculate average execution time from logs
if (allLogs.length > 0) {
  const totalExecTime = allLogs.reduce((sum, log) => {
    const execTime = parseFloat(log.ExecutionTime) || 0;
    return sum + execTime;
  }, 0);
  const avgTime = totalExecTime / allLogs.length;
  setAvgExecutionTime(avgTime * 1000); // Convert to ms
  console.log("[DBA Dashboard] Average execution time:", avgTime * 1000, "ms");
} else {
  setAvgExecutionTime(0);
}
```

#### 3. Improved Alerts Generation

```javascript
// Generate alerts from slow queries
const slowAlerts = allLogs
  .filter((log) => {
    const isSlowQuery =
      log.SlowQuery === "True" ||
      log.SlowQuery === true ||
      log.SlowQuery === "true" ||
      log.SlowQuery === 1 ||
      log.SlowQuery === "1";
    return isSlowQuery;
  })
  .slice(0, 5) // Get last 5 slow queries
  .map((log) => {
    let rootCause = "Performance issue detected";
    try {
      if (log.Ranking && log.Ranking.trim() !== "") {
        const ranking = JSON.parse(log.Ranking);
        if (ranking.root_cause && ranking.root_cause !== "None") {
          rootCause = ranking.root_cause.replace(/_/g, " ");
        } else if (Array.isArray(ranking) && ranking.length > 0) {
          // Handle old format with array of causes
          rootCause = ranking[0].cause.replace(/_/g, " ");
        }
      }
    } catch (e) {
      console.error("[DBA Dashboard] Error parsing ranking:", e);
    }

    return {
      timestamp: log.Timestamp,
      client: `Client ${log.ClientID}`,
      message: `Slow query: ${rootCause}`,
    };
  });

console.log("[DBA Dashboard] Generated alerts:", slowAlerts);
setAlerts(slowAlerts);
```

**Key Improvements:**

- Enhanced SlowQuery boolean parsing (handles multiple formats)
- Added support for both new and old ranking data formats
- Better error handling with try-catch
- Debug logging for generated alerts

#### 4. Fixed Activity Logs Table Rendering

```javascript
{
  logs && logs.length > 0 ? (
    logs.slice(0, 10).map((row, index) => {
      // Parse SlowQuery properly
      const isSlowQuery =
        row.SlowQuery === "True" ||
        row.SlowQuery === true ||
        row.SlowQuery === "true" ||
        row.SlowQuery === 1;

      // Try to parse and format ranking data nicely
      let rankingDisplay = row.Ranking || "N/A";
      try {
        if (row.Ranking && row.Ranking.trim() !== "") {
          const ranking = JSON.parse(row.Ranking);
          if (ranking.status && ranking.root_cause) {
            rankingDisplay = `${ranking.status} - ${ranking.root_cause}`;
          }
        }
      } catch (e) {
        // Keep original string if parsing fails
      }

      return (
        <tr key={index}>
          <td>{row.Timestamp}</td>
          <td>{row.ClientID}</td>
          <td>{row.QueryType}</td>
          <td>
            <pre className="query-cell">{row.Query}</pre>
          </td>
          <td>{row.ExecutionTime}s</td>
          <td>
            <span className={`status-badge ${isSlowQuery ? "slow" : "normal"}`}>
              {isSlowQuery ? "Yes" : "No"}
            </span>
          </td>
          <td>
            <pre className="result-cell">
              {row.Result && row.Result.length > 100
                ? row.Result.substring(0, 100) + "..."
                : row.Result}
            </pre>
          </td>
          <td>
            <pre className="ranking-cell">{rankingDisplay}</pre>
          </td>
        </tr>
      );
    })
  ) : (
    <tr>
      <td colSpan="8">No logs available</td>
    </tr>
  );
}
```

**Key Improvements:**

- Robust SlowQuery boolean parsing
- Smart ranking display formatting
- Result truncation to 100 chars for readability
- Added "s" suffix to ExecutionTime
- Better null/undefined handling

#### 5. Dynamic Query Type Distribution

```javascript
<div className="legend">
  <span className="legend-item">
    <span className="legend-dot" style={{ background: "#42a5f5" }}></span>
    SELECT: {queryTypeData.SELECT || 0}
  </span>
  <span className="legend-item">
    <span className="legend-dot" style={{ background: "#66bb6a" }}></span>
    UPDATE: {queryTypeData.UPDATE || queryTypeData["NEEDS-APPROVAL"] || 0}
  </span>
  <span className="legend-item">
    <span className="legend-dot" style={{ background: "#ffa726" }}></span>
    INSERT: {queryTypeData.INSERT || 0}
  </span>
  <span className="legend-item">
    <span className="legend-dot" style={{ background: "#ef5350" }}></span>
    DELETE: {queryTypeData.DELETE || 0}
  </span>
</div>
```

**Changed from:** Hardcoded values (SELECT: 1, UPDATE: 0, etc.)
**Changed to:** Dynamic values from actual query data

## Testing

### 1. Backend Testing

Created `test_api.html` for API endpoint testing:

- Tests `/api/logs` endpoint
- Tests `/api/dashboard` endpoint
- Shows record counts and slow query statistics
- Auto-runs on page load

**To use:**

1. Ensure Flask backend is running on port 5000
2. Open `test_api.html` in browser
3. Check if logs are being returned correctly

### 2. Frontend Testing Steps

1. **Start Backend:**

   ```bash
   cd backend
   python app.py
   ```

2. **Start Frontend:**

   ```bash
   npm start
   ```

3. **Open Browser Console:**

   - Go to DBA Dashboard
   - Open DevTools (F12) → Console tab
   - Look for debug messages:
     ```
     [DBA Dashboard] Fetched logs: [...]
     [DBA Dashboard] Processed logs count: 56
     [DBA Dashboard] Average execution time: 4523.5 ms
     [DBA Dashboard] Query type distribution: {SELECT: 27, NEEDS-APPROVAL: 29}
     [DBA Dashboard] Generated alerts: [...]
     ```

4. **Verify Data Display:**
   - ✓ Recent Alerts shows 5 most recent slow queries
   - ✓ Recent Queries shows 5 most recent queries with SLOW/NORMAL badges
   - ✓ Activity Logs table shows 10 most recent entries
   - ✓ Average Execution Time shows calculated value (not N/A)

## Debugging Checklist

If data still doesn't appear:

### Backend Checks

- [ ] Flask server is running (`python app.py`)
- [ ] Port 5000 is accessible
- [ ] `activity_log.csv` exists and has data
- [ ] Check terminal for backend logs: `[API /logs] Returning X log records`
- [ ] Test API directly: `curl http://localhost:5000/api/logs`

### Frontend Checks

- [ ] React app is running (`npm start`)
- [ ] No CORS errors in browser console
- [ ] Check browser console for debug logs: `[DBA Dashboard] Fetched logs:`
- [ ] Verify state variables have data (use React DevTools)
- [ ] Check Network tab for successful API calls (Status 200)

### Common Issues

1. **"No logs available"** → Backend not returning data or API call failing
2. **"No alerts"** → No slow queries in database OR SlowQuery parsing issue
3. **"No queries executed yet"** → allQueries state not being set
4. **Network error** → Backend not running or wrong port

## Files Modified

1. `backend/app.py` - Improved /api/logs endpoint with better CSV parsing
2. `src/components/DBADashboard.jsx` - Enhanced data fetching, state management, and rendering
3. `test_api.html` - Created API testing tool

## Auto-Refresh

All data refreshes automatically every 5 seconds via:

```javascript
const interval = setInterval(() => {
  fetchAllData();
}, 5000);

// Cleanup on unmount
return () => clearInterval(interval);
```

## Next Steps

1. **Restart Backend Server** (if running)

   ```bash
   # Stop current server (Ctrl+C)
   cd backend
   python app.py
   ```

2. **Refresh Frontend** (hard refresh: Ctrl+Shift+R)

3. **Monitor Console** for debug messages

4. **Test with API Tester**

   - Open `test_api.html` in browser
   - Verify logs are being returned

5. **Execute a Test Query** as client to generate fresh data

---

## Expected Behavior After Fix

✅ **Recent Alerts Section:**

- Shows up to 5 most recent slow queries
- Displays timestamp, client ID, and root cause
- Example: "⚠️ [2025-11-04 16:01:32] Client 3: Slow query: missing indexes"

✅ **Recent Queries Section:**

- Shows 5 most recent queries
- SLOW/NORMAL badges with color coding
- Client ID, execution time, and query type

✅ **Activity Logs Table:**

- Shows 10 most recent log entries
- Properly formatted SlowQuery column (Yes/No badges)
- Truncated Result column (100 chars max)
- Parsed Ranking column (Status - root_cause format)

✅ **Average Execution Time:**

- Shows calculated average in milliseconds
- Example: "4523.50ms" instead of "N/A"

✅ **Query Type Distribution:**

- Dynamic counts: "SELECT: 27", "UPDATE: 29", etc.
- Matches actual data from logs

All sections update automatically every 5 seconds! 🔄
