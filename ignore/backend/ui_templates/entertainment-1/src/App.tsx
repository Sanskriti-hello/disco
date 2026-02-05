import React from 'react';
import data from './data.json';

export default function App() {
  return (
    <div className="page">
      <header className="topbar">
        <h1 className="title">{data.header.title}</h1>
        <nav className="nav-icons">{data.header.navIcons}</nav>
      </header>

      <div className="container">
        <section className="left-column">
          <div className="large-box" />
          <p className="box-label">{data.leftColumn.label}</p>
        </section>

        <section className="right-column">
          <div className="top-right-box">
            <p className="mini-text">{data.rightColumn.topBox}</p>
          </div>
          <div className="bottom-right-group">
            <div className="text-box">
              <p>{data.rightColumn.textBox}</p>
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
        {data.actionBar.buttons.map((btn) => (
          <button key={btn.id} className={`action-btn ${btn.primary ? 'primary' : ''}`}>
            {btn.label}
          </button>
        ))}
        {data.actionBar.icons.map((icon) => (
          <button key={icon.id} className="icon-btn">
            {icon.icon}
          </button>
        ))}
      </div>
    </div>
  );
}
