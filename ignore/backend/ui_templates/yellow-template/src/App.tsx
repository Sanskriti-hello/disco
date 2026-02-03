import React from 'react';
import data from './data.json';

export default function App() {
  return (
    <div className="page">
      <header className="topbar">
        <h1 className="title">TITLE</h1>
        <div className="search-bar">
          <span className="menu-icon">≡</span>
          <input type="text" placeholder="Hinted search text" />
          <button className="search-btn">🔍</button>
        </div>
        <nav className="nav-icons">🏠 👤 ⓘ</nav>
      </header>

      <div className="container">
        <section className="left-section">
          <div className="summary-box">
            <h2>SUMMARY</h2>
            <p>TEXT</p>
          </div>
          <div className="boxes-row">
            {data.boxes.map((_, idx) => (
              <div className="white-box" key={idx} />
            ))}
          </div>
        </section>

        <aside className="links-section">
          <h3 className="links-title">LINKS TO VISIT</h3>
          {data.links.map((link) => (
            <div className="link-item" key={link.id}>
              {link.text}
            </div>
          ))}
        </aside>
      </div>
    </div>
  );
}
