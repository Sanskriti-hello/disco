import React, { useState } from 'react';
import fallbackData from './data.json';

// ✅ Read from runtime-injected data (populated by backend)
// Falls back to imported data.json for local development
const data = (window as any).__DASHBOARD_DATA__ || fallbackData;
import './styles.css';

export default function App() {
  const [expanded, setExpanded] = useState<{ [key: number]: boolean }>({});

  const toggleExpand = (idx: number) => {
    setExpanded(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div className="page">
      <header className="topbar">
        <h1 className="title">{data.header.title}</h1>
        <div className="map-decoration"></div>
        <div className="header-buttons">
          <button className="header-btn home-btn">{data.header.homeIcon}</button>
          <button className="header-btn user-btn">{data.header.userIcon}</button>
          <button className="header-btn info-btn">{data.header.infoIcon}</button>
        </div>
      </header>

      <div className="photos-section">
        <div className="photos-container">
          {data.photos.items.map((photo, idx) => (
            <div className="photo-box" key={idx}>
              <div className="photo-placeholder"></div>
              <p>{data.photos.description}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="input-bar">
        <button className="back-btn">{data.inputBar.backIcon}</button>
        <input type="text" placeholder={data.inputBar.placeholder} />
        <button className="close-btn">{data.inputBar.closeIcon}</button>
      </div>

      <div className="main-container">
        <section className="left-column">
          <div className="calendar-widget">
            <div className="calendar-header">
              <button>{data.main.calendar.prev}</button>
              <select>
                <option>{data.main.calendar.month}</option>
              </select>
              <select>
                <option>{data.main.calendar.year}</option>
              </select>
              <button>{data.main.calendar.next}</button>
            </div>
            <div className="calendar-grid">
              {data.main.calendar.days.map((day) => (
                <div key={day}>{day}</div>
              ))}
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
            <h3 className="menu-heading">{data.main.menu.heading}</h3>
            <p className="menu-subheading">{data.main.menu.subheading}</p>
            {data.main.menu.items.map((item, idx) => (
              <div className="menu-item" key={idx}>
                <span className="menu-icon">{data.main.menu.icon}</span>
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
            {data.main.accordion.items.map((item, idx) => {
              const isFirst = idx === 0;
              const isExpanded = expanded[0] !== false || isFirst;
              return (
                <div key={idx}>
                  {isFirst && isExpanded && (
                    <div className="accordion-expanded">
                      <h3 className="accordion-title">{item.title}</h3>
                      <p className="accordion-text">{item.content}</p>
                      <button className="accordion-expand-btn" onClick={() => setExpanded({0: false})}>{data.main.accordion.arrowIcon}</button>
                    </div>
                  )}
                  <button
                    className="accordion-collapsed-item"
                    onClick={() => setExpanded({0: isFirst && isExpanded})}
                  >
                    <span>{item.title}</span>
                    <span className="accordion-arrow">{data.main.accordion.arrowIcon}</span>
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
