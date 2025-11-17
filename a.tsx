"use client";

import React, { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

type LoginFormProps = {
  onLoginSuccess: () => void;
};

export const LoginForm: React.FC<LoginFormProps> = ({ onLoginSuccess }) => {
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Check credentials
    if (userId === "admin" && password === "admin123") {
      setError("");
      onLoginSuccess();
    } else {
      setError("Invalid user ID or password. Please try again.");
    }
  };

  return (
    <div className="flex justify-center items-center w-full h-full px-10">
      <form
        className="card"
        onSubmit={handleSubmit}
        noValidate
        style={{ 
          width: "100%", 
          maxWidth: 500, 
          padding: 32,
          margin: "auto"
        }}
      >
        <div className="card__header">
          <div className="card__title" style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>
            Login
          </div>
          <p style={{ fontSize: "0.875rem", color: "#64748b", marginBottom: "1rem" }}>
            Enter your credentials to access the Health Analytics Dashboard
          </p>
          <div aria-hidden className="progress">
            <div className="progress__bar" style={{ width: "100%" }} />
          </div>
        </div>

        <div className="grid" style={{ gap: "1.5rem" }}>
          {/* User ID */}
          <div className="field">
            <label htmlFor="userId">User ID</label>
            <input
              id="userId"
              name="userId"
              type="text"
              autoComplete="username"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="Enter your user ID"
              required
            />
          </div>

          {/* Password */}
          <div className="field relative">
            <label htmlFor="password">Password</label>
            <div className="flex items-center">
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                className="flex-1"
              />
              {password && (
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="ml-2"
                  style={{ background: "none", border: "none", cursor: "pointer", padding: "0.5rem" }}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              )}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div 
              className="error" 
              role="alert"
              style={{
                padding: "0.75rem",
                backgroundColor: "#fee2e2",
                border: "1px solid #fecaca",
                borderRadius: "0.375rem",
                color: "#dc2626",
                fontSize: "0.875rem"
              }}
            >
              {error}
            </div>
          )}
        </div>

        <button 
          className="btn btn--primary" 
          type="submit"
          style={{ marginTop: "1.5rem" }}
        >
          Sign In
        </button>

        <p className="hint" style={{ marginTop: "1rem", textAlign: "center" }}>
          Please contact your administrator if you need assistance
        </p>
      </form>
    </div>
  );
};
