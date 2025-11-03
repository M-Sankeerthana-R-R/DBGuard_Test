// src/components/Login.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/Login.css";

const Login = () => {
  const [userType, setUserType] = useState("client"); // 'client' or 'dba'
  const [clientId, setClientId] = useState("");
  const [dbaPin, setDbaPin] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const DBA_PIN = "1234"; // You can change this or make it configurable

  const handleLogin = () => {
    setError("");

    if (userType === "dba") {
      if (dbaPin === DBA_PIN) {
        // Store authentication in sessionStorage
        sessionStorage.setItem("userType", "dba");
        navigate("/dba-dashboard");
      } else {
        setError("Invalid DBA PIN");
      }
    } else {
      // Client login
      if (clientId.trim()) {
        sessionStorage.setItem("userType", "client");
        sessionStorage.setItem("clientId", clientId);
        navigate("/client-dashboard");
      } else {
        setError("Please enter a Client ID");
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleLogin();
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1 className="login-title">SQL Query Dashboard</h1>

        <div className="user-type-selector">
          <button
            className={`type-btn ${userType === "client" ? "active" : ""}`}
            onClick={() => {
              setUserType("client");
              setError("");
            }}
          >
            Client Login
          </button>
          <button
            className={`type-btn ${userType === "dba" ? "active" : ""}`}
            onClick={() => {
              setUserType("dba");
              setError("");
            }}
          >
            DBA Login
          </button>
        </div>

        {userType === "client" ? (
          <div className="input-container">
            <input
              type="text"
              placeholder="Enter your Client ID"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              onKeyPress={handleKeyPress}
              className="login-input"
            />
          </div>
        ) : (
          <div className="input-container">
            <input
              type="password"
              placeholder="Enter DBA PIN"
              value={dbaPin}
              onChange={(e) => setDbaPin(e.target.value)}
              onKeyPress={handleKeyPress}
              className="login-input"
            />
          </div>
        )}

        {error && <div className="error-message">{error}</div>}

        <button className="login-btn" onClick={handleLogin}>
          Login
        </button>

        {userType === "client" && (
          <p className="demo-text">Demo: Use any Client ID</p>
        )}
      </div>
    </div>
  );
};

export default Login;
