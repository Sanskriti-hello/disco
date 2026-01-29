// ============================================================================
// BACKGROUND.JS - Tab Clustering + Domain Selection
// ============================================================================

// ---------------------------------------------------------------------------
// 1. TAB EXTRACTION
// ---------------------------------------------------------------------------

async function extractTabsContent() {
  const tabs = await chrome.tabs.query({});

  // Filter valid tabs first
  const validTabs = tabs.filter(tab =>
    tab.id &&
    tab.url &&
    !tab.url.startsWith("chrome://") &&
    !tab.url.startsWith("chrome-extension://") &&
    !tab.url.startsWith("https://chrome.google.com")
  );

  // Process tabs in parallel to prevent timeouts
  const results = await Promise.allSettled(validTabs.map(async (tab) => {
    try {
      // Try content script extraction first
      const injectionResults = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content_extractor.js']
      }).catch(() => null);

      if (injectionResults && injectionResults[0] && injectionResults[0].result) {
        return {
          id: tab.id,
          title: tab.title || "Untitled",
          url: tab.url,
          content: (injectionResults[0].result.content || "").substring(0, 2000)
        };
      }

      // Fallback to basic extraction
      const fallbackResult = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => document.body?.innerText?.substring(0, 2000) || ""
      }).catch(() => null);

      const content = (fallbackResult && fallbackResult[0]?.result) || "";

      return {
        id: tab.id,
        title: tab.title || "Untitled",
        url: tab.url,
        content: content
      };

    } catch (err) {
      console.warn(`Failed to extract tab ${tab.id}:`, err);
      // Return basic info even if extraction fails
      return {
        id: tab.id,
        title: tab.title || "Untitled",
        url: tab.url,
        content: ""
      };
    }
  }));

  // Return only successful results
  return results
    .filter(r => r.status === 'fulfilled')
    .map(r => r.value);
}

// ---------------------------------------------------------------------------
// 2. TAB CLUSTERING - Groups tabs into semantic clusters
// ---------------------------------------------------------------------------

async function clusterTabs(apiKey, tabsData) {
  if (tabsData.length === 0) {
    return [];
  }

  // Prepare tab list for LLM
  const tabList = tabsData.map((tab, idx) =>
    `${idx + 1}. [${tab.title}](${tab.url})\n   Content: ${tab.content.substring(0, 150)}...`
  ).join('\n\n');

  const systemPrompt = `You are a tab clustering assistant. Analyze these browser tabs and group them into logical clusters.

For each cluster, determine the PRIMARY domain from ONLY these 6 options:
- study: User is researching, learning, reading documentation/papers
- shopping: User is looking to buy something, comparing prices, shopping
- travel: User is searching for travel destinations, flights, hotels, trains
- code: User has coding problems, documentation, GitHub, Stack Overflow open
- entertainment: User is looking for movies, shows, music, games, streaming
- generic: Anything that doesn't fit above categories

Respond with ONLY valid JSON (no markdown):
{
  "clusters": [
    {
      "cluster_id": 0,
      "tab_numbers": [1, 3, 5],
      "domain": "study",
      "summary": "Research papers on machine learning",
      "cluster_name": "ML Research"
    }
  ]
}

Create 1-5 clusters based on tab similarity. Combine related topics.`;

  const userMessage = `Cluster these ${tabsData.length} tabs:\n\n${tabList}`;

  try {
    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: "llama-3.3-70b-versatile",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: userMessage }
        ],
        temperature: 0.3,
        max_completion_tokens: 2048,
        response_format: { type: "json_object" }
      })
    });

    let data;
    try {
      data = await response.json();
    } catch (e) {
      throw new Error("Invalid JSON from LLM API");
    }

    if (!data.choices || !data.choices[0]) {
      throw new Error("Malformed LLM response");
    }

    const parsed = JSON.parse(data.choices[0].message.content);
    const clusterData = parsed.clusters || parsed;

    // Map clusters back to actual tabs
    const clusters = (Array.isArray(clusterData) ? clusterData : [clusterData]).map(cluster => {
      const tabIndices = (cluster.tab_numbers || [])
        .filter(n => n > 0 && n <= tabsData.length)
        .map(n => n - 1);

      return {
        cluster_id: cluster.cluster_id,
        tabs: tabIndices.map(i => tabsData[i]),
        domain: cluster.domain || "generic",
        summary: cluster.summary || "Mixed tabs",
        cluster_name: cluster.cluster_name || `Cluster ${cluster.cluster_id + 1}`
      };
    });

    return clusters.filter(c => c.tabs.length > 0);

  } catch (error) {
    console.error('Clustering failed:', error);

    // Fallback: single generic cluster
    return [{
      cluster_id: 0,
      tabs: tabsData,
      domain: "generic",
      summary: "All open tabs",
      cluster_name: "All Tabs"
    }];
  }
}

// ---------------------------------------------------------------------------
// 3. DOMAIN SELECTOR - Determines final domain based on user selection
// ---------------------------------------------------------------------------

