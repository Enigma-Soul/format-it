'use strict';

/* ================= 工具 ================= */

const $ = id => document.getElementById(id);

const els = {
  themeToggle: $('themeToggle'),
  configSelect: $('configSelect'),
  dropZone: $('dropZone'),
  fileInput: $('fileInput'),
  fileList: $('fileList'),
  convertBtn: $('convertBtn'),
  tabBar: $('tabBar'),
  formatBtn: $('formatBtn'),
  generateBtn: $('generateBtn'),
  editor: $('mdEditor'),
  overlay: $('editorOverlay'),
  overlayWelcome: $('overlayWelcome'),
  overlayPending: $('overlayPending'),
  pendingName: $('pendingName'),
  sealLayer: $('sealLayer'),
  statusText: $('statusText'),
  toastContainer: $('toastContainer'),
};

// 创建带类名与文本的元素,避免拼 HTML 的转义问题
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

/* ================= 主题 ================= */

function setTheme(dark) {
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
  els.themeToggle.textContent = dark ? '☀' : '☾';
  localStorage.setItem('theme', dark ? 'dark' : 'light');
}

function initTheme() {
  const saved = localStorage.getItem('theme');
  setTheme(saved ? saved === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches);
  els.themeToggle.addEventListener('click', () => {
    setTheme(document.documentElement.getAttribute('data-theme') !== 'dark');
  });
}

/* ================= Toast ================= */

const TOAST_ICONS = { error: '✕', success: '✓', info: 'ℹ' };
const TOAST_MS = { error: 4200, success: 2600, info: 3200 };

function showToast(message, type = 'error') {
  const toast = el('div', `toast ${type}`);
  toast.append(el('span', 't-icon', TOAST_ICONS[type] ?? 'ℹ'), el('span', null, message));
  els.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('toast-out');
    setTimeout(() => toast.remove(), 320);
  }, TOAST_MS[type] ?? 3200);
}

/* ================= 全局状态 ================= */

// tab: { state: 'pending' | 'ready', sessionId, filename, markdown, baseline, dirty, generated }
// baseline 为上传时 / 最近一次生成时的内容,用于判断「有未生成的修改」
const state = {
  files: [],        // 待转换的 File 列表
  tabs: [],
  activeIndex: -1,
  busy: false,      // 上传或生成进行中
};

function activeTab() {
  return state.activeIndex >= 0 ? state.tabs[state.activeIndex] : null;
}

// 按钮忙碌态:进入时换文案并转圈,结束时恢复
function markBusy(button, busyText) {
  button.classList.add('busy');
  button.textContent = busyText;
}

function markIdle(button, normalText) {
  button.classList.remove('busy');
  button.textContent = normalText;
}

/* ================= 标签页 ================= */

function renderTabs() {
  els.tabBar.replaceChildren(...state.tabs.map((tab, i) => {
    const item = el('div', 'tab-item');
    const active = i === state.activeIndex;
    if (active) item.classList.add('active');
    item.role = 'tab';
    item.tabIndex = active ? 0 : -1;
    item.setAttribute('aria-selected', String(active));
    item.dataset.index = i;

    const status = el('span', 'tab-status');
    if (tab.state === 'pending') status.classList.add('pending');
    else if (tab.dirty) status.classList.add('dirty');
    else if (tab.generated) { status.classList.add('done'); status.textContent = '✓'; }

    const close = el('button', 'tab-close', '×');
    close.type = 'button';
    close.setAttribute('aria-label', `关闭 ${tab.filename}`);

    item.append(status, el('span', 'tab-name', tab.filename), close);
    return item;
  }));
}

// 编辑器内容回写到当前标签(转换中的标签无可保存内容)
function saveCurrentTab() {
  const tab = activeTab();
  if (tab && tab.state === 'ready') tab.markdown = els.editor.value;
}

// 将全局状态同步到编辑器、标签栏与各控件
function syncFromState() {
  const tab = activeTab();
  els.editor.value = tab && tab.state === 'ready' ? tab.markdown : '';
  renderTabs();
  refreshUI();
}

function switchTab(index) {
  if (index === state.activeIndex) return;
  saveCurrentTab();
  state.activeIndex = index;
  syncFromState();
}

