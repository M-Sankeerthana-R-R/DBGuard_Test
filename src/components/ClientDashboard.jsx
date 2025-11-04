// src/components/ClientDashboard.jsx
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/ClientDashboard.css";

const ClientDashboard = () => {
  const navigate = useNavigate();
  const [clientId, setClientId] = useState("");
  const [connected, setConnected] = useState(false);
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [alertMessage, setAlertMessage] = useState(null);
  const [queryHistory, setQueryHistory] = useState([]);
  const [queryDetails, setQueryDetails] = useState(null);
  const [alerts, setAlerts] = useState([]);

  const appendMessage = (msg) => {
    setMessages((prev) => [...prev, msg]);
  };

  const autoConnect = React.useCallback(async (id) => {
    try {
      const res = await fetch("/api/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clientId: id }),
      });

      const data = await res.json();

      if (data.status === "connected") {
        setConnected(true);
        appendMessage("✓ Connected to server: " + data.message);
      } else {
        appendMessage("✗ Connection failed: " + data.message);
      }
    } catch (err) {
      appendMessage("✗ Error connecting: " + err.message);
    }
  }, []);

  useEffect(() => {
    // Check authentication
    const userType = sessionStorage.getItem("userType");
    const storedClientId = sessionStorage.getItem("clientId");

    if (userType !== "client" || !storedClientId) {
      navigate("/");
      return;
    }

    setClientId(storedClientId);

    // Auto-connect on mount
    autoConnect(storedClientId);
  }, [navigate, autoConnect]);

  const handleExecute = async () => {
    if (!query.trim()) return;

    const currentQuery = query;
    setQuery("");

    try {
      const res = await fetch("/api/execute_query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clientId, query: currentQuery }),
      });
      const data = await res.json();

      // Parse response - backend sends plain text or may not parse JSON
      let actualResponse = data.response;
      let queryStatus = "SUCCESS";
      let rootCause = "";
      let scoreValue = 0;

      // Try to parse if response is JSON string
      if (
        typeof actualResponse === "string" &&
        actualResponse.startsWith("{")
      ) {
        try {
          const parsed = JSON.parse(actualResponse);
          actualResponse = parsed.response || actualResponse;
          queryStatus = parsed.status || "SUCCESS";
          rootCause = parsed.root_cause || "";
          scoreValue = parsed.score || 0;
        } catch (e) {
          // Not JSON, use as-is
        }
      }

      appendMessage(`\n> ${currentQuery}`);
      appendMessage(`Response: ${actualResponse}`);

      // Show query status if available
      if (queryStatus && queryStatus !== "SUCCESS") {
        appendMessage(`Query Status: ${queryStatus}`);
      }

      // Show score if available
      if (scoreValue > 0) {
        appendMessage(`Score: ${scoreValue.toFixed(4)}`);
      }

      // Show root cause if available
      if (rootCause && rootCause !== "") {
        appendMessage(`Root Cause: ${rootCause}`);
      }

      // Store query details for the sidebar
      setQueryDetails({
        status: queryStatus,
        executionTime: "N/A", // Backend doesn't send execution time to client
        rowsAffected:
          actualResponse.split("\n").length > 0
            ? actualResponse.split("\n").length + " rows"
            : "Unknown",
        rootCauses: rootCause ? [{ cause: rootCause, score: scoreValue }] : [],
        score: scoreValue,
      });

      // Root Cause Ranking (show if available)
      if (rootCause && rootCause !== "") {
        appendMessage("\n----- Root Cause Analysis -----");
        appendMessage(`1. ${rootCause} (Score: ${scoreValue.toFixed(4)})`);
        appendMessage("-------------------------------\n");
      }

      // Real-Time Alert (shown visually for slow queries)
      if (queryStatus === "Slow") {
        const alertMsg = "🚨 Slow query detected! Check root cause analysis.";
        setAlertMessage(alertMsg);
        setTimeout(() => setAlertMessage(null), 6000);

        // Add to persistent alerts
        setAlerts((prev) => [
          {
            id: Date.now(),
            type: "slow",
            message: `Slow query: ${currentQuery.substring(0, 50)}...`,
            timestamp: new Date().toLocaleTimeString(),
            rootCause: rootCause,
            score: scoreValue,
          },
          ...prev.slice(0, 4), // Keep last 5 alerts
        ]);
      } else if (queryStatus === "Near Slow") {
        const alertMsg = "⚠️ Query approaching slowness threshold.";
        setAlertMessage(alertMsg);
        setTimeout(() => setAlertMessage(null), 6000);

        // Add to persistent alerts
        setAlerts((prev) => [
          {
            id: Date.now(),
            type: "near-slow",
            message: `Near slow query: ${currentQuery.substring(0, 50)}...`,
            timestamp: new Date().toLocaleTimeString(),
            rootCause: rootCause,
            score: scoreValue,
          },
          ...prev.slice(0, 4), // Keep last 5 alerts
        ]);
      }

      // Add to history
      setQueryHistory((prev) => [
        {
          query: currentQuery,
          status: queryStatus,
          executionTime: "N/A",
          rowsAffected: actualResponse.split("\n").length + " rows",
          timestamp: new Date().toLocaleTimeString(),
        },
        ...prev.slice(0, 9), // Keep last 10
      ]);
    } catch (err) {
      appendMessage(`✗ Error executing query: ${err.message}`);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && e.ctrlKey) {
      handleExecute();
    }
  };

  const handleLogout = async () => {
    // Call disconnect API to update connected clients
    try {
      await fetch("/api/disconnect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clientId }),
      });
    } catch (error) {
      console.error("Error disconnecting:", error);
    }

    // Clear session and navigate to login
    sessionStorage.clear();
    navigate("/");
  };

  return (
    <div className="client-dashboard">
      <div className="client-header">
        <div>
          <h1>Client Dashboard</h1>
          <p className="client-id">Welcome, Client {clientId}</p>
        </div>
        <button className="logout-btn" onClick={handleLogout}>
          Logout
        </button>
      </div>

      <div className="dashboard-content">
        {/* Main Console Area */}
        <div className="console-section">
          {/* Alert Box */}
          {alertMessage && <div className="alert-box">⚠️ {alertMessage}</div>}

          {/* Query Input */}
          <div className="query-panel">
            <h2>Submit Query</h2>
            <textarea
              className="query-input"
              placeholder="Enter your SQL query here..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyPress}
              disabled={!connected}
            />
            <button
              className="execute-btn"
              onClick={handleExecute}
              disabled={!connected || !query.trim()}
            >
              Execute Query
            </button>
            <p className="hint">Tip: Press Ctrl+Enter to execute</p>
          </div>

          {/* Console Output */}
          <div className="console-output">
            <div className="console-header">
              <span>Console Output</span>
              <button className="clear-btn" onClick={() => setMessages([])}>
                Clear
              </button>
            </div>
            <div className="output-content">
              {messages.length === 0 ? (
                <p className="placeholder">
                  No output yet. Execute a query to see results.
                </p>
              ) : (
                messages.map((msg, idx) => (
                  <div key={idx} className="output-line">
                    {msg}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="sidebar">
          {/* Alerts Section */}
          <div className="sidebar-section">
            <h3>Alerts ({alerts.length})</h3>
            <div className="alerts-content">
              {alerts.length === 0 ? (
                <p className="no-alerts">No alerts</p>
              ) : (
                alerts.map((alert) => (
                  <div key={alert.id} className={`alert-item ${alert.type}`}>
                    <div className="alert-header">
                      <span className={`alert-badge ${alert.type}`}>
                        {alert.type === "slow" ? "SLOW" : "NEAR SLOW"}
                      </span>
                      <span className="alert-time">{alert.timestamp}</span>
                    </div>
                    <div className="alert-message">{alert.message}</div>
                    {alert.rootCause && (
                      <div className="alert-cause">
                        <strong>Root Cause:</strong> {alert.rootCause} (Score:{" "}
                        {alert.score.toFixed(4)})
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Query Details Section */}
          <div className="sidebar-section">
            <h3>Query Details</h3>
            {queryDetails ? (
              <div className="details-content">
                <div className="detail-item">
                  <span className="detail-label">Status</span>
                  <span
                    className={`detail-value status-${queryDetails.status.toLowerCase()}`}
                  >
                    {queryDetails.status}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Execution Time</span>
                  <span className="detail-value">
                    {queryDetails.executionTime}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Rows Affected</span>
                  <span className="detail-value">
                    {queryDetails.rowsAffected}
                  </span>
                </div>
                {queryDetails.score !== undefined && (
                  <div className="detail-item">
                    <span className="detail-label">Analysis Score</span>
                    <span className="detail-value">
                      {queryDetails.score.toFixed(4)}
                    </span>
                  </div>
                )}
                {queryDetails.rootCauses &&
                  queryDetails.rootCauses.length > 0 && (
                    <div className="detail-item root-causes">
                      <span className="detail-label">Root Cause Analysis</span>
                      <ul className="causes-list">
                        {queryDetails.rootCauses.map((cause, idx) => (
                          <li key={idx}>
                            <strong>{cause.cause || "Normal Query"}</strong>
                            <span className="cause-score">
                              {" "}
                              (Score: {cause.score.toFixed(4)})
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
              </div>
            ) : (
              <p className="no-details">Execute a query to see details</p>
            )}
          </div>

          {/* Query History */}
          <div className="sidebar-section">
            <h3>Query History</h3>
            <div className="history-content">
              {queryHistory.length === 0 ? (
                <p className="no-history">No queries executed yet</p>
              ) : (
                queryHistory.map((item, idx) => (
                  <div key={idx} className="history-item">
                    <div className="history-header">
                      <div className="history-query">{item.query}</div>
                      {item.status && item.status !== "SUCCESS" && (
                        <span
                          className={`status-badge ${item.status
                            .toLowerCase()
                            .replace(" ", "-")}`}
                        >
                          {item.status}
                        </span>
                      )}
                    </div>
                    <div className="history-meta">
                      <span>{item.executionTime}</span>
                      <span className="history-rows">{item.rowsAffected}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClientDashboard;
