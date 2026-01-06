(function() {
  let isCapturing = false;
  
  function extractPageContent() {
    const title = document.title;
    const url = window.location.href;
    
    const elementsToRemove = document.querySelectorAll('script, style, nav, footer, header, aside, iframe, noscript');
    const clone = document.body.cloneNode(true);
    clone.querySelectorAll('script, style, nav, footer, header, aside, iframe, noscript').forEach(el => el.remove());
    
    let content = clone.innerText || clone.textContent || '';
    content = content.replace(/\s+/g, ' ').trim();
    content = content.substring(0, 10000);
    
    return { title, url, content };
  }
  
  function saveCurrentPage() {
    if (isCapturing) return;
    isCapturing = true;
    
    const pageData = extractPageContent();
    
    if (pageData.content.length < 100) {
      isCapturing = false;
      return;
    }
    
    chrome.runtime.sendMessage({
      type: 'SAVE_MEMORY',
      data: pageData
    }, (response) => {
      isCapturing = false;
      if (response && !response.error) {
        console.log('MindTape: Page saved');
      }
    });
  }
  
  let saveTimeout = null;
  function debouncedSave() {
    if (saveTimeout) clearTimeout(saveTimeout);
    saveTimeout = setTimeout(saveCurrentPage, 2000);
  }
  
  if (document.readyState === 'complete') {
    debouncedSave();
  } else {
    window.addEventListener('load', debouncedSave);
  }
  
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'GET_PAGE_CONTENT') {
      sendResponse(extractPageContent());
    } else if (request.type === 'MANUAL_SAVE') {
      saveCurrentPage();
      sendResponse({ status: 'saving' });
    }
  });
})();
