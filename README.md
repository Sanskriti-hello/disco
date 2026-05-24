# 🕺 Disco: AI-Powered Browser Dashboard

Disco is a next-generation browser dashboard that transforms your "New Tab" page into a dynamic, context-aware workspace. It uses advanced AI to analyze your browsing context and user prompts, generating personalized dashboards tailored to your current task—whether it's shopping, traveling, studying, or coding.

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🌟 Key Features

-   **🧠 Intelligent Context Awareness:** Automatically analyzes your open tabs to understand what you're working on.
-   **🎨 Domain-Specific Dashboards:** Custom-tailored UI layouts for:
    -   **Shopping:** Track prices and find similar products.
    -   **Travel:** Itinerary management and local weather/discovery.
    -   **Study:** Flashcards, quizzes, and Arxiv research.
    -   **Entertainment:** Spotify playlists and YouTube recommendations.
    -   **Coding:** Documentation search and repository insights.
-   **🛠️ Deep Integrations (MCP Tools):** Seamlessly connects to Google Workspace, Amazon, Spotify, YouTube, Arxiv, and more.
-   **⚡ High Performance:** Fast response times using efficient LLM routing (Groq/Gemini) and specialized tool execution.
-   **🔌 Seamless Extension:** Replaces your standard New Tab page with a beautiful, functional cockpit.

---

## 🏗️ Architecture

Disco is built with a decoupled architecture for maximum flexibility and performance:

1.  **Browser Extension (React/TypeScript):** The user interface. It captures tab metadata and user prompts, sending them to the backend.
2.  **Backend API (Python/FastAPI):** The orchestration layer.
3.  **LangGraph Pipeline:** A state-aware workflow that:
    -   Identifies the primary domain of interest.
    -   Selects the appropriate UI template.
    -   Triggers relevant **MCP (Model Context Protocol) Tools** to fetch real-time data.
    -   Normalizes the payload for the frontend.
4.  **UI Templates:** Pre-designed React components that render the dynamic data into beautiful widgets.

---

## 🛠️ Tech Stack

### Backend
-   **Language:** Python 3.10+
-   **Framework:** FastAPI
-   **Orchestration:** LangGraph
-   **AI Models:** Groq (Llama 3), Google Gemini
-   **Tools:** Tavily Search, SerpApi, Arxiv API, Google OAuth2, Spotify API

### Frontend (Extension)
-   **Framework:** React 19
-   **Language:** TypeScript
-   **Styling:** Tailwind CSS 4
-   **Bundler:** Vite
-   **State Management:** React Hooks

---

## 🧠 How it Works

Disco uses a sophisticated multi-stage pipeline to generate its dashboards:

1.  **Context Extraction:** The browser extension uses a `content_extractor.js` script to pull metadata and visible text from your open tabs.
2.  **Domain Routing:** The backend uses an `LLMRouter` (powered by Llama 3 or Gemini) to classify your current activity into domains like `Shopping`, `Travel`, `Study`, etc.
3.  **Dynamic Graph Execution:** Disco employs **LangGraph** to manage the data-fetching workflow. The graph determines which tools are needed based on the identified domain and user prompt.
4.  **MCP Integration:** Disco utilizes the **Model Context Protocol (MCP)** via `FastMCP` to interact with external services. For example, if you're in the `Travel` domain, it might trigger the `Loc_Weath_Dis` tool to get weather and local attractions.
5.  **Payload Normalization:** All fetched data is funneled through a strict Pydantic schema (`dashboard_schema.py`) to ensure the frontend receives a predictable and valid data structure.
6.  **Template Filling:** Finally, a `TemplateLoader` selects a pre-built React template and injects the normalized data, which is then sent back to the extension for rendering.

---

## 🚀 Getting Started

### Prerequisites
-   Python 3.10+
-   Node.js 18+
-   NPM or Yarn

### 1. Backend Setup
```bash
cd ignore/backend
# Install core dependencies
pip install fastapi uvicorn langgraph python-dotenv pydantic google-generativeai requests fastmcp httpx groq
cp .env.example .env
# Configure your API keys in .env (GROQ_API_KEY, GEMINI_API_KEY, etc.)
python main.py
```

### 2. Extension Setup
```bash
cd ignore/extension
npm install
npm run build
```
#### To install in Chrome:
1.  Open Chrome and go to `chrome://extensions/`.
2.  Enable **Developer mode** in the top right.
3.  Click **Load unpacked**.
4.  Select the `ignore/extension/dist` folder.

## 🛠️ Available Tools (MCP Integrations)

Disco's power comes from its extensive set of Model Context Protocol (MCP) integrations:

-   **🛍️ Amazon:** Search and track products.
-   **📚 Arxiv:** Query academic papers and research.
-   **📅 Google Workspace:** Access Calendar, Drive, Gmail, and Docs.
-   **🎵 Spotify:** Search tracks and manage playlists.
-   **📺 YouTube:** Search videos and get recommendations.
-   **📰 News:** Fetch real-time news updates.
-   **🔍 Search:** Integrated web search via Tavily and SerpApi.
-   **🌤️ Weather & Location:** Get local insights and forecasts.
-   **💱 Exchange Rates:** Real-time currency conversion.
-   **🧠 Study Tools:** Flashcard generation and interactive quizzes.

---

## 📁 Project Structure

```text
.
├── ignore/
│   ├── backend/             # Python FastAPI backend
│   │   ├── langraph/        # Pipeline orchestration logic
│   │   ├── mcp_tools/       # Data fetching integrations
│   │   ├── sandbox_builders/# Payload generation logic
│   │   ├── schemas/         # Data validation & normalization
│   │   └── ui_templates/    # Domain-specific UI definitions
│   └── extension/           # React-based browser extension
│       ├── src/             # Frontend source code
│       ├── public/          # Static assets
│       └── vite.config.ts   # Build configuration
└── README.md
```

---

## 🤝 Contributing

We welcome contributions! Please feel free to submit Pull Requests or open Issues.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
