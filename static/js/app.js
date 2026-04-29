/**
 * app.js - Email Spam Detector Frontend Logic
 * ============================================
 * Features:
 *  - Health check on page load
 *  - Single email analysis with heatmap, stats, timer, PDF export
 *  - Batch CSV upload analysis
 *  - History log (last 5 analyses)
 *  - Dark/light mode toggle with localStorage
 *  - Live stats counter with count-up animation
 *  - Analysis speed timer
 *  - Ollama badge + AI reasoning display
 */

// ── Sample Texts ───────────────────────────────────────────────────────────
const EXAMPLES = {
  spam: `Congratulations! You've been SELECTED as our lucky winner! 🎉
You have won a FREE iPhone 15 Pro worth $1,199!
To claim your prize, click the link below IMMEDIATELY.
This offer expires in 24 hours. Don't miss out!
➡ http://claim-your-prize-now.xyz/?ref=lucky123
Act NOW before someone else takes your spot!`,

  ham: `Hi Sarah,

Following up on our meeting from yesterday regarding the Q4 marketing plan.
I've attached the revised budget spreadsheet with the changes we discussed.

Could you review section 3 on digital campaigns and let me know if the 
allocation looks right? I'd like to finalize everything before Thursday's 
presentation to the board.

Let me know if you have any questions.

Best regards,
James`
};

// ── Stats State ─────────────────────────────────────────────────────────────
let stats = {
  scanned: 0,
  spam: 0,
  ham: 0
};

// ── History State ────────────────────────────────────────────────────────────
let history = [];
let currentAnalysis = null;

// ── DOM References ─────────────────────────────────────────────────────────
const emailInput    = document.getElementById('emailInput');
const charCount     = document.getElementById('charCount');
const analyzeBtn    = document.getElementById('analyzeBtn');
const btnLoader     = document.getElementById('btnLoader');
const resultSection = document.getElementById('resultSection');
const resultCard    = document.getElementById('resultCard');
const healthBadge   = document.getElementById('healthBadge');
const healthText    = document.getElementById('healthText');
const themeToggle   = document.getElementById('themeToggle');

// ── Initialize ───────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  checkHealth();
});

// ────────────────────────────────────────────────────────────────────────────
// FEATURE 5: DARK / LIGHT MODE TOGGLE
// ────────────────────────────────────────────────────────────────────────────

function initTheme() {
  const savedTheme = localStorage.getItem('theme') || 'light';
  applyTheme(savedTheme);
}

function applyTheme(theme) {
  const html = document.documentElement;
  if (theme === 'dark') {
    html.classList.add('dark-mode');
    themeToggle.querySelector('.theme-icon').textContent = '☀️';
  } else {
    html.classList.remove('dark-mode');
    themeToggle.querySelector('.theme-icon').textContent = '🌙';
  }
  localStorage.setItem('theme', theme);
}

themeToggle.addEventListener('click', () => {
  const currentTheme = localStorage.getItem('theme') || 'light';
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  applyTheme(newTheme);
});

// ────────────────────────────────────────────────────────────────────────────
// FEATURE 1: WORD HEATMAP
// ────────────────────────────────────────────────────────────────────────────

function displayHeatmap(annotatedHtml) {
  const heatmapArea = document.getElementById('heatmapArea');
  const heatmapContent = document.getElementById('heatmapContent');
  
  if (annotatedHtml) {
    heatmapContent.innerHTML = annotatedHtml;
    heatmapArea.style.display = 'block';
  } else {
    heatmapArea.style.display = 'none';
  }
}

// ────────────────────────────────────────────────────────────────────────────
// FEATURE 4: LIVE STATS COUNTER
// ────────────────────────────────────────────────────────────────────────────

function updateStats(isSpam) {
  stats.scanned++;
  if (isSpam) {
    stats.spam++;
  } else {
    stats.ham++;
  }
  renderStats();
}

function renderStats() {
  animateCounter('statScanned', stats.scanned);
  animateCounter('statSpam', stats.spam);
  animateCounter('statHam', stats.ham);
  
  const rate = stats.scanned > 0 ? Math.round((stats.spam / stats.scanned) * 100) : 0;
  document.getElementById('statRate').textContent = rate + '%';
}

