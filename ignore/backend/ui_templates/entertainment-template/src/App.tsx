import React from 'react';
import data from './data.json';

export default function App() {
  return (
    <div className="page">
      <header className="topbar">
        <h1 className="title">ENTERTAINMENT</h1>
        <nav className="nav-icons">🏠 👤 ⓘ</nav>
      </header>

      <div className="container">
        <section className="left-column">
          <div className="large-box" />
          <p className="box-label">More Like This</p>
        </section>

        <section className="right-column">
          <div className="top-right-box">
            <p className="mini-text">cat</p>
          </div>
          <div className="bottom-right-group">
            <div className="text-box">
              <p>Text</p>
            </div>
            <div className="small-box" />
          </div>
        </section>
      </div>

      <section className="carousel-section">
        <button className="carousel-btn left">‹</button>
        <div className="carousel">
          {data.items.map((_, idx) => (
            <div className="carousel-item" key={idx} />
          ))}
        </div>
        <button className="carousel-btn right">›</button>
      </section>

      <div className="action-bar">
        <button className="action-btn">Button</button>
        <button className="action-btn primary">Button</button>
        <button className="icon-btn">📌</button>
        <button className="icon-btn">♡</button>
      </div>
    </div>
  );
}
