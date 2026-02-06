import React from 'react';
import fallbackData from './data.json';

// ✅ Read from runtime-injected data (populated by backend)
// Falls back to imported data.json for local development
const data = (window as any).__DASHBOARD_DATA__ || fallbackData;

export default function App() {
  return (
    <div className="page">
      <header className="topbar">
        <h1 className="title">{data.header.title}</h1>
        <div className="header-buttons">
          <button className="header-btn home-btn">{data.header.homeIcon}</button>
          <button className="header-btn user-btn">{data.header.userIcon}</button>
          <button className="header-btn info-btn">{data.header.infoIcon}</button>
        </div>
      </header>

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
                <div key={i} className={`date ${i === 13 || i === 19 ? 'active' : ''}`}>
                  {i + 1}
                </div>
              ))}
            </div>
          </div>
          <div className="text-box">
            <p>{data.main.textBox.text}</p>
          </div>
        </section>

        <section className="right-column">
          <div className="photos-grid">
            {data.main.photos.map((photo, idx) => (
              <div className="photo-item" key={idx}>
                <p>{photo.description}</p>
              </div>
            ))}
          </div>

          <div className="input-bar">
            <button className="back-btn">{data.main.inputBar.backIcon}</button>
            <input type="text" placeholder={data.main.inputBar.placeholder} />
            <button className="close-btn">{data.main.inputBar.closeIcon}</button>
          </div>

          <div className="content-box" />
        </section>
      </div>

      <nav className="bottom-nav">
        {data.footer.nav.map((item, idx) => (
          <div className={`nav-item ${item.color}`} key={idx}>
            {item.icon}
          </div>
        ))}
      </nav>
    </div>
  );
}
