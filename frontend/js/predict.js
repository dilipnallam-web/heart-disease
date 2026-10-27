/**
 * Medical Prediction Form Controller.
 * Handles realtime range sliders, input boundary validation,
 * and calls POST /api/predict.
 */

import { requireAuth } from './auth.js';
import { predictAPI } from './api.js';
import { showToast } from './ui.js';

export async function initPredictPage() {
  await requireAuth();

  const form = document.getElementById('heart-prediction-form');
  if (!form) return;

  // Bind live slider display updates
  bindRangeBadge('age', 'age-badge', 'yrs');
  bindRangeBadge('trestbps', 'trestbps-badge', 'mmHg');
  bindRangeBadge('chol', 'chol-badge', 'mg/dl');
  bindRangeBadge('thalach', 'thalach-badge', 'bpm');
  bindRangeBadge('oldpeak', 'oldpeak-badge', 'mm');

  // Form submission
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;

    const patientName = form.patient_name ? form.patient_name.value.trim() : '';
    const patientPhone = form.patient_phone ? form.patient_phone.value.trim() : '';
    const patientAddress = form.patient_address ? form.patient_address.value.trim() : '';

    if (!patientName) {
      showToast('Please enter the patient name.', 'error');
      if (form.patient_name) form.patient_name.focus();
      return;
    }

    if (!patientPhone) {
      showToast('Please enter the patient phone number.', 'error');
      if (form.patient_phone) form.patient_phone.focus();
      return;
    }

    if (!patientAddress) {
      showToast('Please enter the patient address.', 'error');
      if (form.patient_address) form.patient_address.focus();
      return;
    }

    // Collect and format features exactly matching UCI schema
    const payload = {
      patient_name: patientName,
      patient_phone: patientPhone,
      patient_address: patientAddress,
      age: parseFloat(form.age.value),
      sex: parseInt(form.sex.value, 10),
      cp: parseInt(form.cp.value, 10),
      trestbps: parseFloat(form.trestbps.value),
      chol: parseFloat(form.chol.value),
      fbs: parseInt(form.fbs.value, 10),
      restecg: parseInt(form.restecg.value, 10),
      thalach: parseFloat(form.thalach.value),
      exang: parseInt(form.exang.value, 10),
      oldpeak: parseFloat(form.oldpeak.value),
      slope: parseInt(form.slope.value, 10),
      ca: parseInt(form.ca.value, 10),
      thal: parseInt(form.thal.value, 10)
    };

    // Client-side quick checks for numeric features
    const numericKeys = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal'];
    for (const key of numericKeys) {
      if (isNaN(payload[key])) {
        showToast(`Please complete the feature: ${key}`, 'error');
        return;
      }
    }

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span> Running Stacking Ensemble...';

      const res = await predictAPI.predict(payload);
      const resultData = res.data;

      // Store in session storage for immediate result presentation
      sessionStorage.setItem('current_prediction', JSON.stringify(resultData));

      showToast('Analysis completed successfully!', 'success');
      setTimeout(() => {
        window.location.href = `result.html?id=${resultData.id || ''}`;
      }, 500);

    } catch (err) {
      showToast(err.message, 'error');
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  });
}

function bindRangeBadge(inputId, badgeId, unit = '') {
  const input = document.getElementById(inputId);
  const badge = document.getElementById(badgeId);
  if (!input || !badge) return;

  const update = () => {
    badge.textContent = `${input.value} ${unit}`.trim();
  };

  input.addEventListener('input', update);
  update(); // Initial call
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('heart-prediction-form')) {
    initPredictPage();
  }
});
