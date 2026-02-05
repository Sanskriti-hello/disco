import React, { useState } from "react";
import data from "./data.json";
import "./styles.css";

export default function App() {
  const [activeLabel, setActiveLabel] = useState(0);
  const [search, setSearch] = useState("");

  return (
    <div className="page">
      <header className="topbar">
        <h1 className="title">{data.header.title}</h1>

        <div className="header-buttons">
          <button type="button" className="header-btn home-btn">{data.header.homeIcon}</button>
          <button type="button" className="header-btn user-btn">{data.header.userIcon}</button>
          <button type="button" className="header-btn info-btn">{data.header.settingsIcon}</button>
        </div>
      </header>

      <div className="main-container">
        <section className="left-section">
          <div className="summary-box">
            <h2 className="summary-title">{data.main.summary.title}</h2>
            <p className="summary-text">{data.main.summary.text}</p>
          </div>
        </section>

        <section className="right-section">
          <div className="search-bar">
            <span className="search-icon">{data.main.search.menuIcon}</span>

            <input
              type="text"
              placeholder={data.main.search.placeholder}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />

            <span className="search-btn">{data.main.search.searchIcon}</span>
          </div>

          <div className="label-buttons">
            {data.main.labels.items.map((label, idx) => (
              <button
                key={label}
                type="button"
                className={`label-btn ${activeLabel === idx ? "active" : ""}`}
                onClick={() => setActiveLabel(idx)}
              >
                {activeLabel === idx ? `${data.main.labels.activeIcon} ` : ""}
                {label}
              </button>
            ))}
          </div>

          <div className="shapes-box">
            {data.main.shapes.items.map((shape, idx) => (
              <div key={idx} className="shape-item">{shape}</div>
            ))}

            <p className="shapes-label">
              {data.main.shapes.items.map(() => `${data.main.shapes.label}\u00A0\u00A0`).join('')}
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
