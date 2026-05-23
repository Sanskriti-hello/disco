// Background service worker: extension -> localhost backend only

const BACKEND_URL = "http://127.0.0.1:8000";

async function backendPost(path, body) {
  const start = Date.now();
  const response = await fetch(`${BACKEND_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const elapsed = Date.now() - start;
  console.log(`[backend] POST ${path} -> ${response.status} (${elapsed}ms)`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Backend ${path} failed (${response.status}): ${text}`);
  }
  return response.json();
}

async function backendGet(path) {
  const start = Date.now();
  const response = await fetch(`${BACKEND_URL}${path}`);
  const elapsed = Date.now() - start;
  console.log(`[backend] GET ${path} -> ${response.status} (${elapsed}ms)`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Backend ${path} failed (${response.status}): ${text}`);
  }
  return response.json();
}

async function extractTabsContent() {
  const tabs = await chrome.tabs.query({});
  const validTabs = tabs.filter((tab) =>
    tab.id &&
    tab.url &&
    !tab.url.startsWith("chrome://") &&
    !tab.url.startsWith("chrome-extension://") &&
    !tab.url.startsWith("https://chrome.google.com")
  );

  const results = await Promise.allSettled(
    validTabs.map(async (tab) => {
      try {
        const injectionResults = await chrome.scripting
          .executeScript({ target: { tabId: tab.id }, files: ["content_extractor.js"] })
          .catch(() => null);

        if (injectionResults?.[0]?.result) {
          const result = injectionResults[0].result;
          return {
            id: tab.id,
            title: tab.title || "Untitled",
            url: tab.url,
            content: (result.content || "").substring(0, 2000),
            structured: result.structured || {},
          };
        }

        const fallbackResult = await chrome.scripting
          .executeScript({
            target: { tabId: tab.id },
            func: () => document.body?.innerText?.substring(0, 2000) || "",
          })
          .catch(() => null);

        return {
          id: tab.id,
          title: tab.title || "Untitled",
          url: tab.url,
          content: fallbackResult?.[0]?.result || "",
          structured: {},
        };
      } catch {
        return {
          id: tab.id,
          title: tab.title || "Untitled",
          url: tab.url,
          content: "",
          structured: {},
        };
      }
    })
  );

  return results.filter((r) => r.status === "fulfilled").map((r) => r.value);
}

async function getBrowsingHistory(maxResults = 100) {
  const history = await chrome.history.search({
    text: "",
    maxResults,
    startTime: Date.now() - 7 * 24 * 60 * 60 * 1000,
  });

  return history.map((item) => ({
    title: item.title || "Untitled",
    url: item.url,
    lastVisitTime: item.lastVisitTime,
    visitCount: item.visitCount,
  }));
}

const EXTENSION_ID = "klpjekjcldkpdleckklnoambfliodpca";
const CLIENT_ID = "276787019429-k78ckehgoe5k2egu38fdns4np39vsstf.apps.googleusercontent.com";
const REDIRECT_URI = `https://${EXTENSION_ID}.chromiumapp.org/`;

async function authenticateGoogle() {
  const scopes = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
  ];

  const authUrl =
    "https://accounts.google.com/o/oauth2/v2/auth?" +
    `client_id=${CLIENT_ID}&` +
    "response_type=token&" +
    `redirect_uri=${encodeURIComponent(REDIRECT_URI)}&` +
    `scope=${encodeURIComponent(scopes.join(" "))}`;

  return new Promise((resolve, reject) => {
    chrome.identity.launchWebAuthFlow({ url: authUrl, interactive: true }, (redirectUrl) => {
      if (chrome.runtime.lastError || !redirectUrl) {
        reject(chrome.runtime.lastError?.message || "Auth failed");
        return;
      }
      const url = new URL(redirectUrl);
      const params = new URLSearchParams(url.hash.substring(1));
      const token = params.get("access_token");
      if (token) {
        chrome.storage.local.set({ google_token: token, token_expiry: Date.now() + 3500000 });
        resolve(token);
      } else {
        reject("Token not found in response");
      }
    });
  });
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "healthCheck") {
    (async () => {
      try {
        const health = await backendGet("/health");
        sendResponse({ success: true, health });
      } catch (error) {
        sendResponse({ success: false, error: String(error) });
      }
    })();
    return true;
  }

  if (request.action === "clusterTabs") {
    (async () => {
      try {
        const tabsData = await extractTabsContent();
        if (!tabsData.length) {
          sendResponse({ success: false, error: "No valid tabs found" });
          return;
        }

        const result = await backendPost("/api/cluster-tabs", { tabs: tabsData });
        await chrome.storage.local.set({ tabClusters: result.clusters || [], lastClusterTime: Date.now() });
        sendResponse({ success: true, clusters: result.clusters || [], totalTabs: tabsData.length, meta: result });
      } catch (error) {
        sendResponse({ success: false, error: String(error) });
      }
    })();
    return true;
  }

  if (request.action === "selectDomain") {
    (async () => {
      try {
        const clusterId = request.clusterId;
        const userPrompt = request.userPrompt || "";
        const { tabClusters } = await chrome.storage.local.get("tabClusters");
        const selectedCluster = (tabClusters || []).find((c) => c.cluster_id === clusterId);

        if (!selectedCluster) {
          sendResponse({ success: false, error: "Cluster not found" });
          return;
        }

        const domainResp = await backendPost("/api/select-domain", {
          tabs: selectedCluster.tabs,
          user_prompt: userPrompt,
        });

        const domainResult = {
          ...domainResp.result,
          tabs: selectedCluster.tabs,
          timestamp: Date.now(),
        };

        await chrome.storage.local.set({ selectedDomain: domainResult });
        sendResponse({ success: true, result: domainResult, meta: domainResp });
      } catch (error) {
        sendResponse({ success: false, error: String(error) });
      }
    })();
    return true;
  }

  if (request.action === "generateDashboard") {
    (async () => {
      try {
        const { selectedDomain, google_token } = await chrome.storage.local.get(["selectedDomain", "google_token"]);
        if (!selectedDomain) {
          sendResponse({ success: false, error: "No domain selected. Run selectDomain first." });
          return;
        }

        const payload = {
          domain: selectedDomain.domain,
          tabs: selectedDomain.tabs,
          user_prompt: selectedDomain.userPrompt || request.userPrompt || "",
          summary: selectedDomain.summary || "",
          history: [],
          google_token: google_token || null,
        };

        const dashboardConfig = await backendPost("/api/generate-dashboard", payload);
        console.log("[dashboard] payload received", dashboardConfig.template);

        await chrome.storage.local.set({
          dashboardConfig,
          lastDashboardTime: Date.now(),
          backendMode: dashboardConfig.fallback_mode ? "fallback" : "normal",
        });

        sendResponse({ success: true, config: dashboardConfig });
      } catch (error) {
        sendResponse({
          success: false,
          error: String(error),
          hint: "Make sure backend is running at http://127.0.0.1:8000",
        });
      }
    })();
    return true;
  }

  if (request.action === "getClusters") {
    chrome.storage.local.get("tabClusters", ({ tabClusters }) => sendResponse({ clusters: tabClusters || [] }));
    return true;
  }

  if (request.action === "getSelectedDomain") {
    chrome.storage.local.get("selectedDomain", ({ selectedDomain }) => sendResponse({ result: selectedDomain || null }));
    return true;
  }

  if (request.action === "getDashboardConfig") {
    chrome.storage.local.get("dashboardConfig", ({ dashboardConfig }) => sendResponse({ config: dashboardConfig || null }));
    return true;
  }

  if (request.action === "getAuthToken") {
    authenticateGoogle()
      .then((token) => sendResponse({ success: true, token }))
      .catch((error) => sendResponse({ success: false, error }));
    return true;
  }

  if (request.type === "GET_TABS") {
    extractTabsContent().then((tabs) => sendResponse({ tabs }));
    return true;
  }

  if (request.type === "GET_HISTORY") {
    getBrowsingHistory(request.maxResults || 100).then((history) => sendResponse({ history }));
    return true;
  }

  sendResponse({ success: false, error: "Unhandled message", request });
  return false;
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    tabClusters: [],
    selectedDomain: null,
    lastClusterTime: null,
    backendMode: "unknown",
  });
});
