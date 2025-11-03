// // src/components/ClientDetails.jsx
// import React, { useEffect, useState } from "react";
// import { useParams, Link } from "react-router-dom";
// import Plot from "react-plotly.js";
// import "../styles/ClientDetails.css";

// const ClientDetails = () => {
//   const { clientId } = useParams();
//   const [clientData, setClientData] = useState(null);

//   useEffect(() => {
//     fetch(`/api/client/${clientId}`)
//       .then((res) => res.json())
//       .then((data) => setClientData(data))
//       .catch((err) => console.error("Error fetching client details:", err));
//   }, [clientId]);

//   if (!clientData) {
//     return <p>Loading client details...</p>;
//   }

//   return (
//     <div className="client-details">
//       <h1>Client {clientId} Details</h1>

//       <div className="card">
//         <p>
//           <strong>Total Queries:</strong> {clientData.total_queries}
//         </p>
//         <p>
//           <strong>Slow Queries:</strong> {clientData.slow_queries}
//         </p>
//       </div>

//       <div className="card chart-container">
//         <Plot
//           data={[
//             {
//               labels: ["DB Changes", "View Only"],
//               values: [clientData.change_count, clientData.view_count],
//               type: "pie",
//             },
//           ]}
//           layout={{
//             title: "Change vs View Queries",
//             paper_bgcolor: "#1e1e1e",
//             font: { color: "#e0e0e0" },
//           }}
//           style={{ width: "400px", height: "350px" }}
//         />
//       </div>
//       <h2>Executed Queries (most recent first)</h2>
//       <div className="card">
//         <table>
//           <thead>
//             <tr>
//               <th>Timestamp</th>
//               <th>Query</th>
//               <th>Result</th>
//               <th>Ranking</th> {/* Added Ranking column */}
//             </tr>
//           </thead>
//           <tbody>
//             {clientData.queries.map((q, index) => (
//               <tr key={index}>
//                 <td>{q.Timestamp}</td>
//                 <td>
//                   <pre style={{ whiteSpace: "pre-wrap", color: "#e0e0e0" }}>
//                     {q.Query}
//                   </pre>
//                 </td>
//                 <td>
//                   <pre style={{ whiteSpace: "pre-wrap", color: "#e0e0e0" }}>
//                     {q.Result}
//                   </pre>
//                 </td>
//                 <td>
//                   <pre style={{ whiteSpace: "pre-wrap", color: "#e0e0e0" }}>
//                     {q.Ranking
//                       ? (typeof q.Ranking === "string"
//                           ? JSON.parse(q.Ranking)
//                           : q.Ranking
//                         )
//                           .map((r) => `${r.cause}: ${r.score}`)
//                           .join("\n")
//                       : "—"}
//                   </pre>
//                 </td>
//               </tr>
//             ))}
//           </tbody>
//         </table>
//       </div>

//       {/* <h2>Executed Queries (most recent first)</h2>
//       <div className="card">
//         <table>
//           <thead>
//             <tr>
//               <th>Timestamp</th>
//               <th>Query</th>
//               <th>Result</th>
//             </tr>
//           </thead>
//           <tbody>
//             {clientData.queries.map((q, index) => (
//               <tr key={index}>
//                 <td>{q.Timestamp}</td>
//                 <td>
//                   <pre style={{ whiteSpace: "pre-wrap", color: "#e0e0e0" }}>
//                     {q.Query}
//                   </pre>
//                 </td>
//                 <td>
//                   <pre style={{ whiteSpace: "pre-wrap", color: "#e0e0e0" }}>
//                     {q.Result}
//                   </pre>
//                 </td>
//               </tr>
//             ))}
//           </tbody>
//         </table>
//       </div> */}

//       <p>
//         <Link to="/">Back to Dashboard</Link>
//       </p>
//     </div>
//   );
// };

// export default ClientDetails;

// src/components/ClientDetails.jsx

// src/components/ClientDetails.jsx
import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import Plot from "react-plotly.js";
import "../styles/ClientDetails.css";

