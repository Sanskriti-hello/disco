import React, { useState } from "react";
import data from "./data.json";
import "./styles.css";

export default function App() {
  const [activeLabel, setActiveLabel] = useState(0);
  const [search, setSearch] = useState("");

  return (
    <div className="page">
      <header className="topbar">
        <h1 className="title">STUDY</h1>

        <div className="header-buttons">
          <button type="button" className="header-btn home-btn">⌂</button>
          <button type="button" className="header-btn user-btn">👤</button>
          <button type="button" className="header-btn info-btn">⚙</button>
        </div>
      </header>

      <div className="main-container">
        <section className="left-section">
          <div className="summary-box">
            <h2 className="summary-title">Summary</h2>
            <p className="summary-text">text</p>
          </div>
        </section>

        <section className="right-section">
          <div className="search-bar">
            <span className="search-icon">☰</span>

            <input
              type="text"
              placeholder="Hinted search text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />

            <span className="search-btn">🔍</span>
          </div>

          <div className="label-buttons">
            {data.labels.map((label, idx) => (
              <button
                key={label}
                type="button"
                className={`label-btn ${activeLabel === idx ? "active" : ""}`}
                onClick={() => setActiveLabel(idx)}
              >
                {activeLabel === idx ? "✓ " : ""}
                {label}
              </button>
            ))}
          </div>

          <div className="shapes-box">
            <div className="shape-item">△</div>
            <div className="shape-item">⚙</div>
            <div className="shape-item">◻</div>

            <p className="shapes-label">
              Label&nbsp;&nbsp;Label&nbsp;&nbsp;Label
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
