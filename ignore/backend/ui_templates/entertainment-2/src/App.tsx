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
        <nav className="nav-icons">{data.header.navIcons}</nav>
      </header>

      <div className="main-container">
        <section className="left-section">
          <div className="calendar-widget">
            <div className="calendar-header">
              <span>&lt;</span>
              <span>{data.calendar.month}</span>
              <span>{data.calendar.year}</span>
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
                <div key={i} className={`calendar-date ${data.calendar.activeDates.includes(i + 1) ? 'active' : ''}`}>
                  {i + 1}
                </div>
              ))}
            </div>
          </div>
          <div className="button-group">
            {data.buttons.map((btn) => (
              <button key={btn.id}>{btn.label}</button>
            ))}
          </div>
          <div className="search-box">
            <span className="menu-icon">≡</span>
            <input type="text" placeholder={data.searchPlaceholder} />
            <button className="search-btn">🔍</button>
          </div>
          <p className="more-label">{data.leftSectionLabel}</p>
        </section>

        <section className="center-section">
          <div className="title-box">
            <h3>{data.centerSection.titleBox.title}</h3>
            <p>{data.centerSection.titleBox.body}</p>
          </div>
          <div className="watch-section">
            <h3>{data.centerSection.watchSection}</h3>
          </div>
        </section>

        <aside className="right-section">
          <div className="menu-widget">
            <h3 className="menu-heading">{data.rightSection.heading}</h3>
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
        <p className="carousel-label">{data.leftSectionLabel}</p>
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