const ClientDetails = () => {
  const { clientId } = useParams();
  const [clientData, setClientData] = useState(null);
  const [alertMessages, setAlertMessages] = useState([]);

  useEffect(() => {
    fetch(`/api/client/${clientId}`)
      .then((res) => res.json())
      .then((data) => {
        setClientData(data);

        // 🔹 Collect unique alert messages (for top banners)
        const msgs = [];
        if (data.queries) {
          data.queries.forEach((q) => {
            if (q.Alert && q.Alert.trim() !== "") {
              msgs.push(q.Alert);
            }
          });
        }
        setAlertMessages([...new Set(msgs)]);
      })
      .catch((err) => console.error("Error fetching client details:", err));
  }, [clientId]);

  if (!clientData) {
    return <p>Loading client details...</p>;
  }

  return (
    <div className="client-details">
      <div className="client-details-header">
        <h1>Client {clientId} Details</h1>
        <Link to="/dba-dashboard" className="back-button">
          ← Back to Dashboard
        </Link>
      </div>

      {/* 🔹 Alert banners */}
      {alertMessages.length > 0 && (
        <div className="alerts-container">
          {alertMessages.map((msg, i) => (
            <div
              key={i}
              className={`alert-banner ${
                msg.toLowerCase().includes("highly")
                  ? "alert-high"
                  : msg.toLowerCase().includes("slightly")
                  ? "alert-medium"
                  : "alert-low"
              }`}
            >
              ⚠ {msg}
            </div>
          ))}
        </div>
      )}

      {/* 🔹 Summary Cards */}
      <div className="card">
        <p>
          <strong>Total Queries:</strong> {clientData.total_queries}
        </p>
        <p>
          <strong>Slow Queries:</strong> {clientData.slow_queries}
        </p>
      </div>

      <div className="card chart-container">
        <Plot
          data={[
            {
              labels: ["DB Changes", "View Only"],
              values: [clientData.change_count, clientData.view_count],
              type: "pie",
            },
          ]}
          layout={{
            title: "Change vs View Queries",
            paper_bgcolor: "#1e1e1e",
            font: { color: "#e0e0e0" },
          }}
          style={{ width: "400px", height: "350px" }}
        />
      </div>

      {/* 🔹 Query Table */}
      <h2>Executed Queries (most recent first)</h2>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Query</th>
              <th>Result</th>
              <th>Status</th>
              <th>Score</th>
              <th>Root Causes</th>
              <th>Alert</th>
            </tr>
          </thead>
          <tbody>
            {clientData.queries.map((q, index) => (
              <tr key={index}>
                <td>{q.Timestamp}</td>

                <td>
                  <pre style={{ whiteSpace: "pre-wrap", color: "#e0e0e0" }}>
                    {q.Query}
                  </pre>
                </td>

                <td>
                  <pre style={{ whiteSpace: "pre-wrap", color: "#e0e0e0" }}>
                    {q.Result}
                  </pre>
                </td>

                <td
                  style={{
                    color:
                      q.Status === "Slow"
                        ? "#ff4d4d"
                        : q.Status === "Near Slow"
                        ? "#ffb84d"
                        : "#4dff88",
                    fontWeight: "bold",
                  }}
                >
                  {q.Status || "—"}
                </td>

                <td>{q.Score ? q.Score.toFixed(3) : "—"}</td>

                <td>
                  {q.RootCauses && q.RootCauses.length > 0 ? (
                    <pre style={{ whiteSpace: "pre-wrap", color: "#e0e0e0" }}>
                      {q.RootCauses.map(
                        (r) => `${r.cause}: ${r.score.toFixed(3)}`
                      ).join("\n")}
                    </pre>
                  ) : (
                    "—"
                  )}
                </td>

                <td>
                  {q.Alert ? (
                    <span
                      className={`alert-tag ${
                        q.Alert.toLowerCase().includes("highly")
                          ? "alert-high"
                          : q.Alert.toLowerCase().includes("slightly")
                          ? "alert-medium"
                          : "alert-low"
                      }`}
                    >
                      {q.Alert}
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ClientDetails;
