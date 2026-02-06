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
        <div className="search-box">
          <input type="text" placeholder={data.header.searchPlaceholder} />
          <button className="search-btn">🔍</button>
        </div>
        <nav className="nav-icons">{data.header.navIcons}</nav>
      </header>

      <main className="container">
        <section className="left-col">
          <div className="summary-box">
            <h2>{data.leftColumn.summaryTitle}</h2>
            <p>{data.leftColumn.summaryText}</p>
          </div>
          <div className="boxes-grid">
            {data.boxes.map((_, idx) => (
              <div className="box" key={idx} />
            ))}
          </div>
        </section>

        <aside className="right-col">
          <div className="links-box">
            <h3>{data.rightColumn.linksTitle}</h3>
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
