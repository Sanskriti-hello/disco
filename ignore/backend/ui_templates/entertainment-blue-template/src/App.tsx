import React from 'react';
import data from './data.json';

export default function App() {
  return (
    <div className="page">
      <header className="topbar">
        <h1 className="title">ENTERTAINMENT</h1>
        <nav className="nav-icons">🏠 👤 ⓘ</nav>
      </header>

      <div className="main-container">
        <section className="left-section">
          <div className="calendar-widget">
            <div className="calendar-header">
              <span>&lt;</span>
              <span>Sep</span>
              <span>2025</span>
              <span>&gt;</span>
            </div>
            <div className="calendar-grid">
              <div className="calendar-day">Su</div>
              <div className="calendar-day">Mo</div>
              <div className="calendar-day">Tu</div>
              <div className="calendar-day">We</div>
              <div className="calendar-day">Th</div>
              <div className="calendar-day">Fr</div>
              <div className="calendar-day">Sa</div>
              {Array.from({ length: 30 }).map((_, i) => (
                <div key={i} className={`calendar-date ${i === 9 || i === 19 ? 'active' : ''}`}>
                  {i + 1}
                </div>
              ))}
            </div>
          </div>
          <div className="button-group">
            <button>Button</button>
            <button>Button</button>
          </div>
          <div className="search-box">
            <span className="menu-icon">≡</span>
            <input type="text" placeholder="Hinted search text" />
            <button className="search-btn">🔍</button>
          </div>
          <p className="more-label">More Like This</p>
        </section>

        <section className="center-section">
          <div className="title-box">
            <h3>Title</h3>
            <p>Body text</p>
          </div>
          <div className="watch-section">
            <h3>WHERE TO WATCH</h3>
          </div>
        </section>

        <aside className="right-section">
          <div className="menu-widget">
            <h3 className="menu-heading">Heading</h3>
            {data.menuItems.map((item) => (
              <div className="menu-item" key={item.id}>
                <span className="menu-icon">★</span>
                <span className="menu-label">{item.label}</span>
                <span className="menu-shortcut">{item.shortcut}</span>
              </div>
            ))}
          </div>
        </aside>
      </div>

      <section className="carousel-section">
        <p className="carousel-label">More Like This</p>
        <div className="carousel-container">
          <button className="carousel-btn">‹</button>
          <div className="carousel">
            {data.items.map((_, idx) => (
              <div className="carousel-item" key={idx} />
            ))}
          </div>
          <button className="carousel-btn">›</button>
        </div>
      </section>
    </div>
  );
}