function animateCounter(elementId, targetValue) {
  const element = document.getElementById(elementId);
  const currentValue = parseInt(element.textContent) || 0;
  
  if (currentValue === targetValue) return;
  
  const steps = 10;
  const increment = (targetValue - currentValue) / steps;
  let current = currentValue;
  let step = 0;
  
  const timer = setInterval(() => {
    step++;
    current += increment;
    
    if (step >= steps) {
      element.textContent = targetValue;
      clearInterval(timer);
    } else {
      element.textContent = Math.floor(current);
    }
  }, 20);
}

// ────────────────────────────────────────────────────────────────────────────
// FEATURE 2: HISTORY LOG
// ────────────────────────────────────────────────────────────────────────────

function addToHistory(email, prediction, confidence) {
  const item = {
    email,
    prediction,
    confidence,
    timestamp: Date.now()
  };
  
  history.unshift(item);
  if (history.length > 5) {
    history.pop();
  }
  
  renderHistory();
}

function renderHistory() {
  const historySection = document.getElementById('historySection');
  const historyList = document.getElementById('historyList');
  
  if (history.length === 0) {
    historySection.style.display = 'none';
    return;
  }
  
  historySection.style.display = 'block';
  historyList.innerHTML = '';
  
  history.forEach((item, index) => {
    const historyItem = document.createElement('div');
    historyItem.className = 'history-item';
    
    const preview = item.email.substring(0, 60) + (item.email.length > 60 ? '...' : '');
    const timeAgo = getTimeAgo(item.timestamp);
    const badge = item.prediction === 'spam' ? 'spam' : 'ham';
    const badgeText = item.prediction === 'spam' ? '⚠ SPAM' : '✓ HAM';
    
    historyItem.innerHTML = `
      <div class="history-text">${escapeHtml(preview)}</div>
      <div class="history-meta">
        <span class="history-badge ${badge}">${badgeText}</span>
        <span class="history-time">${Math.round(item.confidence * 100)}%</span>
        <span class="history-time">${timeAgo}</span>
      </div>
    `;
    
    historyItem.onclick = () => loadFromHistory(item.email);
    historyList.appendChild(historyItem);
  });
}

function getTimeAgo(timestamp) {
  const now = Date.now();
  const diff = now - timestamp;
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (seconds < 60) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return 'earlier';
}

function loadFromHistory(email) {
  emailInput.value = email;
  charCount.textContent = `${email.length} chars`;
  emailInput.focus();
  emailInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// ── Char Counter ───────────────────────────────────────────────────────────
emailInput.addEventListener('input', () => {
  const len = emailInput.value.length;
  charCount.textContent = `${len} char${len !== 1 ? 's' : ''}`;
});

// ────────────────────────────────────────────────────────────────────────────
// FEATURE 7: ANALYSIS SPEED TIMER
// ────────────────────────────────────────────────────────────────────────────

let analysisStartTime = null;

function displayTimer(milliseconds) {
  const timerDisplay = document.getElementById('timerDisplay');
  timerDisplay.textContent = `⏱️ Analyzed in ${milliseconds}ms`;
  timerDisplay.style.display = 'block';
}

// ────────────────────────────────────────────────────────────────────────────
// FEATURE 8: OLLAMA HYBRID LLM FALLBACK - BADGE & REASONING
// ────────────────────────────────────────────────────────────────────────────

function displayModelBadge(modelUsed, reasoning) {
  const modelBadge = document.getElementById('modelBadge');
  const reasoningBlock = document.getElementById('reasoningBlock');
  const reasoningText = document.getElementById('reasoningText');
  
  if (modelUsed === 'llama3.2') {
    modelBadge.className = 'model-badge deep-ai';
    modelBadge.textContent = '🧠 Deep AI (LLaMA)';
    modelBadge.style.display = 'inline-block';
    
    if (reasoning) {
      reasoningText.textContent = reasoning;
      reasoningBlock.style.display = 'flex';
    } else {
      reasoningBlock.style.display = 'none';
    }
    
    // Show escalation note
    const previewArea = document.getElementById('previewArea');
    const note = document.createElement('div');
    note.style.cssText = 'font-family: var(--mono); font-size: 0.75rem; color: var(--text-muted); margin-top: 8px; font-style: italic;';
    note.textContent = '⚡ Low confidence detected — escalated to LLaMA for deeper analysis';
    previewArea.after(note);
    
  } else {
    modelBadge.className = 'model-badge fast-ml';
    modelBadge.textContent = '⚡ Fast ML';
    modelBadge.style.display = 'inline-block';
    reasoningBlock.style.display = 'none';
  }
}

// ── Health Check ───────────────────────────────────────────────────────────
async function checkHealth() {
  try {
    const res  = await fetch('/health');
    const data = await res.json();
    if (data.status === 'ok' && data.model_loaded) {
      healthBadge.classList.add('online');
      healthText.textContent = 'API Online';
    } else {
      throw new Error('Model not loaded');
    }
  } catch {
    healthBadge.classList.add('offline');
    healthText.textContent = 'API Offline';
  }
}

// ── Load Example ───────────────────────────────────────────────────────────
function loadExample(type) {
  emailInput.value = EXAMPLES[type];
  charCount.textContent = `${emailInput.value.length} chars`;
  emailInput.focus();
}

// ── Clear ──────────────────────────────────────────────────────────────────
function clearAll() {
  emailInput.value = '';
  charCount.textContent = '0 chars';
  resultSection.style.display = 'none';
  resultCard.className = 'result-card';
  emailInput.focus();
}

// ── Show Error Toast ───────────────────────────────────────────────────────
function showToast(msg) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = `⚠ ${msg}`;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3200);
}

