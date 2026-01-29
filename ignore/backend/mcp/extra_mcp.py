{
  "inputs": [
    {
      "type": "promptString",
      "id": "brave_api_key",
      "description": "Brave Search API Key",
      "password": true
    }
  ],
  "servers": {
    "figma": {
      "url": "https://mcp.figma.com/mcp",
      "type": "http"
    },
    "brave-search": {
      "command": "npx",
      "args": [
        "-y",
        "@brave/brave-search-mcp-server",
        "--transport",
        "http"
      ],
      "env": {
        "BRAVE_API_KEY": "${input:brave_api_key}"
      }
    },
    "tavily-remote": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp.tavily.com/mcp/?tavilyApiKey=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"
      ]
    },
    "arxiv-mcp-server": {
      "command": "C:\\Users\\Sanskriti Jain\\AppData\\Roaming\\Python\\Python314\\Scripts\\uv.exe",
      "args": [
        "tool",
        "run",
        "arxiv-mcp-server",
        "--storage-path",
        "backend/mcp/arxiv_papers"
      ]
    }
  }
}