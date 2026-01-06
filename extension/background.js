const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000';
let deviceId = null;
let apiKey = null;
let ws = null;
let lastSyncTimestamp = null;

// Initialize on load (Service Worker wake up)
function init() {
  chrome.storage.local.get(['deviceId', 'apiKey', 'lastSync'], (result) => {
    if (result.deviceId) {
      deviceId = result.deviceId;
    }
    apiKey = result.apiKey || 'dev-api-key-change-in-production';
    lastSyncTimestamp = result.lastSync || null;
    connectWebSocket();
  });
}

init();

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(['deviceId'], (result) => {
    if (!result.deviceId) {
      const newDeviceId = 'device_' + Date.now() + '_' + Math.random().toString(36).substring(2, 11);
      chrome.storage.local.set({ deviceId: newDeviceId });
      deviceId = newDeviceId;
    }
    init();
  });
});

chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local') {
    let shouldReconnect = false;
    
    if (changes.apiKey) {
      apiKey = changes.apiKey.newValue;
      shouldReconnect = true;
    }
    
    if (changes.deviceId) {
      deviceId = changes.deviceId.newValue;
      shouldReconnect = true;
    }

    if (changes.lastSync) {
      lastSyncTimestamp = changes.lastSync.newValue;
    }
    
    if (shouldReconnect) {
      if (ws) {
        ws.close();
      }
      connectWebSocket();
    }
  }
});

function connectWebSocket() {
  if (!deviceId) return;
  
  try {
    // Ensure we have current values or fallback defaults
    const token = apiKey || 'dev-api-key-change-in-production';
    ws = new WebSocket(`${WS_BASE}/sync/realtime?device_id=${deviceId}&token=${token}`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      ws.send(JSON.stringify({ type: 'sync_request', last_sync: lastSyncTimestamp }));
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Reconnection logic could go here, but be careful with service worker lifecycle
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  } catch (e) {
    console.error('WebSocket connection failed:', e);
  }
}

function handleWebSocketMessage(data) {
  if (data.type === 'memory_updated') {
    chrome.runtime.sendMessage({ type: 'MEMORY_UPDATED', data });
  } else if (data.type === 'sync_ack') {
    lastSyncTimestamp = data.timestamp;
    chrome.storage.local.set({ lastSync: data.timestamp });
  }
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'SAVE_MEMORY') {
    saveMemory(request.data).then(sendResponse);
    return true;
  } else if (request.type === 'QUERY_MEMORIES') {
    queryMemories(request.query).then(sendResponse);
    return true;
  } else if (request.type === 'GET_CONTEXT') {
    getContext(request.query).then(sendResponse);
    return true;
  } else if (request.type === 'GET_RELATED') {
    getRelatedMemories(request.url).then(sendResponse);
    return true;
  }
});

async function getConfig() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['deviceId', 'apiKey'], (result) => {
      resolve({
        deviceId: result.deviceId || deviceId,
        apiKey: result.apiKey || apiKey || 'dev-api-key-change-in-production'
      });
    });
  });
}

async function saveMemory(data) {
  const config = await getConfig();
  try {
    const response = await fetch(`${API_BASE}/memory/add`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': config.apiKey
      },
      body: JSON.stringify({
        ...data,
        device_id: config.deviceId
      })
    });
    return await response.json();
  } catch (error) {
    console.error('Save memory error:', error);
    return { error: error.message };
  }
}

async function queryMemories(query) {
  const config = await getConfig();
  try {
    const response = await fetch(`${API_BASE}/memory/query?query=${encodeURIComponent(query)}&limit=5`, {
      headers: { 'X-API-Key': config.apiKey }
    });
    return await response.json();
  } catch (error) {
    console.error('Query error:', error);
    return [];
  }
}

async function getContext(query) {
  const config = await getConfig();
  try {
    const response = await fetch(`${API_BASE}/memory/context?query=${encodeURIComponent(query)}&limit=5`, {
      headers: { 'X-API-Key': config.apiKey }
    });
    return await response.json();
  } catch (error) {
    console.error('Context error:', error);
    return { answer: 'Error getting context' };
  }
}

async function getRelatedMemories(url) {
  const config = await getConfig();
  try {
    const response = await fetch(`${API_BASE}/memory/query?query=${encodeURIComponent(url)}&limit=5`, {
      headers: { 'X-API-Key': config.apiKey }
    });
    return await response.json();
  } catch (error) {
    console.error('Related memories error:', error);
    return [];
  }
}
