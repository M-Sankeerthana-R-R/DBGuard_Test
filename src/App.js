// src/App.js
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./components/Login";
import DBADashboard from "./components/DBADashboard";
import ClientDashboard from "./components/ClientDashboard";
import ClientDetails from "./components/ClientDetails";
import "./App.css";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dba-dashboard" element={<DBADashboard />} />
        <Route path="/client-dashboard" element={<ClientDashboard />} />
        <Route path="/client/:clientId" element={<ClientDetails />} />
      </Routes>
    </Router>
  );
}

export default App;
// import { BrowserRouter, Routes, Route } from "react-router-dom";

// function Dashboard() {
//   return <h1>Hello Dashboard</h1>;
// }

// export default function App() {
//   return (
//     <BrowserRouter>
//       <Routes>
//         <Route path="/" element={<Dashboard />} />
//       </Routes>
//     </BrowserRouter>
//   );
// }
