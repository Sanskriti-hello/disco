import React from "react";

const Frame22 = (props) => {
  const { 
    title = "Code Assistant", 
    code_snippets = [], 
    documentation = [], 
    terminal_output = "Terminal output goes here..." 
  } = props;

  const mainSnippet = code_snippets[0] || { filename: "welcome.py", code: "# No code found in your tabs\n# Open some code-related pages to see snippets here" };

  return (
    <div className="dashboard-grid">
      <aside className="sidebar">
        <h2>Documentation</h2>
        <div className="sidebar-links">
          {documentation.length > 0 ? (
            documentation.map((doc, index) => (
              <a key={index} href={doc.url} target="_blank" rel="noopener noreferrer">
                {doc.title}
              </a>
            ))
          ) : (
            <p>No documentation links found.</p>
          )}
        </div>
      </aside>

      <main className="main-content">
        <h1>{title}</h1>
        
        <div className="code-display">
          <div className="filename">{mainSnippet.filename}</div>
          <pre><code>{mainSnippet.code}</code></pre>
        </div>
        
        <h2>Terminal Output</h2>
        <div className="terminal-output">
          <pre>{terminal_output}</pre>
        </div>
      </main>
    </div>
  );
};

export default Frame22;

