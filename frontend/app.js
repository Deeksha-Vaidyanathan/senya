const API = "http://localhost:8000";

// Tab switching
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(`tab-${tab.dataset.tab}`).classList.add("active");
  });
});

// Drag-and-drop on upload area
const uploadLabel = document.getElementById("upload-label");
const uploadText = document.getElementById("upload-text");
const fileInput = document.getElementById("video-file");

uploadLabel.addEventListener("dragover", e => {
  e.preventDefault();
  uploadLabel.classList.add("drag-over");
});
uploadLabel.addEventListener("dragleave", () => uploadLabel.classList.remove("drag-over"));
uploadLabel.addEventListener("drop", e => {
  e.preventDefault();
  uploadLabel.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) { fileInput.files = e.dataTransfer.files; uploadText.textContent = file.name; }
});
fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) uploadText.textContent = fileInput.files[0].name;
});

// Submit
document.getElementById("submit-btn").addEventListener("click", async () => {
  const activeTab = document.querySelector(".tab.active").dataset.tab;
  const position = document.getElementById("pip-position").value;

  if (activeTab === "url") {
    const url = document.getElementById("video-url").value.trim();
    if (!url) return alert("Please enter a video URL.");
    await runPipeline(() => processUrl(url, position));
  } else {
    const file = fileInput.files[0];
    if (!file) return alert("Please select a video file.");
    await runPipeline(() => processUpload(file, position));
  }
});

document.getElementById("retry-btn").addEventListener("click", () => {
  hide("error-box"); hide("result-section");
});

async function processUrl(url, position) {
  const resp = await fetch(`${API}/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_url: url, pip_position: position }),
  });
  if (!resp.ok) throw new Error((await resp.json()).detail || "Server error");
  return resp.json();
}

async function processUpload(file, position) {
  const form = new FormData();
  form.append("file", file);
  const resp = await fetch(`${API}/process/upload?pip_position=${position}`, {
    method: "POST",
    body: form,
  });
  if (!resp.ok) throw new Error((await resp.json()).detail || "Server error");
  return resp.json();
}

async function runPipeline(fn) {
  const btn = document.getElementById("submit-btn");
  btn.disabled = true;
  show("result-section"); show("loader"); hide("output"); hide("error-box");

  const steps = [
    "Adding captions to source video...",
    "Converting to ASL gloss...",
    "Looking up sign clips...",
    "Overlaying ASL avatar...",
  ];
  let stepIdx = 0;
  const loaderText = document.getElementById("loader-text");
  loaderText.textContent = steps[0];
  const ticker = setInterval(() => {
    stepIdx = Math.min(stepIdx + 1, steps.length - 1);
    loaderText.textContent = steps[stepIdx];
  }, 8000);

  try {
    const result = await fn();
    clearInterval(ticker);
    showResult(result);
  } catch (err) {
    clearInterval(ticker);
    hide("loader");
    show("error-box");
    document.getElementById("error-text").textContent = err.message;
  } finally {
    btn.disabled = false;
  }
}

function showResult(result) {
  hide("loader");
  show("output");

  const video = document.getElementById("output-video");
  video.src = result.output_url;
  video.load();

  document.getElementById("meta-transcript").textContent = result.transcript;
  document.getElementById("meta-gloss").textContent = result.gloss.join(" ");
  document.getElementById("meta-coverage").textContent =
    `${result.signs_found} / ${result.signs_total} signs matched` +
    (result.missing_signs.length ? ` (missing: ${result.missing_signs.join(", ")})` : "");

  const dl = document.getElementById("download-btn");
  dl.href = result.output_url;
}

function show(id) { document.getElementById(id).classList.remove("hidden"); }
function hide(id) { document.getElementById(id).classList.add("hidden"); }
