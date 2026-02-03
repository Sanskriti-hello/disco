import React from 'react';
import data from './data.json';

export default function App() {
  return (
    <div className="page">
      <header className="topbar">
        <h1 className="title">{data.header.title}</h1>
        <div className="search-bar">
          <span className="menu-icon">≡</span>
          <input type="text" placeholder={data.header.searchPlaceholder} />
          <button className="search-btn">{data.header.searchIcon}</button>
        </div>
        <nav className="nav-icons">{data.header.navIcons}</nav>
      </header>

      <div className="container">
        <section className="left-section">
          <div className="summary-box">
            <h2>{data.main.summary.title}</h2>
            <p>{data.main.summary.text}</p>
          </div>
          <div className="boxes-row">
            {data.main.boxes.map((_, idx) => (
              <div className="white-box" key={idx} />
            ))}
          </div>
        </section>

        <aside className="links-section">
          <h3 className="links-title">{data.sidebar.title}</h3>
          {data.sidebar.links.map((link) => (
            <div className="link-item" key={link.id}>
              {link.text}
            </div>
          ))}
        </aside>
      </div>
    </div>
  );
}
