/**
 * Prediction History Controller.
 * Handles user-restricted prediction records, risk filtering, pagination,
 * detail modal viewer, and record deletion.
 */

import { requireAuth } from './auth.js';
import { historyAPI } from './api.js';
import { showToast, formatDateTime, openModal, closeModal } from './ui.js';

let currentPage = 1;
let currentRisk = 'all';

export async function initHistoryPage() {
  await requireAuth();

  // Setup risk filter tabs
  const filterBtns = document.querySelectorAll('.risk-filter-btn');
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentRisk = btn.dataset.risk || 'all';
      currentPage = 1;
      loadHistory();
    });
  });

  // Setup pagination buttons
  const prevBtn = document.getElementById('hist-prev-btn');
  const nextBtn = document.getElementById('hist-next-btn');

  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        loadHistory();
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      currentPage++;
      loadHistory();
    });
  }

  loadHistory();
}

async function loadHistory() {
  const tbody = document.getElementById('history-tbody');
  const emptyState = document.getElementById('history-empty-state');
  const paginationControls = document.getElementById('history-pagination');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 2rem;"><span class="spinner spinner-primary"></span> Loading records...</td></tr>';

  try {
    const res = await historyAPI.getAll({ page: currentPage, per_page: 8, risk: currentRisk });
    const { items, pagination } = res.data;

    tbody.innerHTML = '';

    if (!items || items.length === 0) {
      if (emptyState) emptyState.style.display = 'block';
      if (paginationControls) paginationControls.style.display = 'none';
      return;
    }

    if (emptyState) emptyState.style.display = 'none';
    if (paginationControls) paginationControls.style.display = 'flex';

    items.forEach(item => {
      const tr = document.createElement('tr');

      // Date
      const tdDate = document.createElement('td');
      tdDate.textContent = formatDateTime(item.created_at);
      tr.appendChild(tdDate);

      // Patient Details & Vitals
      const tdVitals = document.createElement('td');
      const feats = item.validated_features || {};
      const sexLabel = feats.sex === 1 ? 'Male' : 'Female';
      const patientName = item.patient_name || 'Anonymous Patient';
      const phoneText = item.patient_phone ? ` | 📞 ${item.patient_phone}` : '';
      tdVitals.innerHTML = `
        <div style="font-weight: 700; color: var(--text-main);">${escapeHtml(patientName)}</div>
        <small class="text-muted">${feats.age || 'N/A'} yrs, ${sexLabel} | BP: ${feats.trestbps || 'N/A'}${escapeHtml(phoneText)}</small>
      `;
      tr.appendChild(tdVitals);

      // Prediction
      const tdPred = document.createElement('td');
      tdPred.textContent = item.prediction_label || (item.prediction === 1 ? 'Disease Risk' : 'No Disease');
      tr.appendChild(tdPred);

      // Risk Badge
      const tdRisk = document.createElement('td');
      const badge = document.createElement('span');
      badge.className = item.prediction === 1 ? 'badge risk-high' : 'badge risk-low';
      badge.textContent = item.risk_level || (item.prediction === 1 ? 'Elevated' : 'Low');
      tdRisk.appendChild(badge);
      tr.appendChild(tdRisk);

      // Probability
      const tdProb = document.createElement('td');
      tdProb.textContent = typeof item.probability === 'number'
        ? `${(item.probability * 100).toFixed(1)}%`
        : 'N/A';
      tr.appendChild(tdProb);

      // Actions (View & Delete)
      const tdActions = document.createElement('td');
      tdActions.style.display = 'flex';
      tdActions.style.gap = '0.5rem';

      const viewBtn = document.createElement('button');
      viewBtn.className = 'btn btn-outline btn-sm';
      viewBtn.textContent = 'Inspect';
      viewBtn.onclick = () => showDetailModal(item);
      tdActions.appendChild(viewBtn);

      const deleteBtn = document.createElement('button');
      deleteBtn.className = 'btn btn-outline btn-sm';
      deleteBtn.style.color = 'var(--danger)';
      deleteBtn.innerHTML = '🗑️';
      deleteBtn.title = 'Delete Record';
      deleteBtn.onclick = () => confirmDelete(item.id);
      tdActions.appendChild(deleteBtn);

      tr.appendChild(tdActions);
      tbody.appendChild(tr);
    });

    // Update pagination status
    const pageIndicator = document.getElementById('page-indicator');
    if (pageIndicator) {
      pageIndicator.textContent = `Page ${pagination.page} of ${pagination.total_pages}`;
    }

    const prevBtn = document.getElementById('hist-prev-btn');
    const nextBtn = document.getElementById('hist-next-btn');
    if (prevBtn) prevBtn.disabled = !pagination.has_prev;
    if (nextBtn) nextBtn.disabled = !pagination.has_next;

  } catch (err) {
    showToast('Failed to load history: ' + err.message, 'error');
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function showDetailModal(item) {
  const modalContent = document.getElementById('modal-detail-content');
  if (!modalContent) return;

  const feats = item.validated_features || {};
  modalContent.innerHTML = `
    <!-- Patient Demographic Card -->
    <div style="background: #f8fafc; border: 1px solid var(--light-border); border-radius: var(--radius-md); padding: 1rem; margin-bottom: 1.25rem;">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
        <div>
          <span style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700;">Patient Identification</span>
          <h3 style="margin: 0.2rem 0; font-size: 1.25rem; color: var(--text-main);">${escapeHtml(item.patient_name || 'Anonymous Patient')}</h3>
        </div>
        <span class="badge ${item.prediction === 1 ? 'risk-high' : 'risk-low'}">${item.risk_level || 'Prediction'}</span>
      </div>
      <div style="font-size: 0.88rem; color: var(--text-muted); display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.5rem;">
        <div><strong>Phone:</strong> ${escapeHtml(item.patient_phone || 'Not provided')}</div>
        <div><strong>Analyzed:</strong> ${formatDateTime(item.created_at)}</div>
        <div style="grid-column: 1 / -1;"><strong>Address:</strong> ${escapeHtml(item.patient_address || 'Not provided')}</div>
      </div>
    </div>

    <div style="margin-bottom: 1rem;">
      <h4 style="margin: 0 0 0.25rem 0; color: ${item.prediction === 1 ? 'var(--danger)' : 'var(--success)'};">${item.prediction_label}</h4>
      <p class="text-muted" style="font-size: 0.9rem;">Estimated Heart Disease Probability: <strong>${typeof item.probability === 'number' ? (item.probability * 100).toFixed(1) + '%' : 'N/A'}</strong></p>
    </div>
    <div class="table-wrapper">
      <table class="table">
        <thead>
          <tr><th>Clinical Attribute</th><th>Patient Value</th></tr>
        </thead>
        <tbody>
          <tr><td>Age</td><td>${feats.age} years</td></tr>
          <tr><td>Sex</td><td>${feats.sex === 1 ? 'Male (1)' : 'Female (0)'}</td></tr>
          <tr><td>Chest Pain Type (cp)</td><td>${feats.cp}</td></tr>
          <tr><td>Resting Blood Pressure (trestbps)</td><td>${feats.trestbps} mm Hg</td></tr>
          <tr><td>Serum Cholesterol (chol)</td><td>${feats.chol} mg/dl</td></tr>
          <tr><td>Fasting Blood Sugar > 120 (fbs)</td><td>${feats.fbs === 1 ? 'True' : 'False'}</td></tr>
          <tr><td>Resting ECG (restecg)</td><td>${feats.restecg}</td></tr>
          <tr><td>Max Heart Rate (thalach)</td><td>${feats.thalach} bpm</td></tr>
          <tr><td>Exercise-Induced Angina (exang)</td><td>${feats.exang === 1 ? 'Yes' : 'No'}</td></tr>
          <tr><td>ST Depression (oldpeak)</td><td>${feats.oldpeak} mm</td></tr>
          <tr><td>ST Slope (slope)</td><td>${feats.slope}</td></tr>
          <tr><td>Major Vessels (ca)</td><td>${feats.ca}</td></tr>
          <tr><td>Thalassemia Status (thal)</td><td>${feats.thal}</td></tr>
        </tbody>
      </table>
    </div>
  `;

  openModal('history-detail-modal');
}

async function confirmDelete(predictionId) {
  if (!confirm('Are you sure you want to delete this prediction record? This cannot be undone.')) {
    return;
  }

  try {
    await historyAPI.delete(predictionId);
    showToast('Record deleted successfully.', 'success');
    loadHistory();
  } catch (err) {
    showToast('Delete failed: ' + err.message, 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('history-table-container')) {
    initHistoryPage();
  }
});
