"""
Update all UI templates to read from window.__DASHBOARD_DATA__
This makes them work with runtime data injection while maintaining local development compatibility.
"""

import os
from pathlib import Path

# Template directories
TEMPLATES_DIR = Path(__file__).parent.parent / "ui_templates"

# Templates to update
TEMPLATES = [
    "code-1",
    "entertainment-1",
    "entertainment-2",
    "generic-1",
    "generic-2",
    "study-1",
    "travel-1",
    "travel-2"
]

def update_template(template_name):
    """Update a single template's App.tsx"""
    app_file = TEMPLATES_DIR / template_name / "src" / "App.tsx"
    
    if not app_file.exists():
        print(f"⏭️ Skipping {template_name} - App.tsx not found")
        return False
    
    # Read current content
    content = app_file.read_text(encoding='utf-8')
    
    # Check if already updated
    if "window.__DASHBOARD_DATA__" in content or "__DASHBOARD_DATA__" in content:
        print(f"✅ {template_name} - Already updated")
        return True
    
    # Check if it imports data.json
    if "import data from './data.json'" not in content and 'import data from "./data.json"' not in content:
        print(f"⚠️ {template_name} - No data.json import found, skipping")
        return False
    
    # Replace the import
    updated = content.replace(
        "import data from './data.json';",
        """import fallbackData from './data.json';

// ✅ Read from runtime-injected data (populated by backend)
// Falls back to imported data.json for local development
const data = (window as any).__DASHBOARD_DATA__ || fallbackData;"""
    )
    
    # Also handle double quotes
    updated = updated.replace(
        'import data from "./data.json";',
        """import fallbackData from "./data.json";

// ✅ Read from runtime-injected data (populated by backend)
// Falls back to imported data.json for local development
const data = (window as any).__DASHBOARD_DATA__ || fallbackData;"""
    )
    
    # Write back
    app_file.write_text(updated, encoding='utf-8')
    print(f"✅ {template_name} - Updated successfully")
    return True

def main():
    print("🔧 Updating all UI templates to use window.__DASHBOARD_DATA__\n")
    
    updated = 0
    skipped = 0
    
    for template in TEMPLATES:
        if update_template(template):
            updated += 1
        else:
            skipped += 1
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Updated: {updated}")
    print(f"   ⏭️ Skipped: {skipped}")
    print(f"\n🎉 All templates are now runtime-data compatible!")

if __name__ == "__main__":
    main()
