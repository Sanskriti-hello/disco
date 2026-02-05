import React from 'react';
import data from './data.json';

export default function App() {
  return (
    <div className="page">
      <header className="topbar">
        <h1 className="main-title">{data.header.title}</h1>
        <nav className="nav-icons">{data.header.navIcons}</nav>
      </header>

      <div className="main-wrapper">
        <aside className="sidebar">
          <p className="frame-label">{data.sidebar.frameLabel}</p>
          <div className="search-box">
            <span className="menu-icon">≡</span>
            <input type="text" placeholder={data.sidebar.searchPlaceholder} />
            <button className="search-btn">🔍</button>
          </div>
          <div className="sidebar-content-box">
            <p className="box-text">{data.sidebar.content}</p>
          </div>
        </aside>

        <main className="main-content">
          <div className="top-box">
            <p className="box-text">{data.mainContent.topBox}</p>
          </div>
          <div className="bottom-box">
            <p className="box-text">{data.mainContent.bottomBox}</p>
          </div>
        </main>
      </div>
    </div>
  );
}
