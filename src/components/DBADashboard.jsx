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

          // Calculate average execution time from logs
          if (allLogs.length > 0) {
            const totalExecTime = allLogs.reduce((sum, log) => {
              const execTime = parseFloat(log.ExecutionTime) || 0;
              return sum + execTime;
            }, 0);
            const avgTime = totalExecTime / allLogs.length;
            setAvgExecutionTime(avgTime * 1000); // Convert to ms
            console.log(
              "[DBA Dashboard] Average execution time:",
              avgTime * 1000,
              "ms"
            );
          } else {
            setAvgExecutionTime(0);
          }

          // Calculate query type distribution
          const types = {};
          allLogs.forEach((q) => {
            const type = q.QueryType || "UNKNOWN";
            types[type] = (types[type] || 0) + 1;
          });
          setQueryTypeData(types);
          console.log("[DBA Dashboard] Query type distribution:", types);

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
              // Try to parse ranking data for root cause
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
        })
        .catch((err) => {
          console.error("[DBA Dashboard] Error fetching logs:", err);
          setLogs([]);
          setAllQueries([]);
          setAlerts([]);
        });

      // Fetch dashboard data for client counts and timeline
      fetch("/api/dashboard")
        .then((res) => res.json())
        .then((data) => {
          console.log("[DBA Dashboard] Dashboard data:", data);

          const clientCounts = data.client_counts || {};
          setClientData(clientCounts);
          console.log("[DBA Dashboard] Client counts:", clientCounts);

          // Backend sends different field names, map them correctly
          const slowCount = data.slow_counts?.Slow || 0;
          const fastCount = data.slow_counts?.Fast || 0;
          const totalQueriesCount = slowCount + fastCount;

          setTotalQueries(totalQueriesCount);
          setSlowQueries(slowCount);

          // Show currently connected clients (actually logged in)
          // This will show 0 when everyone logs out
          const activeClientCount = data.current_connected || 0;
          setActiveClients(activeClientCount);
          console.log(
            "[DBA Dashboard] Active clients (currently connected):",
            activeClientCount
          );

          // Build timeline from five_min_counts
          const timeline = [];
          if (data.five_min_counts) {
            Object.entries(data.five_min_counts).forEach(
              ([timestamp, count]) => {
                timeline.push({
                  timestamp: timestamp,
                  count: count,
                  slow: false,
                  client: "Multiple",
                });
              }
            );
          }
          setTimelineData(timeline);
        })
        .catch((err) => console.error("Error fetching dashboard:", err));
    };

    // Initial fetch
    fetchAllData();

    // Auto-refresh every 5 seconds
    const interval = setInterval(() => {
      fetchAllData();
    }, 5000);

    // Cleanup on unmount
    return () => clearInterval(interval);
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
        <div>
          <h1>DBA Dashboard</h1>
          <p className="subtitle">
            System Monitoring & Analytics
            <span className="live-badge">● LIVE</span>
          </p>
        </div>
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
          <p className="metric-value">
            {avgExecutionTime > 0 ? avgExecutionTime.toFixed(2) + "ms" : "N/A"}
          </p>
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
                y: timelineData.map((d) => d.count || 0),
                text: timelineData.map((d) => `${d.count} queries`),
                mode: "lines+markers",
                type: "scatter",
                marker: {
                  color: "#26c6da",
                  size: 8,
                },
                line: {
                  color: "#26c6da",
                  width: 2,
                },
                name: "Queries",
              },
            ]}
            layout={{
              title: "",
              xaxis: { title: "Time (5-minute intervals)" },
              yaxis: {
                title: "Number of Queries",
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
            <span
              className="legend-dot"
              style={{ background: "#26c6da" }}
            ></span>{" "}
            Query Activity (5-minute intervals)
          </span>
        </div>
      </div>

      {/* Charts Row */}
      <div className="charts-row">
        <div className="chart-section half">
          <h2>Client Activity</h2>
          <div className="chart-container">
            {Object.keys(clientData).length > 0 ? (
              <Plot
                data={[
                  {
                    x: Object.keys(clientData),
                    y: Object.values(clientData),
                    type: "bar",
                    marker: {
                      color: "#42a5f5",
                    },
                    text: Object.values(clientData).map((v) => `${v} queries`),
                    textposition: "auto",
                    hovertemplate:
                      "<b>Client %{x}</b><br>%{y} queries<extra></extra>",
                  },
                ]}
                layout={{
                  title: "",
                  xaxis: {
                    title: "Client ID",
                    type: "category",
                  },
                  yaxis: {
                    title: "Total Queries",
                    rangemode: "tozero",
                  },
                  ...darkLayout,
                  showlegend: false,
                  bargap: 0.3,
                }}
                style={{ width: "100%", height: "100%" }}
                config={{ responsive: true }}
              />
            ) : (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  height: "100%",
                  color: "#888",
                }}
              >
                No client activity data available
              </div>
            )}
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
              SELECT: {queryTypeData.SELECT || 0}
            </span>
            <span className="legend-item">
              <span
                className="legend-dot"
                style={{ background: "#66bb6a" }}
              ></span>{" "}
              UPDATE:{" "}
              {queryTypeData.UPDATE || queryTypeData["NEEDS-APPROVAL"] || 0}
            </span>
            <span className="legend-item">
              <span
                className="legend-dot"
                style={{ background: "#ffa726" }}
              ></span>{" "}
              INSERT: {queryTypeData.INSERT || 0}
            </span>
            <span className="legend-item">
              <span
                className="legend-dot"
                style={{ background: "#ef5350" }}
              ></span>{" "}
              DELETE: {queryTypeData.DELETE || 0}
            </span>
          </div>
        </div>
      </div>

      {/* Recent Alerts and All Queries side by side */}
      <div className="info-row">
        <div className="info-section">
          <h2>Recent Alerts</h2>
          <div className="alerts-container">
            {alerts && alerts.length > 0 ? (
              alerts.map((alert, i) => (
                <div key={i} className="alert-item">
                  ⚠️ [{alert.timestamp}] <strong>{alert.client}</strong>:{" "}
                  {alert.message}
                </div>
              ))
            ) : (
              <p className="no-data">
                No alerts{" "}
                {alerts
                  ? `(${alerts.length} alerts in state)`
                  : "(alerts is null/undefined)"}
              </p>
            )}
          </div>
        </div>

        <div className="info-section">
          <h2>Recent Queries</h2>
          <div className="queries-list">
            {allQueries && allQueries.length > 0 ? (
              allQueries.slice(0, 5).map((query, i) => (
                <div key={i} className="query-item">
                  <div className="query-header-dba">
                    <div className="query-text">{query.Query}</div>
                    {query.SlowQuery === "True" ||
                    query.SlowQuery === true ||
                    query.SlowQuery === "true" ? (
                      <span className="query-badge slow-badge">SLOW</span>
                    ) : (
                      <span className="query-badge normal-badge">NORMAL</span>
                    )}
                  </div>
                  <div className="query-meta">
                    <span>Client {query.ClientID}</span>
                    <span>{query.ExecutionTime}s</span>
                    <span className="query-type">{query.QueryType}</span>
                  </div>
                </div>
              ))
            ) : (
              <p className="no-data">
                No queries executed yet{" "}
                {allQueries
                  ? `(${allQueries.length} queries in state)`
                  : "(queries is null/undefined)"}
              </p>
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
                logs.slice(0, 10).map((row, index) => {
                  // Parse SlowQuery properly (can be "True", true, "true", 1, etc.)
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
                        <span
                          className={`status-badge ${
                            isSlowQuery ? "slow" : "normal"
                          }`}
                        >
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
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DBADashboard;
