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

      appendMessage(`\n> ${currentQuery}`);
      appendMessage(`Response: ${data.response}`);

      if (data.status) {
        appendMessage(`Status: ${data.status}`);
      }

      // Store query details for the sidebar
      setQueryDetails({
        status: data.status || "SUCCESS",
        executionTime: data.execution_time || "298.33ms",
        rowsAffected: data.rows_affected || "44606",
        rootCauses: data.ranking || [],
      });

      // Root Cause Ranking (only if slow)
      if (
        data.ranking &&
        Array.isArray(data.ranking) &&
        data.ranking.length > 0
      ) {
        appendMessage("----- Root Cause Ranking -----");
        data.ranking.forEach((item, idx) =>
          appendMessage(
            `${idx + 1}. ${item.cause} (Score: ${item.score.toFixed(2)})`
          )
        );
        appendMessage("-----------------------------");
      }

      // Real-Time Alert (shown visually)
      if (data.alert) {
        setAlertMessage(data.alert);
        setTimeout(() => setAlertMessage(null), 6000);
      }

      // Add to history
      setQueryHistory((prev) => [
        {
          query: currentQuery,
          executionTime: data.execution_time || "298.33ms",
          rowsAffected: data.rows_affected || "44606",
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

  const handleLogout = () => {
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
            <h3>Alerts (0)</h3>
            <div className="alerts-content">
              <p className="no-alerts">No alerts</p>
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
                {queryDetails.rootCauses &&
                  queryDetails.rootCauses.length > 0 && (
                    <div className="detail-item root-causes">
                      <span className="detail-label">Root Causes</span>
                      <ul className="causes-list">
                        {queryDetails.rootCauses.map((cause, idx) => (
                          <li key={idx}>• {cause.cause}</li>
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
                    <div className="history-query">{item.query}</div>
                    <div className="history-meta">
                      <span>{item.executionTime}</span>
                      <span className="history-rows">
                        {item.rowsAffected} rows
                      </span>
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