function closeTab(index) {
  state.tabs.splice(index, 1);
  if (state.tabs.length === 0) state.activeIndex = -1;
  else if (state.activeIndex === index) state.activeIndex = Math.min(index, state.tabs.length - 1);
  else if (state.activeIndex > index) state.activeIndex--;
  syncFromState();
}

function addPendingTab(filename) {
  const tab = {
    state: 'pending', sessionId: null, filename,
    markdown: '', baseline: '', dirty: false, generated: false,
  };
  state.tabs.push(tab);
  state.activeIndex = state.tabs.length - 1;
  syncFromState();
  return tab;
}

function finalizeTab(tab, data) {
  Object.assign(tab, {
    state: 'ready',
    sessionId: data.session_id,
    filename: data.original_filename,
    markdown: data.markdown,
    baseline: data.markdown,
  });
  syncFromState();
}

function failTab(tab, message) {
  const index = state.tabs.indexOf(tab);
  if (index >= 0) closeTab(index);
  showToast(message);
}

// 依据状态刷新按钮、遮罩与状态栏
function refreshUI() {
  const tab = activeTab();
  const ready = !!tab && tab.state === 'ready';

  els.convertBtn.disabled = state.busy || state.files.length === 0;
  els.formatBtn.disabled = !ready;
  els.generateBtn.disabled = !ready || state.busy;
  els.editor.readOnly = !ready;

  els.overlay.hidden = ready;
  els.overlayWelcome.hidden = !!tab;
  els.overlayPending.hidden = !tab;
  if (tab) els.pendingName.textContent = tab.filename;

  els.statusText.textContent = statusTextFor(tab);
}

function statusTextFor(tab) {
  if (!tab) return '-';
  if (tab.state === 'pending') return `正在转换:${tab.filename}`;
  if (tab.generated && !tab.dirty) return `${tab.filename} · 已盖章`;
  if (tab.generated) return `${tab.filename} · 有未生成的修改`;
  return `${tab.filename} · 待生成`;
}

// 编辑即对比基线,标记「未重新生成」
function onEditorInput() {
  const tab = activeTab();
  if (!tab || tab.state !== 'ready') return;
  const dirty = els.editor.value !== tab.baseline;
  if (dirty !== tab.dirty) {
    tab.dirty = dirty;
    renderTabs();
    refreshUI();
  }
}

/* ================= 文件选择 ================= */

function addFiles(fileList) {
  const rejected = [];
  for (const file of fileList) {
    if (file.name.toLowerCase().endsWith('.docx')) state.files.push(file);
    else rejected.push(file.name);
  }
  if (rejected.length) showToast(`已忽略非 .docx 文件:${rejected.join('、')}`, 'info');
  renderFiles();
  refreshUI();
}

function renderFiles() {
  els.fileList.replaceChildren(...state.files.map((file, i) => {
    const remove = el('button', 'chip-remove', '×');
    remove.type = 'button';
    remove.setAttribute('aria-label', `移除 ${file.name}`);
    remove.addEventListener('click', () => {
      state.files.splice(i, 1);
      renderFiles();
      refreshUI();
    });
    const chip = el('li', 'file-chip');
    chip.append(el('span', 'chip-name', file.name), remove);
    return chip;
  }));
}

/* ================= 上传与转换 ================= */

async function uploadAll() {
  const files = state.files;
  state.busy = true;
  markBusy(els.convertBtn, '转换中…');
  refreshUI();
  await Promise.allSettled(files.map(uploadOne));
  state.files = [];
  renderFiles();
  state.busy = false;
  markIdle(els.convertBtn, '转换为 Markdown');
  refreshUI();
}

async function uploadOne(file) {
  const tab = addPendingTab(file.name);
  try {
    const form = new FormData();
    form.append('file', file);
    form.append('config', els.configSelect.value);
    const res = await fetch('/api/upload', { method: 'POST', body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || '上传失败');
    }
    finalizeTab(tab, await res.json());
  } catch (e) {
    failTab(tab, `${file.name}:${e.message}`);
  }
}

/* ================= 生成与下载 ================= */

