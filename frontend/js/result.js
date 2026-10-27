/**
 * Prediction Result and Clinical Interpretation Controller.
 * Displays risk probability meter, diagnostic breakdown, and 13-feature recap.
 */

import { requireAuth } from './auth.js';
import { historyAPI } from './api.js';
import { showToast, formatDateTime } from './ui.js';

export async function initResultPage() {
  await requireAuth();

  const urlParams = new URLSearchParams(window.location.search);
  const predictionId = urlParams.get('id');

  let data = null;

  // First check if current result is cached in sessionStorage
  const cached = sessionStorage.getItem('current_prediction');
  if (cached) {
    try {
      const parsed = JSON.parse(cached);
      if (!predictionId || parsed.id === predictionId) {
        data = parsed;
      }
    } catch {
      data = null;
    }
  }

  // If not cached or viewing historical prediction by ID, fetch from API
  if (!data && predictionId) {
    try {
      const res = await historyAPI.getById(predictionId);
      data = res.data?.prediction;
    } catch (err) {
      showToast('Could not load prediction: ' + err.message, 'error');
      renderErrorState();
      return;
    }
  }

  if (!data) {
    renderEmptyState();
    return;
  }

  renderResult(data);
}

function renderResult(data) {
  const isDisease = data.prediction === 1;
  const prob = typeof data.probability === 'number' ? data.probability : (isDisease ? 0.85 : 0.15);
  const probPercent = (prob * 100).toFixed(1);

  // Result Banner & Badges
  const badgeEl = document.getElementById('result-risk-badge');
  if (badgeEl) {
    badgeEl.className = isDisease ? 'badge risk-high' : 'badge risk-low';
    badgeEl.textContent = data.risk_level || (isDisease ? 'Elevated Cardiac Risk' : 'Low Cardiac Risk');
  }

  const titleEl = document.getElementById('result-title');
  if (titleEl) {
    titleEl.textContent = data.prediction_label || (isDisease ? 'Heart Disease Indicator Detected' : 'No Heart Disease Detected');
    titleEl.style.color = isDisease ? 'var(--danger)' : 'var(--success)';
  }

  const probTextEl = document.getElementById('result-prob-value');
  if (probTextEl) {
    probTextEl.textContent = `${probPercent}%`;
  }

  const probBarEl = document.getElementById('result-prob-bar');
  if (probBarEl) {
    probBarEl.style.width = `${probPercent}%`;
    probBarEl.style.backgroundColor = isDisease ? 'var(--danger)' : 'var(--success)';
  }

  const modelVerEl = document.getElementById('result-model-version');
  if (modelVerEl) {
    modelVerEl.textContent = `v${data.model_version || '1.0.0'} (${data.model_architecture || 'StackingClassifier'})`;
  }

  const dateEl = document.getElementById('result-timestamp');
  if (dateEl) {
    dateEl.textContent = formatDateTime(data.created_at);
  }

  // Populate Patient Demographic Details
  const nameEl = document.getElementById('result-patient-name');
  if (nameEl) {
    nameEl.textContent = data.patient_name || 'Anonymous Patient';
  }

  const phoneEl = document.getElementById('result-patient-phone');
  if (phoneEl) {
    phoneEl.textContent = data.patient_phone || 'Not provided';
  }

  const addressEl = document.getElementById('result-patient-address');
  if (addressEl) {
    addressEl.textContent = data.patient_address || 'Not provided';
  }

  // Render 13-feature input table
  renderFeatureTable(data.validated_features || {});
}

function renderFeatureTable(feats) {
  const tbody = document.getElementById('result-features-tbody');
  if (!tbody) return;

  tbody.innerHTML = '';

  const featureDefinitions = [
    { key: 'age', name: 'Age', unit: 'years', normal: '18 - 100' },
    { key: 'sex', name: 'Sex', unit: '', normal: 'Male / Female', format: v => v === 1 ? 'Male (1)' : 'Female (0)' },
    { key: 'cp', name: 'Chest Pain Type', unit: '', normal: '1 to 4', format: v => {
      const m = { 1: 'Typical Angina (1)', 2: 'Atypical Angina (2)', 3: 'Non-anginal Pain (3)', 4: 'Asymptomatic (4)' };
      return m[v] || v;
    }},
    { key: 'trestbps', name: 'Resting Blood Pressure', unit: 'mm Hg', normal: '90 - 120 mm Hg' },
    { key: 'chol', name: 'Serum Cholesterol', unit: 'mg/dl', normal: '< 200 mg/dl' },
    { key: 'fbs', name: 'Fasting Blood Sugar > 120 mg/dl', unit: '', normal: 'False (<= 120)', format: v => v === 1 ? 'True (> 120 mg/dl)' : 'False (<= 120 mg/dl)' },
    { key: 'restecg', name: 'Resting ECG', unit: '', normal: '0: Normal', format: v => {
      const m = { 0: 'Normal (0)', 1: 'ST-T Wave Abnormality (1)', 2: 'Left Ventricular Hypertrophy (2)' };
      return m[v] || v;
    }},
    { key: 'thalach', name: 'Max Heart Rate Achieved', unit: 'bpm', normal: '70 - 200 bpm' },
    { key: 'exang', name: 'Exercise-Induced Angina', unit: '', normal: 'No (0)', format: v => v === 1 ? 'Yes (1)' : 'No (0)' },
    { key: 'oldpeak', name: 'ST Depression (Oldpeak)', unit: 'mm', normal: '0.0 - 1.0 mm' },
    { key: 'slope', name: 'Peak ST Slope', unit: '', normal: '1: Upsloping', format: v => {
      const m = { 1: 'Upsloping (1)', 2: 'Flat (2)', 3: 'Downsloping (3)' };
      return m[v] || v;
    }},
    { key: 'ca', name: 'Major Vessels Colored (Fluoroscopy)', unit: 'vessels', normal: '0 vessels' },
    { key: 'thal', name: 'Thalassemia Status', unit: '', normal: '3: Normal', format: v => {
      const m = { 3: 'Normal (3)', 6: 'Fixed Defect (6)', 7: 'Reversible Defect (7)' };
      return m[v] || v;
    }}
  ];

  featureDefinitions.forEach(item => {
    const val = feats[item.key];
    const displayVal = item.format ? item.format(val) : `${val} ${item.unit}`.trim();

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${item.name}</strong></td>
      <td><span class="badge badge-primary">${displayVal}</span></td>
      <td><small class="text-muted">${item.normal}</small></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderEmptyState() {
  const container = document.getElementById('result-container');
  if (container) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📋</div>
        <h2 class="empty-state-title">No Prediction Report Found</h2>
        <p class="empty-state-text">You haven't run a prediction yet or the requested record does not exist.</p>
        <a href="predict.html" class="btn btn-primary">Run New Prediction</a>
      </div>
    `;
  }
}

function renderErrorState() {
  const container = document.getElementById('result-container');
  if (container) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">⚠️</div>
        <h2 class="empty-state-title">Unable to Load Report</h2>
        <p class="empty-state-text">The requested prediction record could not be loaded or you do not have permission to view it.</p>
        <a href="history.html" class="btn btn-outline">Back to History</a>
      </div>
    `;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('result-container')) {
    initResultPage();
  }
});
