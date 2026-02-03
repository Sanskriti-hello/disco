import React from 'react';
import data from './data.json';

export default function App() {
  return (
    <div className="page">
      <header className="topbar">
        <h1 className="main-title">CODE</h1>
        <nav className="nav-icons">🏠 👤 ⓘ</nav>
      </header>

      <div className="main-wrapper">
        <aside className="sidebar">
          <p className="frame-label">Frame 25</p>
          <div className="search-box">
            <span className="menu-icon">≡</span>
            <input type="text" placeholder="Hinted search text" />
            <button className="search-btn">🔍</button>
          </div>
          <div className="sidebar-content-box">
            <p className="box-text">TEXT</p>
          </div>
        </aside>

        <main className="main-content">
          <div className="top-box">
            <p className="box-text">TEXT CONTENT</p>
          </div>
          <div className="bottom-box">
            <p className="box-text">TEXT</p>
          </div>
        </main>
      </div>
    </div>
  );
}