async function generate() {
  const tab = activeTab();
  if (!tab || tab.state !== 'ready' || state.busy) return;

  state.busy = true;
  markBusy(els.generateBtn, '生成中…');
  refreshUI();
  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: tab.sessionId, markdown: els.editor.value }),
    });
    if (res.status === 404) throw new Error('会话已过期,请重新上传该文档');
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || '生成失败');
    }
    const data = await res.json();

    tab.generated = true;
    tab.baseline = els.editor.value;
    tab.dirty = false;
    renderTabs();
    refreshUI();
    stampSeal();
    showToast(`已生成:${data.filename}`, 'success');
    triggerDownload(data.download_url, data.filename);
  } catch (e) {
    showToast(e.message);
  } finally {
    state.busy = false;
    markIdle(els.generateBtn, '生成并下载');
    refreshUI();
  }
}

function triggerDownload(url, filename) {
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

// 盖章:先砸下再停留片刻淡出
let sealTimer = 0;

function stampSeal() {
  clearTimeout(sealTimer);
  els.sealLayer.classList.remove('show', 'hide');
  void els.sealLayer.offsetWidth; // 重新触发动画
  els.sealLayer.classList.add('show');
  sealTimer = setTimeout(() => {
    els.sealLayer.classList.add('hide');
    sealTimer = setTimeout(() => els.sealLayer.classList.remove('show', 'hide'), 500);
  }, 1500);
}

/* ================= 一键整理 ================= */

// 幂等整理:统一换行、去行尾空白、收紧空行、修剪首尾
function formatMarkdown() {
  if (!activeTab()) return;
  els.editor.value = els.editor.value
    .replace(/\r\n?/g, '\n')
    .split('\n')
    .map(line => line.replace(/[ \t]+$/, ''))
    .join('\n')
    .replace(/\n{2,}/g, '\n')
    .replace(/^\n+|\n+$/g, '');
  onEditorInput();
}

/* ================= 配置加载 ================= */

async function loadConfigs() {
  let configs = [];
  try {
    const res = await fetch('/api/configs');
    if (res.ok) configs = (await res.json()).configs ?? [];
  } catch { /* 接口不可用时回退默认 */ }
  if (!configs.length) configs = [{ name: '默认配置', filename: 'default.toml' }];
  els.configSelect.replaceChildren(...configs.map(c => new Option(c.name, c.filename)));
}

/* ================= 事件绑定 ================= */

function initDropZone() {
  els.dropZone.addEventListener('click', () => els.fileInput.click());
  els.dropZone.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      els.fileInput.click();
    }
  });
  els.dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    els.dropZone.classList.add('drag-over');
  });
  els.dropZone.addEventListener('dragleave', () => els.dropZone.classList.remove('drag-over'));
  els.dropZone.addEventListener('drop', e => {
    e.preventDefault();
    e.stopPropagation(); // 避免与窗口级 drop 重复添加
    els.dropZone.classList.remove('drag-over');
    addFiles(e.dataTransfer.files);
  });
  els.fileInput.addEventListener('change', () => {
    addFiles(els.fileInput.files);
    els.fileInput.value = '';
  });

  // 拖到页面任意位置均可接收,同时阻止浏览器直接打开文件
  window.addEventListener('dragover', e => e.preventDefault());
  window.addEventListener('drop', e => {
    e.preventDefault();
    addFiles(e.dataTransfer.files);
  });
}

function initTabs() {
  els.tabBar.addEventListener('click', e => {
    const item = e.target.closest('.tab-item');
    if (!item) return;
    const index = Number(item.dataset.index);
    if (e.target.closest('.tab-close')) closeTab(index);
    else switchTab(index);
  });

  // 左右方向键切换标签(ARIA 标签列表模式)
  els.tabBar.addEventListener('keydown', e => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    e.preventDefault();
    const delta = e.key === 'ArrowLeft' ? -1 : 1;
    const next = Math.min(state.tabs.length - 1, Math.max(0, state.activeIndex + delta));
    switchTab(next);
    els.tabBar.querySelector(`[data-index="${next}"]`)?.focus();
  });
}

function initShortcuts() {
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (!els.generateBtn.disabled) generate();
    }
  });
}

/* ================= 启动 ================= */

initTheme();
initDropZone();
initTabs();
initShortcuts();
els.convertBtn.addEventListener('click', uploadAll);
els.generateBtn.addEventListener('click', generate);
els.formatBtn.addEventListener('click', formatMarkdown);
els.editor.addEventListener('input', onEditorInput);
loadConfigs();
