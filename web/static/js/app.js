const $ = id => document.getElementById(id);
let sessionId = null;

// Theme
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

function setStatus(logs, error) {
  const area = $('statusArea');
  area.innerHTML = logs.map(l => `<div class="log-line">${escapeHtml(l)}</div>`).join('');
  if (error) {
    area.innerHTML += `<div class="log-line error">${escapeHtml(error)}</div>`;
  }
  area.scrollTop = area.scrollHeight;
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

async function upload() {
  const fileInput = $('fileInput');
  if (!fileInput.files.length) return;

  const file = fileInput.files[0];
  const config = $('configSelect').value;

  $('convertBtn').disabled = true;
  $('generateBtn').disabled = true;
  $('downloadArea').style.display = 'none';
  $('mdEditor').value = '';
  setStatus([`正在上传: ${file.name}...`]);

  const form = new FormData();
  form.append('file', file);
  form.append('config', config);

  try {
    const res = await fetch('/api/upload', { method: 'POST', body: form });
    if (!res.ok) {
      const err = await res.json();
      setStatus([], err.detail || '上传失败');
      $('convertBtn').disabled = false;
      return;
    }
    const data = await res.json();
    sessionId = data.session_id;
    $('mdEditor').value = data.markdown;
    setStatus(data.log || []);
    $('generateBtn').disabled = false;
    $('convertBtn').disabled = false;
  } catch (e) {
    setStatus([], e.message);
    $('convertBtn').disabled = false;
  }
}

async function generate() {
  if (!sessionId) return;

  $('generateBtn').disabled = true;
  setStatus(['正在生成格式化文档...']);

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, markdown: $('mdEditor').value }),
    });
    if (!res.ok) {
      const err = await res.json();
      setStatus([], err.detail || '生成失败');
      $('generateBtn').disabled = false;
      return;
    }
    const data = await res.json();
    $('downloadLink').href = data.download_url;
    $('downloadLink').textContent = data.filename;
    $('downloadLink').download = data.filename;
    $('downloadArea').style.display = 'flex';
    setStatus(['文档生成完毕，点击下载']);
    $('generateBtn').disabled = false;
  } catch (e) {
    setStatus([], e.message);
    $('generateBtn').disabled = false;
  }
}

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
    $('fileName').textContent = fileInput.files[0].name;
    $('convertBtn').disabled = false;
  }
}

$('convertBtn').addEventListener('click', upload);
$('generateBtn').addEventListener('click', generate);

initTheme();
initDropZone();
loadConfigs();
