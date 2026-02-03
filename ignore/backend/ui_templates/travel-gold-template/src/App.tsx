import React, { useState } from 'react';
import data from './data.json';
import './styles.css';

export default function App() {
  const [expanded, setExpanded] = useState<{ [key: number]: boolean }>({});

  const toggleExpand = (idx: number) => {
    setExpanded(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div className="page">
      <header className="topbar">
        <h1 className="title">Travel</h1>
        <div className="map-decoration"></div>
        <div className="header-buttons">
          <button className="header-btn home-btn">⌂</button>
          <button className="header-btn user-btn">👤</button>
          <button className="header-btn info-btn">ℹ</button>
        </div>
      </header>

      <div className="photos-section">
        <div className="photos-container">
          {data.photos.map((_, idx) => (
            <div className="photo-box" key={idx}>
              <div className="photo-placeholder"></div>
              <p>Photo desc</p>
            </div>
          ))}
        </div>
      </div>

      <div className="input-bar">
        <button className="back-btn">←</button>
        <input type="text" placeholder="Input text" />
        <button className="close-btn">✕</button>
      </div>

      <div className="main-container">
        <section className="left-column">
          <div className="calendar-widget">
            <div className="calendar-header">
              <button>&lt;</button>
              <select>
                <option>Sep</option>
              </select>
              <select>
                <option>2025</option>
              </select>
              <button>&gt;</button>
            </div>
            <div className="calendar-grid">
              <div>Su</div>
              <div>Mo</div>
              <div>Tu</div>
              <div>We</div>
              <div>Th</div>
              <div>Fr</div>
              <div>Sa</div>
              {Array.from({ length: 30 }).map((_, i) => (
                <div key={i} className={`date ${i === 9 || i === 12 ? 'active' : ''}`}>
                  {i + 1}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="middle-column">
          <div className="menu-card">
            <h3 className="menu-heading">Heading</h3>
            <p className="menu-subheading">Heading</p>
            {data.menu.map((item, idx) => (
              <div className="menu-item" key={idx}>
                <span className="menu-icon">⭐</span>
                <div className="menu-text">
                  <p className="menu-label">{item.label}</p>
                  <p className="menu-description">{item.description}</p>
                </div>
                <span className="menu-shortcut">{item.shortcut}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="right-column">
          <div className="accordion-card">
            {data.accordion.map((item, idx) => {
              const isFirst = idx === 0;
              const isExpanded = expanded[0] !== false || isFirst;
              return (
                <div key={idx}>
                  {isFirst && isExpanded && (
                    <div className="accordion-expanded">
                      <h3 className="accordion-title">{item.title}</h3>
                      <p className="accordion-text">{item.content}</p>
                      <button className="accordion-expand-btn" onClick={() => setExpanded({0: false})}>^</button>
                    </div>
                  )}
                  <button
                    className="accordion-collapsed-item"
                    onClick={() => setExpanded({0: isFirst && isExpanded})}
                  >
                    <span>{item.title}</span>
                    <span className="accordion-arrow">^</span>
                  </button>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
