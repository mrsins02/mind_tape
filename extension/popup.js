document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  loadCurrentPage();
  loadRelatedMemories();
  initSearch();
  initSettings();
  updateStatus();
});

function initTabs() {
  const tabs = document.querySelectorAll('.tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(tab.dataset.tab + 'Tab').classList.add('active');
    });
  });
}

function loadCurrentPage() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs[0];
    document.getElementById('pageTitle').textContent = tab.title;
    
    chrome.tabs.sendMessage(tab.id, { type: 'GET_PAGE_CONTENT' }, (response) => {
      if (response) {
        const summary = response.content.substring(0, 300) + '...';
        document.getElementById('pageSummary').innerHTML = `<p>${summary}</p>`;
      }
    });
  });
  
  document.getElementById('saveBtn').addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.tabs.sendMessage(tabs[0].id, { type: 'MANUAL_SAVE' }, () => {
        showNotification('Page saved to memory!');
      });
    });
  });
}

function loadRelatedMemories() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const url = tabs[0].url;
    chrome.runtime.sendMessage({ type: 'GET_RELATED', url }, (results) => {
      const container = document.getElementById('relatedList');
      if (results && results.length > 0) {
        container.innerHTML = results.map(r => `
          <div class="memory-item">
            <h4>${r.memory.title}</h4>
            <p>${r.memory.content.substring(0, 100)}...</p>
            <span class="score">Score: ${r.score.toFixed(2)}</span>
          </div>
        `).join('');
      } else {
        container.innerHTML = '<p class="empty-state">No related memories found</p>';
      }
    });
  });
}

function initSearch() {
  const searchBtn = document.getElementById('searchBtn');
  const searchInput = document.getElementById('searchInput');
  const askBtn = document.getElementById('askBtn');
  const questionInput = document.getElementById('questionInput');
  
  searchBtn.addEventListener('click', () => performSearch());
  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
  });
  
  askBtn.addEventListener('click', () => askQuestion());
  questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') askQuestion();
  });
}

function performSearch() {
  const query = document.getElementById('searchInput').value;
  if (!query) return;
  
  chrome.runtime.sendMessage({ type: 'QUERY_MEMORIES', query }, (results) => {
    const container = document.getElementById('searchResults');
    if (results && results.length > 0) {
      container.innerHTML = results.map(r => `
        <div class="memory-item">
          <h4>${r.memory.title}</h4>
          <p>${r.memory.content.substring(0, 100)}...</p>
          <a href="${r.memory.url}" target="_blank" class="link">Open</a>
        </div>
      `).join('');
    } else {
      container.innerHTML = '<p class="empty-state">No results found</p>';
    }
  });
}

function askQuestion() {
  const query = document.getElementById('questionInput').value;
  if (!query) return;
  
  const answerBox = document.getElementById('answerBox');
  answerBox.classList.remove('hidden');
  answerBox.innerHTML = '<p class="loading">Thinking...</p>';
  
  chrome.runtime.sendMessage({ type: 'GET_CONTEXT', query }, (response) => {
    if (response && response.answer) {
      answerBox.innerHTML = `
        <div class="answer">
          <p>${response.answer}</p>
          <div class="sources">
            <h5>Sources:</h5>
            ${response.sources.map(s => `<a href="${s.url}" target="_blank">${s.title}</a>`).join(', ')}
          </div>
        </div>
      `;
    } else {
      answerBox.innerHTML = '<p class="error">Could not find an answer</p>';
    }
  });
}

function initSettings() {
  const settingsBtn = document.getElementById('settingsBtn');
  const settingsPanel = document.getElementById('settingsPanel');
  const saveSettingsBtn = document.getElementById('saveSettings');
  const apiKeyInput = document.getElementById('apiKeyInput');
  
  settingsBtn.addEventListener('click', () => {
    settingsPanel.classList.toggle('hidden');
  });
  
  chrome.storage.local.get(['apiKey'], (result) => {
    if (result.apiKey) {
      apiKeyInput.value = result.apiKey;
    }
  });
  
  saveSettingsBtn.addEventListener('click', () => {
    const apiKey = apiKeyInput.value.trim();
    chrome.storage.local.set({ apiKey }, () => {
      showNotification('Settings saved!');
      settingsPanel.classList.add('hidden');
    });
  });
}

function updateStatus() {
  fetch('http://localhost:8000/health')
    .then(res => res.json())
    .then(data => {
      document.getElementById('statusIndicator').classList.add('connected');
      document.getElementById('statusText').textContent = 'Connected';
    })
    .catch(() => {
      document.getElementById('statusIndicator').classList.add('disconnected');
      document.getElementById('statusText').textContent = 'Disconnected';
    });
}

function showNotification(message) {
  const notification = document.createElement('div');
  notification.className = 'notification';
  notification.textContent = message;
  document.body.appendChild(notification);
  setTimeout(() => notification.remove(), 2000);
}
