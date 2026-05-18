const $ = id => document.getElementById(id);

// --- Toast ---
function showToast(message, type = 'error') {
  const container = $('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// --- Theme ---
function initTheme() {
  const toggle = $('themeToggle');
  const html = document.documentElement;
  function setTheme(dark) {
    html.setAttribute('data-theme', dark ? 'dark' : 'light');
    toggle.innerHTML = dark ? '☀' : '☾';
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }
  const saved = localStorage.getItem('theme');
  if (saved === 'dark' || (!saved && matchMedia('(prefers-color-scheme: dark)').matches)) {
    setTheme(true);
  }
  toggle.addEventListener('click', () => {
    setTheme(html.getAttribute('data-theme') !== 'dark');
  });
}

// --- Config ---
async function loadConfigs() {
  const res = await fetch('/api/configs');
  const data = await res.json();
  const sel = $('configSelect');
  sel.innerHTML = '';
  data.configs.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.filename;
    opt.textContent = c.name;
    sel.appendChild(opt);
  });
}

// --- Tab Management ---
const tabManager = {
  tabs: [],
  activeIndex: -1,
};

function getActiveTab() {
  return tabManager.activeIndex >= 0 ? tabManager.tabs[tabManager.activeIndex] : null;
}

function addTab(sessionId, filename, markdown) {
  tabManager.tabs.push({
    sessionId,
    filename,
    markdown,
    downloadUrl: null,
    downloadFilename: null,
    generated: false,
  });
  switchTab(tabManager.tabs.length - 1);
}

function closeTab(index) {
  tabManager.tabs.splice(index, 1);
  if (tabManager.tabs.length === 0) {
    tabManager.activeIndex = -1;
  } else if (tabManager.activeIndex === index) {
    tabManager.activeIndex = Math.min(index, tabManager.tabs.length - 1);
  } else if (tabManager.activeIndex > index) {
    tabManager.activeIndex--;
  }
  renderTabs();
  restoreEditor();
  refreshUI();
}

function switchTab(index) {
  if (index === tabManager.activeIndex) return;
  saveCurrentTab();
  tabManager.activeIndex = index;
  renderTabs();
  restoreEditor();
  refreshUI();
}

function saveCurrentTab() {
  const tab = getActiveTab();
  if (tab) tab.markdown = $('mdEditor').value;
}

function restoreEditor() {
  const tab = getActiveTab();
  $('mdEditor').value = tab ? tab.markdown : '';
}

function updateTabAfterGenerate(downloadUrl, downloadFilename) {
  const tab = getActiveTab();
  if (!tab) return;
  tab.downloadUrl = downloadUrl;
  tab.downloadFilename = downloadFilename;
  tab.generated = true;
  renderTabs();
  refreshUI();
}

function renderTabs() {
  const bar = $('tabBar');
  bar.innerHTML = '';
  tabManager.tabs.forEach((tab, i) => {
    const el = document.createElement('div');
    el.className = 'tab-item' + (i === tabManager.activeIndex ? ' active' : '') + (tab.generated ? ' generated' : '');
    el.dataset.index = i;
    el.innerHTML = `<span class="tab-name">${escapeHtml(tab.filename)}</span><span class="tab-close">×</span>`;
    bar.appendChild(el);
  });
}

function refreshUI() {
  const tab = getActiveTab();
  $('generateBtn').disabled = !tab;
  $('downloadBtn').disabled = !tab || !tab.generated;
  $('formatBtn').disabled = !tab;
}

// --- Upload ---
async function upload() {
  const fileInput = $('fileInput');
  if (!fileInput.files.length) return;

  const config = $('configSelect').value;
  $('convertBtn').disabled = true;

  for (const file of fileInput.files) {
    const form = new FormData();
    form.append('file', file);
    form.append('config', config);

    try {
      const res = await fetch('/api/upload', { method: 'POST', body: form });
      if (!res.ok) {
        const err = await res.json();
        showToast(`${file.name}: ${err.detail || '上传失败'}`);
        continue;
      }
      const data = await res.json();
      addTab(data.session_id, data.original_filename, data.markdown);
    } catch (e) {
      showToast(`${file.name}: ${e.message}`);
    }
  }

  $('convertBtn').disabled = false;
  fileInput.value = '';
  $('fileName').textContent = '';
}

// --- Generate ---
async function generate() {
  const tab = getActiveTab();
  if (!tab) return;

  $('generateBtn').disabled = true;

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: tab.sessionId, markdown: $('mdEditor').value }),
    });
    if (!res.ok) {
      const err = await res.json();
      showToast(err.detail || '生成失败');
      $('generateBtn').disabled = false;
      return;
    }
    const data = await res.json();
    updateTabAfterGenerate(data.download_url, data.filename);
    $('generateBtn').disabled = false;
  } catch (e) {
    showToast(e.message);
    $('generateBtn').disabled = false;
  }
}

// --- Download ---
function downloadFile() {
  const tab = getActiveTab();
  if (!tab || !tab.generated || !tab.downloadUrl) return;
  const a = document.createElement('a');
  a.href = tab.downloadUrl;
  a.download = tab.downloadFilename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// --- Format ---
function formatMarkdown() {
  const editor = $('mdEditor');
  if (!editor.value) return;
  editor.value = editor.value.replace(/(?<!\n)\n\n(?!\n)/g, '\n');
}

// --- Drop Zone ---
function initDropZone() {
  const dropZone = $('dropZone');
  const fileInput = $('fileInput');

  dropZone.addEventListener('click', () => fileInput.click());
  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    fileInput.files = e.dataTransfer.files;
    onFileSelected();
  });
  fileInput.addEventListener('change', onFileSelected);
}

function onFileSelected() {
  const fileInput = $('fileInput');
  if (fileInput.files.length) {
    $('fileName').textContent = fileInput.files.length === 1
      ? fileInput.files[0].name
      : `已选择 ${fileInput.files.length} 个文件`;
    $('convertBtn').disabled = false;
  }
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

// --- Event Listeners ---
$('convertBtn').addEventListener('click', upload);
$('generateBtn').addEventListener('click', generate);
$('downloadBtn').addEventListener('click', downloadFile);
$('formatBtn').addEventListener('click', formatMarkdown);
$('tabBar').addEventListener('click', e => {
  const close = e.target.closest('.tab-close');
  const item = e.target.closest('.tab-item');
  if (!item) return;
  const index = parseInt(item.dataset.index);
  if (close) {
    closeTab(index);
  } else {
    switchTab(index);
  }
});

initTheme();
initDropZone();
loadConfigs();
