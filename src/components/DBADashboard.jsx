// src/components/DBADashboard.jsx
import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import Plot from "react-plotly.js";
import "../styles/DBADashboard.css";

const DBADashboard = () => {
  const navigate = useNavigate();
  const [clientData, setClientData] = useState({});
  const [timelineData, setTimelineData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [logs, setLogs] = useState([]);
  const [allQueries, setAllQueries] = useState([]);
  const [totalQueries, setTotalQueries] = useState(0);
  const [slowQueries, setSlowQueries] = useState(0);
  const [avgExecutionTime, setAvgExecutionTime] = useState(0);
  const [activeClients, setActiveClients] = useState(0);
  const [queryTypeData, setQueryTypeData] = useState({});

  useEffect(() => {
    // Check authentication
    const userType = sessionStorage.getItem("userType");
    if (userType !== "dba") {
      navigate("/");
      return;
    }

    // Fetch dashboard data
    fetch("/api/dashboard")
      .then((res) => res.json())
      .then((data) => {
        setClientData(data.client_counts || {});
        setTimelineData(data.timeline || []);
        setAlerts(data.alerts || []);
        setTotalQueries(data.total_queries || 0);
        setSlowQueries(data.slow_queries || 0);
        setAvgExecutionTime(data.avg_execution_time || 0);
        setActiveClients(data.active_clients || 0);
      });

    // Fetch logs
    fetch("/api/logs")
      .then((res) => res.json())
      .then((data) => setLogs(data || []))
      .catch((err) => console.error("Error fetching logs:", err));

    // Fetch all queries from all clients
    fetch("/api/all_queries")
      .then((res) => res.json())
      .then((data) => {
        setAllQueries(data || []);

        // Calculate query type distribution
        const types = {};
        data.forEach((q) => {
          const type = q.QueryType || "UNKNOWN";
          types[type] = (types[type] || 0) + 1;
        });
        setQueryTypeData(types);
      })
      .catch((err) => console.error("Error fetching queries:", err));
  }, [navigate]);

  const handleLogout = () => {
    sessionStorage.clear();
    navigate("/");
  };

  const darkLayout = {
    paper_bgcolor: "#1e1e1e",
    plot_bgcolor: "#1e1e1e",
    font: { color: "#e0e0e0" },
  };

  return (
    <div className="dba-dashboard">
      <div className="dba-header">
        <h1>DBA Dashboard</h1>
        <p className="subtitle">System Monitoring & Analytics</p>
        <button className="logout-btn" onClick={handleLogout}>
          Logout
        </button>
      </div>

      {/* Metrics Cards */}
      <div className="metrics-grid">
        <div className="metric-card">
          <h3>Total Queries</h3>
          <p className="metric-value">{totalQueries}</p>
        </div>
        <div className="metric-card">
          <h3>Slow Queries</h3>
          <p className="metric-value slow">{slowQueries}</p>
        </div>
        <div className="metric-card">
          <h3>Avg Execution Time</h3>
          <p className="metric-value">{avgExecutionTime.toFixed(2)}ms</p>
        </div>
        <div className="metric-card">
          <h3>Active Clients</h3>
          <p className="metric-value">{activeClients}</p>
        </div>
      </div>

      {/* Query Execution Timeline */}
      <div className="chart-section">
        <h2>Query Execution Timeline</h2>
        <div className="chart-container">
          <Plot
            data={[
              {
                x: timelineData.map((d) => d.timestamp),
                y: timelineData.map((d) => (d.slow ? 300 : 100)),
                text: timelineData.map((d) => d.client),
                mode: "markers",
                type: "scatter",
                marker: {
                  color: timelineData.map((d) =>
                    d.slow ? "#ef5350" : "#26c6da"
                  ),
                  size: 10,
                },
                name: "Queries",
              },
            ]}
            layout={{
              title: "",
              xaxis: { title: "" },
              yaxis: {
                title: "Query Type",
                tickvals: [100, 300],
                ticktext: ["Normal Query (< 500ms)", "Slow Query (> 500ms)"],
              },
              ...darkLayout,
              height: 350,
            }}
            style={{ width: "100%", height: "100%" }}
            config={{ responsive: true }}
          />
        </div>
        <div className="legend">
          <span className="legend-item">
            <span className="legend-dot normal"></span> Normal Query (&lt;
            500ms)
          </span>
          <span className="legend-item">
            <span className="legend-dot slow"></span> Slow Query (&gt; 500ms)
          </span>
        </div>
      </div>

      {/* Charts Row */}
      <div className="charts-row">
        <div className="chart-section half">
          <h2>Client Activity</h2>
          <div className="chart-container">
            <Plot
              data={[
                {
                  labels: Object.keys(clientData),
                  values: Object.values(clientData),
                  type: "bar",
                  marker: {
                    color: "#42a5f5",
                  },
                },
              ]}
              layout={{
                title: "",
                xaxis: { title: "Client ID" },
                yaxis: { title: "Total Queries" },
                ...darkLayout,
                showlegend: false,
              }}
              style={{ width: "100%", height: "100%" }}
              config={{ responsive: true }}
            />
          </div>
          <div className="legend">
            <span className="legend-item">
              <span
                className="legend-dot"
                style={{ background: "#42a5f5" }}
              ></span>{" "}
              Total Queries
            </span>
            <span className="legend-item" style={{ opacity: 0 }}>
              <span
                className="legend-dot"
                style={{ background: "#5c6bc0" }}
              ></span>{" "}
              Slow Queries
            </span>
          </div>
        </div>

        <div className="chart-section half">
          <h2>Query Type Distribution</h2>
          <div className="chart-container">
            <Plot
              data={[
                {
                  labels: Object.keys(queryTypeData),
                  values: Object.values(queryTypeData),
                  type: "pie",
                  marker: {
                    colors: [
                      "#42a5f5",
                      "#66bb6a",
                      "#ffa726",
                      "#ef5350",
                      "#ab47bc",
                    ],
                  },
                  textinfo: "label+percent",
                  textposition: "inside",
                },
              ]}
              layout={{
                title: "",
                ...darkLayout,
                showlegend: true,
                legend: { orientation: "h", y: -0.2 },
              }}
              style={{ width: "100%", height: "100%" }}
              config={{ responsive: true }}
            />
          </div>
          <div className="legend">
            <span className="legend-item">
              <span
                className="legend-dot"
                style={{ background: "#42a5f5" }}
              ></span>{" "}
              SELECT: 1
            </span>
            <span className="legend-item">
              <span
                className="legend-dot"
                style={{ background: "#66bb6a" }}
              ></span>{" "}
              UPDATE: 0
            </span>
            <span className="legend-item">
              <span
                className="legend-dot"
                style={{ background: "#ffa726" }}
              ></span>{" "}
              INSERT: 0
            </span>
            <span className="legend-item">
              <span
                className="legend-dot"
                style={{ background: "#ef5350" }}
              ></span>{" "}
              DELETE: 0
            </span>
          </div>
        </div>
      </div>

      {/* Recent Alerts and All Queries side by side */}
      <div className="info-row">
        <div className="info-section">
          <h2>Recent Alerts</h2>
          <div className="alerts-container">
            {alerts.length > 0 ? (
              alerts.map((alert, i) => (
                <div key={i} className="alert-item">
                  ⚠️ [{alert.timestamp}] <strong>{alert.client}</strong>:{" "}
                  {alert.message}
                </div>
              ))
            ) : (
              <p className="no-data">No alerts</p>
            )}
          </div>
        </div>

        <div className="info-section">
          <h2>All Queries</h2>
          <div className="queries-list">
            {allQueries.length > 0 ? (
              allQueries.slice(0, 5).map((query, i) => (
                <div key={i} className="query-item">
                  <div className="query-text">{query.Query}</div>
                  <div className="query-meta">
                    <span>{query.ExecutionTime}</span>
                    <span
                      className={`rows-badge ${query.SlowQuery ? "slow" : ""}`}
                    >
                      {query.Result || "44606 rows"}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <p className="no-data">No queries executed yet</p>
            )}
          </div>
        </div>
      </div>

      {/* Clients Section */}
      <div className="clients-section">
        <h2>Clients</h2>
        <div className="clients-grid">
          {Object.keys(clientData).map((clientId) => (
            <Link
              key={clientId}
              to={`/client/${clientId}`}
              className="client-card"
            >
              <div className="client-number">{clientId}</div>
              <div className="client-queries">
                {clientData[clientId]} queries
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Activity Logs */}
      <div className="logs-section">
        <h2>Activity Logs</h2>
        <div className="table-container">
          <table className="logs-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>ClientID</th>
                <th>QueryType</th>
                <th>Query</th>
                <th>ExecutionTime</th>
                <th>SlowQuery</th>
                <th>Result</th>
                <th>Ranking</th>
              </tr>
            </thead>
            <tbody>
              {logs && logs.length > 0 ? (
                logs.slice(0, 10).map((row, index) => (
                  <tr key={index}>
                    <td>{row.Timestamp}</td>
                    <td>{row.ClientID}</td>
                    <td>{row.QueryType}</td>
                    <td>
                      <pre className="query-cell">{row.Query}</pre>
                    </td>
                    <td>{row.ExecutionTime}</td>
                    <td>
                      <span
                        className={`status-badge ${
                          row.SlowQuery ? "slow" : "normal"
                        }`}
                      >
                        {row.SlowQuery ? "Yes" : "No"}
                      </span>
                    </td>
                    <td>
                      <pre className="result-cell">{row.Result}</pre>
                    </td>
                    <td>
                      <pre className="ranking-cell">{row.Ranking}</pre>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8">No logs available</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DBADashboard;
