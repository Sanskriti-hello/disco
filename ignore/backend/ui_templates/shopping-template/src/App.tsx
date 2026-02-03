import React from 'react';
import data from './data.json';

export default function App() {
  return (
    <div className="page">
      <header className="topbar">
        <h1 className="brand">SHOPPING</h1>
        <nav className="icons">🏠 👤 ⓘ</nav>
      </header>

      <main className="container">
        <section className="left-quote">
          <div className="quote-box">“Quote"</div>
        </section>

        <section className="product-highlight">
          <div className="product-card">
            <h2>Product name</h2>
            <p>Text</p>
          </div>
          <div className="fav">♡</div>
        </section>

        <section className="carousel">
          <div className="carousel-inner">
            {data.items.map((it) => (
              <div className="item" key={it.id}>
                <div className="thumb" />
                <div className="item-title">{it.title}</div>
                <button className="btn">TEXT</button>
              </div>
            ))}
          </div>
        </section>

        <section className="reviews">
          {data.reviews.map((r) => (
            <div className="rev" key={r.id}>
              <div className="avatar" />
              <div className="meta">
                <div className="rev-title">{r.title}</div>
                <div className="stars">{Array(r.stars).fill('★')}</div>
                <p className="rev-text">{r.text}</p>
              </div>
            </div>
          ))}
        </section>

        <section className="footer-area">
          <div className="big-box" />
        </section>
      </main>
    </div>
  );
}