async function selectDomain(apiKey, selectedCluster, userPrompt) {
  /**
   * Takes user selection (cluster or custom prompt) and determines domain
   * Returns: { domain, tabs, summary, userPrompt }
   */

  const VALID_DOMAINS = ['study', 'shopping', 'travel', 'code', 'entertainment', 'generic'];

  // If user typed custom prompt, use LLM to determine domain
  if (userPrompt && userPrompt.trim()) {
    const tabSummaries = selectedCluster.tabs.map(t =>
      `- ${t.title}`
    ).join('\n');

    const systemPrompt = `Based on the user's request and their open tabs, determine which domain best fits.

Available domains:
- study: researching, learning, reading papers/documentation
- shopping: buying products, comparing prices
- travel: planning trips, booking flights/hotels
- code: programming, debugging, reading docs
- entertainment: movies, shows, music, games
- generic: general tasks, summarization, simple apps

Respond with ONLY valid JSON:
{
  "domain": "study",
  "reason": "User wants to study the ML papers they have open"
}`;

    const userMessage = `User request: "${userPrompt}"

Open tabs:
${tabSummaries}

What domain should handle this?`;

    try {
      const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          model: "llama-3.3-70b-versatile",
          messages: [
            { role: "system", content: systemPrompt },
            { role: "user", content: userMessage }
          ],
          temperature: 0.2,
          max_completion_tokens: 256,
          response_format: { type: "json_object" }
        })
      });

      const data = await response.json();

      if (!data.error) {
        const result = JSON.parse(data.choices[0].message.content);
        const domain = VALID_DOMAINS.includes(result.domain) ? result.domain : "generic";

        return {
          domain: domain,
          tabs: selectedCluster.tabs,
          summary: result.reason || selectedCluster.summary,
          userPrompt: userPrompt,
          timestamp: Date.now()
        };
      }
    } catch (error) {
      console.error('Domain selection failed:', error);
    }
  }

  // Default: use cluster's domain
  return {
    domain: VALID_DOMAINS.includes(selectedCluster.domain) ? selectedCluster.domain : "generic",
    tabs: selectedCluster.tabs,
    summary: selectedCluster.summary,
    userPrompt: userPrompt || "",
    timestamp: Date.now()
  };
}

// ---------------------------------------------------------------------------
// 4. MESSAGE HANDLERS
// ---------------------------------------------------------------------------

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {

  // STEP 1: Extract and cluster tabs
  if (request.action === 'clusterTabs') {
    (async () => {
      try {
        const apiKey = request.apiKey;
        if (!apiKey) {
          sendResponse({ error: 'API key required' });
          return;
        }

        // Extract tabs
        const tabsData = await extractTabsContent();

        if (tabsData.length === 0) {
          sendResponse({ error: 'No valid tabs found' });
          return;
        }

        // Cluster tabs
        const clusters = await clusterTabs(apiKey, tabsData);

        // Save clusters to storage
        await chrome.storage.local.set({
          tabClusters: clusters,
          lastClusterTime: Date.now()
        });

        sendResponse({
          success: true,
          clusters: clusters,
          totalTabs: tabsData.length
        });

      } catch (error) {
        console.error('Clustering error:', error);
        sendResponse({ error: error.message });
      }
    })();
    return true; // Keep channel open for async
  }

  // STEP 2: Select domain based on user choice
  if (request.action === 'selectDomain') {
    (async () => {
      try {
        const apiKey = request.apiKey;
        const clusterId = request.clusterId;
        const userPrompt = request.userPrompt || "";

        // Get stored clusters
        const { tabClusters } = await chrome.storage.local.get('tabClusters');

        if (!tabClusters || !Array.isArray(tabClusters)) {
          sendResponse({ error: 'No clusters found. Run clustering first.' });
          return;
        }

        const selectedCluster = tabClusters.find(c => c.cluster_id === clusterId);

        if (!selectedCluster) {
          sendResponse({ error: 'Cluster not found' });
          return;
        }

        // Get domain selection
        const domainResult = await selectDomain(apiKey, selectedCluster, userPrompt);

        // Save to storage
        await chrome.storage.local.set({
          selectedDomain: domainResult
        });

        sendResponse({
          success: true,
          result: domainResult
        });

      } catch (error) {
        console.error('Domain selection error:', error);
        sendResponse({ error: error.message });
      }
    })();
    return true;
  }

  // Get stored clusters (for UI refresh)
  if (request.action === 'getClusters') {
    (async () => {
      const { tabClusters } = await chrome.storage.local.get('tabClusters');
      sendResponse({ clusters: tabClusters || [] });
    })();
    return true;
  }

  // Get selected domain result
  if (request.action === 'getSelectedDomain') {
    (async () => {
      const { selectedDomain } = await chrome.storage.local.get('selectedDomain');
      sendResponse({ result: selectedDomain || null });
    })();
    return true;
  }

  // Legacy: Get tabs for display
  if (request.type === "GET_TABS") {
    extractTabsContent().then(tabs => {
      sendResponse({ tabs });
    });
    return true;
  }

  // Legacy: Get history
  if (request.type === "GET_HISTORY") {
    getBrowsingHistory(request.maxResults || 100).then(history => {
      sendResponse({ history });
    });
    return true;
  }

  // Catch-all: Always respond to prevent "message port closed" errors
  // Return false synchronously for unhandled messages
  sendResponse({ error: "Unhandled message", request });
  return false;
});

// ---------------------------------------------------------------------------
// 5. HELPER: Get Browsing History
// ---------------------------------------------------------------------------

async function getBrowsingHistory(maxResults = 100) {
  const history = await chrome.history.search({
    text: "",
    maxResults: maxResults,
    startTime: Date.now() - (7 * 24 * 60 * 60 * 1000)
  });

  return history.map(item => ({
    title: item.title || "Untitled",
    url: item.url,
    lastVisitTime: item.lastVisitTime,
    visitCount: item.visitCount
  }));
}

// ---------------------------------------------------------------------------
// 6. INITIALIZATION
// ---------------------------------------------------------------------------

chrome.runtime.onInstalled.addListener(() => {
  console.log('Dashboard Extension installed');

  chrome.storage.local.set({
    tabClusters: [],
    selectedDomain: null,
    lastClusterTime: null
  });

});