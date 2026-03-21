/* MoodBeats AI — Webcam capture logic (detect.html only) */

let _stream   = null;
let _captured = false;

const video    = () => document.getElementById('webcam-video');
const canvas   = () => document.getElementById('capture-canvas');
const preview  = () => document.getElementById('capture-preview');
const imgInput = () => document.getElementById('image-data-input');
const startBtn = () => document.getElementById('start-camera-btn');
const capBtn   = () => document.getElementById('capture-btn');
const analyzeBtn = () => document.getElementById('analyze-btn');

// ── Start webcam ──────────────────────────────────────────────────────────────
async function startWebcam() {
  const placeholder = document.getElementById('webcam-placeholder');
  const container   = document.getElementById('webcam-container');

  try {
    _stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
      audio: false,
    });
    video().srcObject = _stream;
    await video().play();

    placeholder.classList.add('hidden');
    container.classList.remove('hidden');
    startBtn().classList.add('hidden');
    capBtn().classList.remove('hidden');
  } catch (err) {
    showToast('Camera access denied. Switch to the Text tab or allow camera access.', 'error');
    console.error('getUserMedia error:', err);
  }
}

// ── Capture frame ─────────────────────────────────────────────────────────────
function captureFrame() {
  const v = video();
  const c = canvas();
  c.width  = v.videoWidth  || 640;
  c.height = v.videoHeight || 480;
  c.getContext('2d').drawImage(v, 0, 0);

  const dataUrl = c.toDataURL('image/jpeg', 0.85);
  imgInput().value = dataUrl;

  // Show captured preview instead of live feed
  preview().src = dataUrl;
  preview().classList.remove('hidden');
  v.classList.add('hidden');

  capBtn().textContent = '📷 Retake';
  _captured = true;

  // Enable analyse button
  const ab = analyzeBtn();
  ab.disabled = false;
  ab.classList.remove('opacity-40', 'cursor-not-allowed');
}

// ── Retake ────────────────────────────────────────────────────────────────────
function retakePhoto() {
  preview().classList.add('hidden');
  video().classList.remove('hidden');
  capBtn().textContent = '📸 Capture';
  imgInput().value = '';
  _captured = false;

  const ab = analyzeBtn();
  ab.disabled = true;
  ab.classList.add('opacity-40', 'cursor-not-allowed');
}

// ── Capture button click (toggle) ─────────────────────────────────────────────
function onCaptureClick() {
  if (_captured) retakePhoto();
  else captureFrame();
}

// ── Submit face form ──────────────────────────────────────────────────────────
function submitFaceForm() {
  if (!imgInput().value) {
    showToast('Please capture a photo first.', 'error');
    return;
  }
  showLoading('Reading your facial expression…');
  document.getElementById('input-type').value = 'face';
  document.getElementById('detect-form').submit();
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  startBtn()?.addEventListener('click', startWebcam);
  capBtn()?.addEventListener('click', onCaptureClick);
  analyzeBtn()?.addEventListener('click', submitFaceForm);
});

// ── Stop camera when navigating away ─────────────────────────────────────────
window.addEventListener('beforeunload', () => {
  if (_stream) _stream.getTracks().forEach(t => t.stop());
});
