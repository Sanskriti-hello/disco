// dashboard.js - Script for dashboard.html
// Extracted to comply with Chrome Extension Content Security Policy (Manifest V3)

if (typeof chrome === 'undefined' || !chrome.storage) {
    console.error('Chrome extension APIs not available');
    showError();
} else {
    loadDashboard();
}

function loadDashboard() {
    chrome.storage.local.get(['dashboardConfig'], (result) => {
        if (chrome.runtime.lastError) {
            console.error('Storage error:', chrome.runtime.lastError);
            showError();
            return;
        }

        const config = result.dashboardConfig;

        if (!config || !config.success) {
            console.error('No valid dashboard config found');
            showError();
            return;
        }

        console.log('Dashboard config loaded:', config);

        // Hide loading
        document.getElementById('loading').style.display = 'none';

        // Option 1: Show CodeSandbox iframe (PREFERRED)
        if (config.sandbox_embed_url) {
            showCodeSandbox(config);
        }
        // Option 2: Fallback to custom rendering
        else {
            showFallbackDashboard(config);
        }
    });
}

function showCodeSandbox(config) {
    const container = document.getElementById('sandbox-container');
    container.style.display = 'block';

    const iframe = document.createElement('iframe');
    iframe.src = config.sandbox_embed_url;
    iframe.allow = "accelerometer; ambient-light-sensor; camera; encrypted-media; geolocation; gyroscope; hid; microphone; midi; payment; usb; vr; xr-spatial-tracking";
    iframe.sandbox = "allow-forms allow-modals allow-popups allow-presentation allow-same-origin allow-scripts";
    iframe.title = config.selected_template || "Dashboard";

    // Add loading handler
    iframe.onload = () => {
        console.log('CodeSandbox loaded successfully');
    };

    iframe.onerror = () => {
        console.error('CodeSandbox failed to load');
        container.style.display = 'none';
        showFallbackDashboard(config);
    };

    container.appendChild(iframe);
}

function showFallbackDashboard(config) {
    const dashboard = document.getElementById('fallback-dashboard');
    dashboard.style.display = 'block';

    // Set header info
    document.getElementById('domain-badge').textContent = config.domain || 'General';
    document.getElementById('template-name').textContent = config.selected_template || 'Dashboard';
    document.getElementById('template-desc').textContent = `Generated using ${config.domain || 'generic'} domain intelligence`;

    // Render data
    const dataContainer = document.getElementById('data-container');
    const uiProps = config.ui_props || {};

    // Try to find renderable data
    let items = [];

    // Study domain
    if (uiProps.papers && Array.isArray(uiProps.papers)) {
        items = uiProps.papers.map(p => ({
            title: p.title || 'Untitled Paper',
            description: p.summary || p.abstract || 'No description',
            url: p.pdf_url || p.url || '#'
        }));
    }
    // Shopping domain
    else if (uiProps.products && Array.isArray(uiProps.products)) {
        items = uiProps.products.map(p => ({
            title: p.title || p.name || 'Product',
            description: `Price: ${p.price || 'N/A'}`,
            url: p.url || '#'
        }));
    }
    // Travel domain
    else if (uiProps.flights && Array.isArray(uiProps.flights)) {
        items = uiProps.flights.map(f => ({
            title: f.airline || 'Flight',
            description: `${f.price || ''} - ${f.duration || ''}`,
            url: f.bookingUrl || '#'
        }));
    }
    // Code domain
    else if (uiProps.code_snippets && Array.isArray(uiProps.code_snippets)) {
        items = uiProps.code_snippets.map(c => ({
            title: c.language || 'Code',
            description: c.code?.substring(0, 200) + '...' || 'Code snippet',
            url: '#'
        }));
    }
    // Entertainment domain
    else if (uiProps.videos && Array.isArray(uiProps.videos)) {
        items = uiProps.videos.map(v => ({
            title: v.title || 'Video',
            description: v.description || v.snippet || '',
            url: v.url || '#'
        }));
    }
    // Generic fallback
    else {
        // Show raw JSON if no specific structure
        dataContainer.innerHTML = `
            <div style="grid-column: 1 / -1;">
                <h3 style="color: white; margin-bottom: 16px;">Dashboard Data:</h3>
                <div class="json-viewer">${JSON.stringify(uiProps, null, 2)}</div>
            </div>
        `;
        return;
    }

    // Render items as cards
    if (items.length === 0) {
        dataContainer.innerHTML = '<p style="color: #ffffff99;">No data to display</p>';
        return;
    }

    items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'data-card';
        card.innerHTML = `
            <h3>${escapeHtml(item.title)}</h3>
            <p>${escapeHtml(item.description)}</p>
            ${item.url && item.url !== '#' ? `<a href="${escapeHtml(item.url)}" target="_blank">View Details →</a>` : ''}
        `;
        dataContainer.appendChild(card);
    });
}

function showError() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('error').style.display = 'flex';
}

// Window global for manual button
window.goHome = function () {
    chrome.tabs.getCurrent((tab) => {
        chrome.tabs.update(tab.id, { url: chrome.runtime.getURL('dist/newtab.html') });
    });
};

function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
