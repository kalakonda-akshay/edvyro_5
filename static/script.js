/**
 * InternHub Capstone Portal Frontend Script
 * Production Features: Real-time filtering, loading/failure states, toast alerts, client validation, application tracking.
 */

const API_BASE = window.location.origin.includes(":80") ? window.location.origin : "http://127.0.0.1:8000";

// App State
let allInternships = [];
let savedIds = JSON.parse(localStorage.getItem("internhub_capstone_saved") || "[]");
let activeCategory = "";

// Element Selectors
const $ = (id) => document.getElementById(id);
const loadingState = $("loadingState");
const failureState = $("failureState");
const emptyState = $("emptyState");
const internshipGrid = $("internshipGrid");
const failureMessage = $("failureMessage");
const resultCount = $("resultCount");
const apiStatusBadge = $("apiStatusBadge");
const retryBtn = $("retryBtn");
const refreshBtn = $("refreshBtn");

// Modals
const applyModal = $("applyModal");
const applyForm = $("applyForm");
const applyAlert = $("applyAlert");
const submitApplyBtn = $("submitApplyBtn");
const cancelApplyBtn = $("cancelApplyBtn");
const closeApplyModal = $("closeApplyModal");
const detailModal = $("detailModal");
const detailContent = $("detailContent");
const closeDetailModal = $("closeDetailModal");
const myAppsModal = $("myAppsModal");
const closeMyAppsModal = $("closeMyAppsModal");
const filtersDrawer = $("filters");

// Utilities
const formatCurrency = (val) => (val ? "₹" + Number(val).toLocaleString("en-IN") + "/mo" : "Unpaid / Experience");
const formatDate = (isoStr) => {
  if (!isoStr) return "Rolling admission";
  try {
    return new Date(isoStr).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  } catch (e) {
    return isoStr;
  }
};

function showToast(message) {
  const container = $("toastContainer");
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 3200);
}

// -------------------------------------------------------------
// 1. Data Fetching & State Management
// -------------------------------------------------------------
async function fetchInternships() {
  loadingState.hidden = false;
  failureState.hidden = true;
  emptyState.hidden = true;
  internshipGrid.hidden = true;
  resultCount.textContent = "Querying live database...";

  apiStatusBadge.className = "api-badge connecting";
  apiStatusBadge.querySelector(".status-text").textContent = "Connecting API...";

  try {
    const res = await fetch(`${API_BASE}/internships?limit=100`, {
      headers: { "Accept": "application/json" }
    });

    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }

    const json = await res.json();
    allInternships = json.data || [];

    apiStatusBadge.className = "api-badge connected";
    apiStatusBadge.querySelector(".status-text").textContent = "API Live";

    loadingState.hidden = true;
    renderListings();
  } catch (err) {
    console.error("API error:", err);
    loadingState.hidden = true;
    internshipGrid.hidden = true;
    emptyState.hidden = true;

    failureState.hidden = false;
    failureMessage.textContent = `Unable to connect to the backend server (${err.message}). Verify the API server is running on ${API_BASE}.`;

    apiStatusBadge.className = "api-badge error";
    apiStatusBadge.querySelector(".status-text").textContent = "Offline";
    resultCount.textContent = "0 positions loaded";
  }
}

