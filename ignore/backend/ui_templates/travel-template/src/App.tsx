import React from 'react';
import data from './data.json';

export default function App() {
  return (
    <div className="page">
      <header className="topbar">
        <h1 className="title">Travel</h1>
        <div className="header-buttons">
          <button className="header-btn home-btn">⌂</button>
          <button className="header-btn user-btn">👤</button>
          <button className="header-btn info-btn">ℹ</button>
        </div>
      </header>

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
                <div key={i} className={`date ${i === 13 || i === 19 ? 'active' : ''}`}>
                  {i + 1}
                </div>
              ))}
            </div>
          </div>
          <div className="text-box">
            <p>text</p>
          </div>
        </section>

        <section className="right-column">
          <div className="photos-grid">
            {data.photos.map((_, idx) => (
              <div className="photo-item" key={idx}>
                <p>Photo desc</p>
              </div>
            ))}
          </div>

          <div className="input-bar">
            <button className="back-btn">←</button>
            <input type="text" placeholder="Input text" />
            <button className="close-btn">✕</button>
          </div>

          <div className="content-box" />
        </section>
      </div>

      <nav className="bottom-nav">
        <div className="nav-item orange">✈</div>
        <div className="nav-item yellow">🏖</div>
        <div className="nav-item blue">🏨</div>
        <div className="nav-item green">🚗</div>
        <div className="nav-item red">🍽</div>
      </nav>
    </div>
  );
}
