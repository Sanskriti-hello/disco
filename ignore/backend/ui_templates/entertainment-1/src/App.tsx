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

      <div className="container">
        <section className="left-column">
          {/* Show featured movie poster in large box */}
          <div className="large-box" style={{
            backgroundImage: data.rightColumn?.featured?.imageUrl
              ? `linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.7)), url(${data.rightColumn.featured.imageUrl})`
              : 'none',
            backgroundSize: 'cover',
            backgroundPosition: 'center'
          }}>
            {data.rightColumn?.featured && (
              <div className="featured-overlay">
                <h2>{data.rightColumn.featured.title}</h2>
                <p>{data.rightColumn.featured.description}</p>
                {data.rightColumn.featured.genre && (
                  <span className="genre-badge">{data.rightColumn.featured.genre}</span>
                )}
              </div>
            )}
          </div>
          <p className="box-label">{data.leftColumn.label}</p>
          {/* Display left column items */}
          <div className="left-items">
            {data.leftColumn.items.map((item: any) => (
              <div key={item.id} className="left-item">
                <img src={item.imageUrl} alt={item.title} className="item-thumb" />
                <a href={item.url} target="_blank" rel="noopener noreferrer">
                  {item.title}
                </a>
              </div>
            ))}
          </div>
        </section>

        <section className="right-column">
          {/* Top box with summary text */}
          <div className="top-right-box">
            <div className="summary-content">
              <p className="mini-text">{data.rightColumn.topBox}</p>
              {data.rightColumn?.featured?.year && (
                <span className="year-badge">{data.rightColumn.featured.year}</span>
              )}
            </div>
          </div>
          <div className="bottom-right-group">
            {/* Text box with page summary */}
            <div className="text-box">
              <p>{data.rightColumn.textBox}</p>
            </div>
            {/* Small box with first movie poster */}
            <div className="small-box" style={{
              backgroundImage: data.items?.[0]?.imageUrl
                ? `url(${data.items[0].imageUrl})`
                : 'none',
              backgroundSize: 'cover',
              backgroundPosition: 'center'
            }}>
              {data.items?.[0] && (
                <div className="small-box-overlay">
                  <span>{data.items[0].title}</span>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>

      <section className="carousel-section">
        <button className="carousel-btn left">‹</button>
        <div className="carousel">
          {data.items.map((item: any) => (
            <div className="carousel-item" key={item.id}>
              <img src={item.imageUrl} alt={item.title} className="carousel-img" />
              <div className="carousel-info">
                <h3>{item.title}</h3>
                {item.rating > 0 && <span className="rating">⭐ {item.rating}</span>}
                <a href={item.url} target="_blank" rel="noopener noreferrer" className="view-link">
                  View Details
                </a>
              </div>
            </div>
          ))}
        </div>
        <button className="carousel-btn right">›</button>
      </section>

      <div className="action-bar">
        {data.actionBar.buttons.map((btn: any) => (
          <a
            key={btn.id}
            href={btn.url}
            target="_blank"
            rel="noopener noreferrer"
            className={`action-btn ${btn.primary ? 'primary' : ''}`}
          >
            {btn.label}
          </a>
        ))}
        {data.actionBar.icons.map((icon: any) => (
          <button key={icon.id} className="icon-btn">
            {icon.icon}
          </button>
        ))}
      </div>
    </div>
  );
}