// -------------------------------------------------------------
// 2. Multi-Facet Filtering & Sorting
// -------------------------------------------------------------
function getFilteredResults() {
  const query = ($("search").value || "").trim().toLowerCase();
  const mode = $("workModeFilter").value;
  const status = $("statusFilter").value;
  const minStipend = Number($("stipendFilter").value) || 0;
  const sort = $("sortFilter").value;
  const savedOnly = $("savedOnly").checked;

  let list = allInternships.filter((item) => {
    // Search keyword
    if (query) {
      const skillsStr = Array.isArray(item.skills) ? item.skills.join(" ") : "";
      const text = [item.title, item.company, item.location, item.category, skillsStr, item.description].join(" ").toLowerCase();
      if (!text.includes(query)) return false;
    }
    // Category pill
    if (activeCategory && item.category !== activeCategory) return false;
    // Work Mode
    if (mode && item.work_mode !== mode) return false;
    // Status
    if (status && item.status !== status) return false;
    // Minimum Stipend
    if (minStipend > 0 && (item.stipend || 0) < minStipend) return false;
    // Saved
    if (savedOnly && !savedIds.includes(item.id)) return false;

    return true;
  });

  if (sort === "stipend-high") {
    list.sort((a, b) => (b.stipend || 0) - (a.stipend || 0));
  } else if (sort === "deadline-soon") {
    list.sort((a, b) => {
      if (!a.deadline) return 1;
      if (!b.deadline) return -1;
      return new Date(a.deadline) - new Date(b.deadline);
    });
  } else {
    list.sort((a, b) => a.id - b.id);
  }

  return list;
}

function renderListings() {
  const items = getFilteredResults();
  resultCount.textContent = `${items.length} position${items.length === 1 ? "" : "s"} found`;
  $("savedCount").textContent = savedIds.length;

  if (items.length === 0) {
    emptyState.hidden = false;
    internshipGrid.hidden = true;
    return;
  }

  emptyState.hidden = true;
  internshipGrid.hidden = false;
  internshipGrid.innerHTML = "";

  items.forEach((item) => {
    const isSaved = savedIds.includes(item.id);
    const isOpen = item.status === "open";
    const skills = Array.isArray(item.skills) ? item.skills : [];

    const card = document.createElement("article");
    card.className = "card";
    card.innerHTML = `
      <div class="card-top">
        <h3 class="card-title" data-action="detail" data-id="${item.id}">${item.title}</h3>
        <div class="card-actions-top">
          <button class="btn btn-ghost btn-sm" data-action="share" data-id="${item.id}" title="Share position">🔗</button>
          <button class="btn btn-ghost btn-sm save-btn ${isSaved ? 'saved' : ''}" data-action="save" data-id="${item.id}" title="${isSaved ? 'Unsave' : 'Save'}">
            ${isSaved ? '♥' : '♡'}
          </button>
        </div>
      </div>
      <div class="card-company">${item.company} · ${item.location} (${item.duration || 3} mos)</div>
      <div class="card-badges">
        <span class="badge badge-category">${item.category}</span>
        <span class="badge badge-mode">${item.work_mode}</span>
        <span class="badge badge-status-${item.status}">${item.status.toUpperCase()}</span>
      </div>
      <div class="skills-tags">
        ${skills.map((s) => `<span class="skill-tag">${s}</span>`).join("")}
      </div>
      <p class="card-desc">${item.description || "No description provided."}</p>
      <div class="card-meta">
        <span class="stipend-val">${formatCurrency(item.stipend)}</span>
        <span>Deadline: ${formatDate(item.deadline)}</span>
      </div>
      <div class="card-footer">
        <button class="btn btn-outline full" data-action="detail" data-id="${item.id}">View Details</button>
        <button class="btn btn-primary full apply-btn" data-action="apply" data-id="${item.id}" ${!isOpen ? 'disabled' : ''}>
          ${isOpen ? 'Apply Now' : 'Closed'}
        </button>
      </div>
    `;
    internshipGrid.appendChild(card);
  });
}

// -------------------------------------------------------------
// 3. Application Form Submission & Client Validation
// -------------------------------------------------------------
function openApplyModal(id) {
  const item = allInternships.find((i) => i.id === Number(id));
  if (!item) return;

  $("applyInternshipId").value = item.id;
  $("applyModalTitle").textContent = `Apply for ${item.title}`;
  $("applyModalSubtitle").textContent = `${item.company} · ${item.location} (${item.work_mode})`;

  applyForm.reset();
  $("charCount").textContent = "0";
  clearErrors();
  hideAlert();

  applyModal.hidden = false;
  $("fullName").focus();
}

function closeApplyModalView() {
  applyModal.hidden = true;
  applyForm.reset();
  clearErrors();
  hideAlert();
}