// ── Set Loading State ──────────────────────────────────────────────────────
function setLoading(loading) {
  analyzeBtn.disabled = loading;
  document.querySelector('.btn-icon').style.display = loading ? 'none' : 'inline';
  document.querySelector('.btn-text').style.display = loading ? 'none' : 'inline';
  btnLoader.style.display = loading ? 'inline-flex' : 'none';
}

// ── Display Result ─────────────────────────────────────────────────────────
function displayResult(data) {
  const isSpam = data.is_spam;
  const pct    = Math.round(data.confidence * 100);

  // Remove any old escalation notes
  const oldNote = document.querySelector('[style*="font-style: italic"]');
  if (oldNote) oldNote.remove();

  // Card class
  resultCard.className = `result-card ${isSpam ? 'is-spam' : 'is-ham'}`;

  // Icon
  document.getElementById('resultIcon').textContent = isSpam ? '🚨' : '✅';

  // Label + Verdict
  document.getElementById('resultLabel').textContent = 'CLASSIFICATION RESULT';
  document.getElementById('resultVerdict').textContent = isSpam
    ? '⚠ SPAM DETECTED'
    : '✓ LEGITIMATE EMAIL (Ham)';

  // Confidence
  document.getElementById('confidencePct').textContent = `${pct}%`;

  // Animate bar after paint
  const fill = document.getElementById('confidenceFill');
  fill.style.width = '0%';
  setTimeout(() => { fill.style.width = `${pct}%`; }, 60);

  // Preview
  const preview = data.processed_text_preview || '';
  if (preview) {
    document.getElementById('previewText').textContent = preview + '…';
    document.getElementById('previewArea').style.display = 'block';
  } else {
    document.getElementById('previewArea').style.display = 'none';
  }

  // Display heatmap (Feature 1)
  if (data.annotated_html) {
    displayHeatmap(data.annotated_html);
  }

  // Display model badge and reasoning (Feature 8)
  if (data.model_used) {
    displayModelBadge(data.model_used, data.reasoning);
  }

  // Show section
  resultSection.style.display = 'block';

  // Smooth scroll to result on mobile
  if (window.innerWidth <= 600) {
    setTimeout(() => resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 100);
  }

  // Store current analysis for PDF export
  currentAnalysis = {
    email: emailInput.value,
    prediction: data.prediction,
    confidence: data.confidence,
    confidencePct: pct,
    topWords: data.top_words || [],
    wordScores: data.word_scores || {},
    modelUsed: data.model_used,
    reasoning: data.reasoning
  };

  // Store in history (Feature 2)
  addToHistory(emailInput.value, data.prediction, data.confidence);

  // Update stats (Feature 4)
  updateStats(isSpam);
}

 function exportPDF() {
  if (!currentAnalysis) {
    showToast('No analysis to export.');
    return;
  }

  // ✅ FIXED IMPORT
  if (!window.jspdf || !window.jspdf.jsPDF) {
    alert("jsPDF not loaded properly");
    return;
  }

  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();

  const pageWidth = doc.internal.pageSize.getWidth();
  const margin = 15;
  const maxWidth = pageWidth - 2 * margin;
  let yPos = margin;

  const addWrappedText = (text, x, y, maxW, fontSize = 10) => {
    doc.setFontSize(fontSize);
    const lines = doc.splitTextToSize(text || "", maxW);
    doc.text(lines, x, y);
    return y + lines.length * 5;
  };

  // Header
  doc.setFont(undefined, 'bold');
  doc.setFontSize(18);
  doc.text('The Spam Examiner', margin, yPos);
  yPos += 8;
  doc.text('Analysis Report', margin, yPos);
  yPos += 12;

  // Date
  doc.setFont(undefined, 'normal');
  doc.setFontSize(10);
  const now = new Date().toLocaleString();
  yPos = addWrappedText(`Generated: ${now}`, margin, yPos, maxWidth);
  yPos += 4;

  // Verdict
  doc.setFont(undefined, 'bold');
  doc.setFontSize(14);
  const verdict = currentAnalysis.prediction === 'spam' ? 'SPAM' : 'LEGITIMATE (HAM)';
  const verdictColor = currentAnalysis.prediction === 'spam' ? [230, 57, 70] : [46, 192, 96];
  doc.setTextColor(...verdictColor);
  yPos = addWrappedText(`Verdict: ${verdict}`, margin, yPos, maxWidth);
  yPos += 6;

  // Confidence
  doc.setTextColor(0, 0, 0);
  doc.setFont(undefined, 'normal');
  doc.setFontSize(10);
  yPos = addWrappedText(`Confidence: ${currentAnalysis.confidencePct || ""}`, margin, yPos, maxWidth);
  yPos += 8;

  // Email content
  doc.setFont(undefined, 'bold');
  doc.setFontSize(11);
  yPos = addWrappedText('Email Content:', margin, yPos, maxWidth);
  doc.setFont(undefined, 'normal');
  doc.setFontSize(9);
  yPos += 2;
  yPos = addWrappedText(currentAnalysis.email || "", margin, yPos, maxWidth);
  yPos += 10;

  // Top words
  if (currentAnalysis.topWords && currentAnalysis.topWords.length > 0) {
    doc.setFont(undefined, 'bold');
    doc.setFontSize(11);
    yPos = addWrappedText('Top Trigger Words:', margin, yPos, maxWidth);

    doc.setFont(undefined, 'normal');
    doc.setFontSize(9);
    yPos += 2;

    currentAnalysis.topWords.slice(0, 5).forEach(word => {
      const score = currentAnalysis.wordScores?.[word] || 0;
      yPos = addWrappedText(`• ${word} (${score.toFixed(3)})`, margin, yPos, maxWidth);
    });

    yPos += 5;
  }

  // Save
  const fileName = `spam_analysis_${Date.now()}.pdf`;
  doc.save(fileName);

  showToast(`PDF exported as ${fileName}`);
}
// ────────────────────────────────────────────────────────────────────────────
// FEATURE 3: BATCH CSV UPLOAD
// ────────────────────────────────────────────────────────────────────────────

