(function () {
  const clone = document.body.cloneNode(true);

  // Remove junk elements
  const junkSelectors = [
    'script', 'style', 'noscript', 'iframe',
    'header', 'footer', 'nav',
    '.ad', '.advertisement', '.cookie-banner',
    '#sidebar', '.comments'
  ];

  junkSelectors.forEach(selector => {
    clone.querySelectorAll(selector).forEach(el => el.remove());
  });

  const paragraphs = Array.from(clone.querySelectorAll('p'))
    .map(p => p.innerText.trim())
    .filter(text => text.length > 20)
    .slice(0, 10);

  const links = Array.from(clone.querySelectorAll('a[href]'))
    .map(a => ({ text: a.innerText.trim(), url: a.href }))
    .filter(l => l.text && l.url)
    .slice(0, 20);

  const images = Array.from(clone.querySelectorAll('img[src]'))
    .map(img => ({ src: img.src, alt: img.alt || '' }))
    .slice(0, 10);

  const headings = Array.from(clone.querySelectorAll('h1, h2, h3'))
    .map(h => h.innerText.trim())
    .filter(Boolean)
    .slice(0, 5);

  const plainText = clone.innerText
    .replace(/\s+/g, ' ')
    .trim()
    .substring(0, 2000);

  return {
    url: window.location.href,
    title: document.title,
    content: plainText,
    structured: {
      paragraphs,
      links,
      images,
      headings
    }
  };
})();