function showAlert(type, msg) {
  applyAlert.className = `alert-box ${type}`;
  applyAlert.textContent = msg;
  applyAlert.hidden = false;
}

function hideAlert() {
  applyAlert.hidden = true;
}

function setFieldError(field, msg) {
  const input = $(field);
  const err = $(`err-${field}`);
  if (input) input.classList.add("invalid");
  if (err) err.textContent = msg;
}

function clearFieldError(field) {
  const input = $(field);
  const err = $(`err-${field}`);
  if (input) input.classList.remove("invalid");
  if (err) err.textContent = "";
}

function clearErrors() {
  ["fullName", "email", "phone", "resumeUrl", "coverLetter"].forEach(clearFieldError);
}

function validateForm() {
  clearErrors();
  let valid = true;

  const name = $("fullName").value.trim();
  const email = $("email").value.trim();
  const phone = $("phone").value.trim();
  const resume = $("resumeUrl").value.trim();

  if (!name || name.length < 2) {
    setFieldError("fullName", "Full legal name must be at least 2 characters.");
    valid = false;
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!email || !emailRegex.test(email)) {
    setFieldError("email", "Provide a valid email address (e.g. name@domain.com).");
    valid = false;
  }

  const phoneRegex = /^\+?[0-9\s\-()]{7,25}$/;
  if (!phone || !phoneRegex.test(phone)) {
    setFieldError("phone", "Provide a valid contact phone number (at least 7 digits).");
    valid = false;
  }

  if (!resume || !/^https?:\/\/.+/i.test(resume)) {
    setFieldError("resumeUrl", "Resume URL must begin with http:// or https://");
    valid = false;
  }

  return valid;
}

applyForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideAlert();

  if (!validateForm()) return;

  const internshipId = $("applyInternshipId").value;
  const payload = {
    full_name: $("fullName").value.trim(),
    email: $("email").value.trim().toLowerCase(),
    phone: $("phone").value.trim(),
    resume_url: $("resumeUrl").value.trim(),
    cover_letter: $("coverLetter").value.trim()
  };

  const btnText = submitApplyBtn.querySelector(".btn-text");
  const spinner = submitApplyBtn.querySelector(".spinner");
  submitApplyBtn.disabled = true;
  btnText.textContent = "Verifying & Submitting...";
  spinner.hidden = false;

  try {
    const res = await fetch(`${API_BASE}/internships/${internshipId}/apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (res.status === 201) {
      showAlert("success", `🎉 ${data.data.message}`);
      showToast("Application submitted successfully!");
      applyForm.reset();
      $("charCount").textContent = "0";

      // Save email for quick lookup
      localStorage.setItem("internhub_last_email", payload.email);

      setTimeout(() => {
        closeApplyModalView();
      }, 2400);
    } else {
      const err = data.error || {};
      if (err.code === "DUPLICATE_APPLICATION") {
        showAlert("error", "⚠️ Duplicate application: You have already applied for this opening.");
        setFieldError("email", "Application already on file.");
      } else if (err.code === "RATE_LIMITED") {
        showAlert("error", `⏳ ${err.message}`);
      } else if (err.code === "VALIDATION_ERROR" && Array.isArray(err.details)) {
        showAlert("error", "Server validation caught invalid inputs.");
        err.details.forEach((d) => setFieldError(d.field, d.message));
      } else {
        showAlert("error", err.message || "Failed to submit application.");
      }
    }
  } catch (err) {
    showAlert("error", "Network error: Unable to contact server. Please retry.");
  } finally {
    submitApplyBtn.disabled = false;
    btnText.textContent = "Submit Application";
    spinner.hidden = true;
  }
});

$("coverLetter").addEventListener("input", (e) => {
  $("charCount").textContent = e.target.value.length;
});

["fullName", "email", "phone", "resumeUrl"].forEach((id) => {
  $(id).addEventListener("input", () => clearFieldError(id));
});

// -------------------------------------------------------------
// 4. Role Detail View
// -------------------------------------------------------------
function openDetailView(id) {
  const item = allInternships.find((i) => i.id === Number(id));
  if (!item) return;

  const isSaved = savedIds.includes(item.id);
  const isOpen = item.status === "open";
  const skills = Array.isArray(item.skills) ? item.skills : [];

  detailContent.innerHTML = `
    <div class="modal-header">
      <span class="modal-badge">${item.category} · ${item.work_mode.toUpperCase()}</span>
      <h2>${item.title}</h2>
      <p class="modal-subtitle">${item.company} · ${item.location}</p>
    </div>
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:12px; margin: 18px 0; padding:16px; background:#f8f9fa; border-radius:8px;">
      <div><strong>Stipend:</strong> <div>${formatCurrency(item.stipend)}</div></div>
      <div><strong>Duration:</strong> <div>${item.duration || 3} Months</div></div>
      <div><strong>Deadline:</strong> <div>${formatDate(item.deadline)}</div></div>
      <div><strong>Status:</strong> <div><span class="badge badge-status-${item.status}">${item.status.toUpperCase()}</span></div></div>
    </div>
    <h4 style="margin-bottom:8px;">Required Skills & Technologies</h4>
    <div class="skills-tags" style="margin-bottom:18px;">
      ${skills.map((s) => `<span class="skill-tag" style="font-size:0.85rem; padding:4px 9px;">${s}</span>`).join("")}
    </div>
    <h4 style="margin-bottom:8px;">About the Opportunity</h4>
    <p style="color:#495057; line-height:1.6; margin-bottom:24px;">${item.description || 'No detailed description provided.'}</p>
    <div style="display:flex; gap:10px; justify-content:flex-end;">
      <button class="btn btn-outline" id="detailSaveBtn">
        ${isSaved ? '♥ Saved' : '♡ Save Internship'}
      </button>
      <button class="btn btn-primary" id="detailApplyBtn" ${!isOpen ? 'disabled' : ''}>
        ${isOpen ? 'Apply for this Position' : 'Applications Closed'}
      </button>
    </div>
  `;

  $("detailSaveBtn").addEventListener("click", () => {
    toggleSave(item.id);
    openDetailView(item.id);
  });

  if (isOpen) {
    $("detailApplyBtn").addEventListener("click", () => {
      detailModal.hidden = true;
      openApplyModal(item.id);
    });
  }

  detailModal.hidden = false;
}

// -------------------------------------------------------------
// 5. My Applications Tracker
// -------------------------------------------------------------
$("myAppsBtn").addEventListener("click", () => {
  const lastEmail = localStorage.getItem("internhub_last_email") || "";
  if (lastEmail) $("lookupEmail").value = lastEmail;
  myAppsModal.hidden = false;
  if (lastEmail) fetchMyApplications(lastEmail);
});

$("lookupBtn").addEventListener("click", () => {
  const email = $("lookupEmail").value.trim();
  if (!email) return;
  fetchMyApplications(email);
});

async function fetchMyApplications(email) {
  const listEl = $("myAppsResults");
  listEl.innerHTML = `<p class="text-muted text-center" style="margin:20px 0;">Searching records...</p>`;

  try {
    const res = await fetch(`${API_BASE}/applications/my?email=${encodeURIComponent(email)}`);
    const data = await res.json();
    const apps = data.data || [];

    if (apps.length === 0) {
      listEl.innerHTML = `<p class="text-muted text-center" style="margin:20px 0;">No submitted applications found for <strong>${email}</strong>.</p>`;
      return;
    }

    listEl.innerHTML = apps.map((a) => `
      <div class="app-item-card">
        <div class="app-item-header">
          <span>${a.title}</span>
          <span class="badge badge-status-open">SUBMITTED</span>
        </div>
        <div style="font-size:0.85rem; color:#6c757d; margin-bottom:6px;">${a.company} · ${a.location}</div>
        <div style="font-size:0.8rem; color:#868e96;">Applied on: ${formatDate(a.created_at)} · Reference #${a.id}</div>
      </div>
    `).join("");
  } catch (err) {
    listEl.innerHTML = `<p style="color:var(--danger); text-align:center; margin:20px 0;">Failed to load applications.</p>`;
  }
}

// -------------------------------------------------------------
// 6. Bookmarking & Share
// -------------------------------------------------------------
function toggleSave(id) {
  const numId = Number(id);
  if (savedIds.includes(numId)) {
    savedIds = savedIds.filter((x) => x !== numId);
    showToast("Removed from saved list");
  } else {
    savedIds.push(numId);
    showToast("Saved to your bookmarks! ♥");
  }
  localStorage.setItem("internhub_capstone_saved", JSON.stringify(savedIds));
  renderListings();
}

function shareInternship(id) {
  const item = allInternships.find((i) => i.id === Number(id));
  if (!item) return;
  const shareText = `Check out this opening: ${item.title} at ${item.company} (${item.work_mode}) on InternHub!`;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(shareText);
    showToast("Position details copied to clipboard! 📋");
  } else {
    showToast(shareText);
  }
}

// -------------------------------------------------------------
// 7. Event Wiring
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  $("year").textContent = new Date().getFullYear();

  // Retry & Sync
  retryBtn.addEventListener("click", fetchInternships);
  refreshBtn.addEventListener("click", fetchInternships);

  // Filters & Search
  $("search").addEventListener("input", renderListings);
  $("workModeFilter").addEventListener("change", renderListings);
  $("statusFilter").addEventListener("change", renderListings);
  $("sortFilter").addEventListener("change", renderListings);
  $("savedOnly").addEventListener("change", renderListings);

  // Stipend Slider
  $("stipendFilter").addEventListener("input", (e) => {
    $("stipendLabel").textContent = `₹${Number(e.target.value).toLocaleString("en-IN")}/mo`;
    renderListings();
  });

  // Category Pills
  $("categoryPills").addEventListener("click", (e) => {
    const pill = e.target.closest(".pill");
    if (!pill) return;
    document.querySelectorAll(".category-pills .pill").forEach((p) => p.classList.remove("active"));
    pill.classList.add("active");
    activeCategory = pill.getAttribute("data-category");
    renderListings();
  });

  $("resetFilters").addEventListener("click", () => {
    $("search").value = "";
    $("workModeFilter").value = "";
    $("statusFilter").value = "";
    $("stipendFilter").value = 0;
    $("stipendLabel").textContent = "₹0/mo";
    $("sortFilter").value = "default";
    $("savedOnly").checked = false;
    document.querySelectorAll(".category-pills .pill").forEach((p) => p.classList.remove("active"));
    document.querySelector('.category-pills .pill[data-category=""]').classList.add("active");
    activeCategory = "";
    renderListings();
  });

  $("clearFiltersBtn").addEventListener("click", () => $("resetFilters").click());

  // Mobile Drawer Toggle
  $("filterToggle").addEventListener("click", () => {
    filtersDrawer.classList.toggle("open");
  });
  $("closeFiltersBtn").addEventListener("click", () => {
    filtersDrawer.classList.remove("open");
  });

  // Modal Closers
  cancelApplyBtn.addEventListener("click", closeApplyModalView);
  closeApplyModal.addEventListener("click", closeApplyModalView);
  closeDetailModal.addEventListener("click", () => { detailModal.hidden = true; });
  closeMyAppsModal.addEventListener("click", () => { myAppsModal.hidden = true; });

  window.addEventListener("click", (e) => {
    if (e.target === applyModal) closeApplyModalView();
    if (e.target === detailModal) detailModal.hidden = true;
    if (e.target === myAppsModal) myAppsModal.hidden = true;
  });

  // Grid Action Delegator
  internshipGrid.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const action = btn.getAttribute("data-action");
    const id = btn.getAttribute("data-id");

    if (action === "apply") openApplyModal(id);
    else if (action === "detail") openDetailView(id);
    else if (action === "save") toggleSave(id);
    else if (action === "share") shareInternship(id);
  });

  // Initial Fetch
  fetchInternships();
});