function switchTab(tab) {
  const singleContent = document.getElementById('singleTab-content');
  const batchContent = document.getElementById('batchTab-content');
  const singleTab = document.getElementById('singleTab');
  const batchTab = document.getElementById('batchTab');

  if (tab === 'single') {
    singleContent.style.display = 'block';
    batchContent.style.display = 'none';
    singleTab.classList.add('active');
    batchTab.classList.remove('active');
  } else {
    singleContent.style.display = 'none';
    batchContent.style.display = 'block';
    singleTab.classList.remove('active');
    batchTab.classList.add('active');
  }
}

async function analyzeBatch() {
  const csvFile = document.getElementById('csvFile').files[0];

  if (!csvFile) {
    showToast('Please select a CSV file.');
    return;
  }

  if (!csvFile.name.toLowerCase().endsWith('.csv')) {
    showToast('File must be a CSV.');
    return;
  }

  const batchBtn = document.getElementById('batchBtn');
  const batchLoader = document.getElementById('batchLoader');
  
  batchBtn.disabled = true;
  batchLoader.style.display = 'inline-flex';

  try {
    const formData = new FormData();
    formData.append('file', csvFile);

    const response = await fetch('/predict_batch', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (!response.ok) {
      showToast(data.error || 'Batch processing failed.');
      return;
    }

    displayBatchResults(data);

  } catch (err) {
    console.error('Batch API error:', err);
    showToast('Could not reach the server.');
  } finally {
    batchBtn.disabled = false;
    batchLoader.style.display = 'none';
  }
}

function displayBatchResults(data) {
  const batchResults = document.getElementById('batchResults');
  const batchSummary = document.getElementById('batchSummary');
  const batchTableBody = document.getElementById('batchTableBody');

  // Summary
  batchSummary.innerHTML = `
    ✅ Scanned ${data.total} emails — 
    <span style="color: var(--spam);">⚠️ ${data.spam_count} spam</span>, 
    <span style="color: var(--ham);">✓ ${data.ham_count} ham</span>
    (${data.spam_rate}% spam rate)
  `;

  // Table
  batchTableBody.innerHTML = '';
  data.results.forEach((result) => {
    const row = document.createElement('tr');
    const verdict = result.prediction === 'spam' ? '⚠ SPAM' : '✓ HAM';
    const verdictClass = result.prediction === 'spam' ? 'spam' : 'ham';
    const confidence = Math.round(result.confidence * 100);

    row.innerHTML = `
      <td>${escapeHtml(result.email_preview)}</td>
      <td><span class="batch-verdict ${verdictClass}">${verdict}</span></td>
      <td>${confidence}%</td>
    `;
    batchTableBody.appendChild(row);
  });

  batchResults.style.display = 'block';

  // Update stats
  data.results.forEach((result) => {
    stats.scanned++;
    if (result.is_spam) {
      stats.spam++;
    } else {
      stats.ham++;
    }
  });
  renderStats();
}

function downloadBatchResults() {
  const tableBody = document.getElementById('batchTableBody');
  const rows = tableBody.querySelectorAll('tr');

  if (rows.length === 0) {
    showToast('No results to download.');
    return;
  }

  // Build CSV
  let csv = 'Email Preview,Verdict,Confidence\n';
  rows.forEach((row) => {
    const cells = row.querySelectorAll('td');
    const email = cells[0].textContent.trim();
    const verdict = cells[1].textContent.trim();
    const confidence = cells[2].textContent.trim();
    csv += `"${email.replace(/"/g, '""')}","${verdict}","${confidence}"\n`;
  });

  // Download
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `batch_results_${Date.now()}.csv`;
  a.click();
  window.URL.revokeObjectURL(url);

  showToast('Results downloaded.');
}

// ── Main Analyze Function ──────────────────────────────────────────────────
async function analyzeEmail() {
  const text = emailInput.value.trim();

  // Client-side validation
  if (!text) {
    showToast('Please enter an email to analyze.');
    emailInput.focus();
    return;
  }

  if (text.length < 5) {
    showToast('Email text is too short. Please enter more content.');
    return;
  }

  setLoading(true);
  analysisStartTime = performance.now();

  try {
    const response = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: text })
    });

    const analysisEndTime = performance.now();
    const analysisTime = Math.round(analysisEndTime - analysisStartTime);

    const data = await response.json();

    if (!response.ok) {
      showToast(data.error || 'Server error. Please try again.');
      return;
    }

    // Display timer (Feature 7)
    displayTimer(analysisTime);

    displayResult(data);

  } catch (err) {
    console.error('API error:', err);
    showToast('Could not reach the server. Is Flask running?');
  } finally {
    setLoading(false);
  }
}

// ── Keyboard Shortcut: Ctrl+Enter ─────────────────────────────────────────
emailInput.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    analyzeEmail();
  }
});

// ── Utility ────────────────────────────────────────────────────────────────
function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

// ── Init ───────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
});