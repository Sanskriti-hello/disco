"""
Template Renderer (DEV PREVIEW)
Safe version: avoids f-string JSX parsing issues
Renderer lives inside ui_templates/study-1
"""

from typing import Dict, Any
from pathlib import Path
import json


class TemplateRenderer:
    def __init__(self):
        # renderer.py is inside ui_templates/study-1
        self.template_dir = Path(__file__).parent

    async def render(
        self,
        data: Dict[str, Any],
        domain: str = "study"
    ) -> str:
        """
        Render the local study-1 template
        """

        entry = self.template_dir / "index.tsx"

        if not entry.exists():
            raise FileNotFoundError(
                f"index.tsx not found at {entry}"
            )

        # Read TSX
        tsx_code = entry.read_text(encoding="utf-8")

        # Babel inline cannot handle `export default`
        tsx_code = tsx_code.replace(
            "export default function StudyTemplate",
            "function StudyTemplate"
        )

        props_json = json.dumps(data, indent=2)

        html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>STUDY TEMPLATE PREVIEW</title>

  <!-- React -->
  <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>

  <!-- Babel -->
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

  <!-- Tailwind (CDN, dev only) -->
  <script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-gray-100">
  <div id="root"></div>

  <script type="text/babel" data-presets="react,typescript">
    console.log("✅ Babel script started");

    // ---------- TEMPLATE CODE ----------
    __TSX_CODE__
    // ---------- END TEMPLATE CODE ----------

    const props = __PROPS_JSON__;
    console.log("📥 Props:", props);

    const rootEl = document.getElementById("root");
    console.log("📦 Root element:", rootEl);

    const root = ReactDOM.createRoot(rootEl);
    console.log("🚀 Rendering StudyTemplate");

    root.render(
      React.createElement(StudyTemplate, props)
    );
  </script>
</body>
</html>
"""

        html = html.replace("__TSX_CODE__", tsx_code)
        html = html.replace("__PROPS_JSON__", props_json)

        return html
