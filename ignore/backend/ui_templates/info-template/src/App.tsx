import React from 'react';
import data from './data.json';

export default function App() {
  return (
    <div className="page">
      <header className="topbar">
        <h1 className="title">TITLE</h1>
        <div className="search-box">
          <input type="text" placeholder="Hinted search text" />
          <button className="search-btn">🔍</button>
        </div>
        <nav className="nav-icons">🏠 👤 ⓘ</nav>
      </header>

      <main className="container">
        <section className="left-col">
          <div className="summary-box">
            <h2>SUMMARY</h2>
            <p>TEXT</p>
          </div>
          <div className="boxes-grid">
            {data.boxes.map((_, idx) => (
              <div className="box" key={idx} />
            ))}
          </div>
        </section>

        <aside className="right-col">
          <div className="links-box">
            <h3>LINKS TO VISIT</h3>
            {data.links.map((link) => (
              <div className="link-item" key={link.id}>
                {link.text}
              </div>
            ))}
          </div>
        </aside>
      </main>
    </div>
  );
}
