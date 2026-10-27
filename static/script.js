/**
 * InternshipChesko 🎯 Full Application Script
 * Features:
 * - Dynamic fetch with loading & retry states
 * - Real-time multi-facet filtering (search, category pills, mode, stipend, status, saved)
 * - Candidate Application submission with dual client & server validation
 * - Recruiter "Post an Internship" publishing directly into SQLite via REST API
 * - Recruiter "View Candidates" for any internship listing
 * - "My Applications" tracking by email
 * - Bookmark saving with localStorage persistence
 * - One-click Share to clipboard with toast notification
 */

const API_BASE = window.location.origin.includes(":80") ? window.location.origin : "http://127.0.0.1:8000";

// App State
let allInternships = [];
let savedIds = JSON.parse(localStorage.getItem("internship_chesko_saved") || "[]");
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

const postModal = $("postModal");
const postForm = $("postForm");
const postAlert = $("postAlert");
const submitPostBtn = $("submitPostBtn");
const cancelPostBtn = $("cancelPostBtn");
const closePostModal = $("closePostModal");
const postInternshipBtn = $("postInternshipBtn");

const applicantsModal = $("applicantsModal");
const closeApplicantsModal = $("closeApplicantsModal");
const applicantsList = $("applicantsList");

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
  resultCount.textContent = "Connecting to InternshipChesko API...";

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
    apiStatusBadge.querySelector(".status-text").textContent = "API Live 🟢";

    loadingState.hidden = true;
    renderListings();
  } catch (err) {
    console.error("API error:", err);
    loadingState.hidden = true;
    internshipGrid.hidden = true;
    emptyState.hidden = true;

    failureState.hidden = false;
    failureMessage.textContent = `Unable to connect to the backend server (${err.message}). Verify the API is running on ${API_BASE}.`;

    apiStatusBadge.className = "api-badge error";
    apiStatusBadge.querySelector(".status-text").textContent = "Offline 🔴";
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
  hideAlert(applyAlert);

  applyModal.hidden = false;
  $("fullName").focus();
}

function closeApplyModalView() {
  applyModal.hidden = true;
  applyForm.reset();
  clearErrors();
  hideAlert(applyAlert);
}

function showAlert(alertEl, type, msg) {
  alertEl.className = `alert-box ${type}`;
  alertEl.textContent = msg;
  alertEl.hidden = false;
}

function hideAlert(alertEl) {
  alertEl.hidden = true;
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
  hideAlert(applyAlert);

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
      showAlert(applyAlert, "success", `🎉 ${data.data.message}`);
      showToast("Application submitted successfully! 🚀");
      applyForm.reset();
      $("charCount").textContent = "0";

      // Save email for quick candidate lookup
      localStorage.setItem("internhub_last_email", payload.email);

      setTimeout(() => {
        closeApplyModalView();
      }, 2400);
    } else {
      const err = data.error || {};
      if (err.code === "DUPLICATE_APPLICATION") {
        showAlert(applyAlert, "error", "⚠️ Duplicate application: You have already applied for this opening.");
        setFieldError("email", "Application already on file.");
      } else if (err.code === "RATE_LIMITED") {
        showAlert(applyAlert, "error", `⏳ ${err.message}`);
      } else if (err.code === "VALIDATION_ERROR" && Array.isArray(err.details)) {
        showAlert(applyAlert, "error", "Server validation caught invalid inputs.");
        err.details.forEach((d) => setFieldError(d.field, d.message));
      } else {
        showAlert(applyAlert, "error", err.message || "Failed to submit application.");
      }
    }
  } catch (err) {
    showAlert(applyAlert, "error", "Network error: Unable to contact server. Please retry.");
  } finally {
    submitApplyBtn.disabled = false;
    btnText.textContent = "Submit Application 🚀";
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
// 4. Role Detail View & Candidate List for Employers
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
    <div style="display:flex; flex-wrap:wrap; gap:10px; justify-content:flex-end;">
      <button class="btn btn-outline" id="viewCandidatesBtn">
        👥 View Applicants
      </button>
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

  $("viewCandidatesBtn").addEventListener("click", () => {
    detailModal.hidden = true;
    openApplicantsModal(item.id, item.title, item.company);
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
// 5. Recruiter: View Applicants for an Internship
// -------------------------------------------------------------
async function openApplicantsModal(internshipId, title, company) {
  $("applicantsModalTitle").textContent = `Candidates for: ${title}`;
  $("applicantsModalSubtitle").textContent = `${company} · Position #${internshipId}`;
  applicantsList.innerHTML = `<p class="text-muted text-center" style="margin:20px 0;">Loading applicants from database...</p>`;
  applicantsModal.hidden = false;

  try {
    const res = await fetch(`${API_BASE}/internships/${internshipId}/applications`);
    const data = await res.json();
    const apps = data.data || [];

    if (apps.length === 0) {
      applicantsList.innerHTML = `<p class="text-muted text-center" style="margin:20px 0;">No candidates have applied for this position yet.</p>`;
      return;
    }

    applicantsList.innerHTML = apps.map((a) => `
      <div class="app-item-card">
        <div class="app-item-header">
          <span>${a.full_name}</span>
          <span style="font-size:0.8rem; color:#868e96;">Applied ${formatDate(a.created_at)}</span>
        </div>
        <div style="font-size:0.88rem; color:#495057; margin-bottom:6px;">
          📧 ${a.email} · 📱 ${a.phone}
        </div>
        ${a.cover_letter ? `<div style="font-size:0.84rem; color:#6c757d; font-style:italic; margin-bottom:8px;">"${a.cover_letter}"</div>` : ''}
        <div>
          <a href="${a.resume_url}" target="_blank" rel="noopener" class="btn btn-outline btn-sm" style="display:inline-flex;">
            📄 View Resume
          </a>
        </div>
      </div>
    `).join("");
  } catch (err) {
    applicantsList.innerHTML = `<p style="color:var(--danger); text-align:center; margin:20px 0;">Failed to load candidate applications.</p>`;
  }
}

// -------------------------------------------------------------
// 6. Recruiter: Post New Internship
// -------------------------------------------------------------
postInternshipBtn.addEventListener("click", () => {
  postForm.reset();
  const d = new Date();
  d.setDate(d.getDate() + 30);
  $("postDeadline").value = d.toISOString().split("T")[0];
  hideAlert(postAlert);
  postModal.hidden = false;
  $("postTitle").focus();
});

cancelPostBtn.addEventListener("click", () => { postModal.hidden = true; });
closePostModal.addEventListener("click", () => { postModal.hidden = true; });

postForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideAlert(postAlert);

  const title = $("postTitle").value.trim();
  const company = $("postCompany").value.trim();
  const category = $("postCategory").value;
  const location = $("postLocation").value.trim();
  const workMode = $("postWorkMode").value;
  const duration = Number($("postDuration").value) || 3;
  const stipend = Number($("postStipend").value) || 0;
  const rawSkills = $("postSkills").value.trim();
  const deadline = $("postDeadline").value;
  const status = $("postStatus").value;
  const description = $("postDesc").value.trim();

  if (!title || !company || !location || !rawSkills || !deadline || !description) {
    showAlert(postAlert, "error", "Please fill out all required fields.");
    return;
  }

  const skills = rawSkills.split(",").map((s) => s.trim()).filter(Boolean);

  const payload = {
    title,
    company,
    category,
    location,
    work_mode: workMode,
    duration,
    stipend,
    skills,
    deadline,
    status,
    description
  };

  const btnText = submitPostBtn.querySelector(".btn-text");
  const spinner = submitPostBtn.querySelector(".spinner");
  submitPostBtn.disabled = true;
  btnText.textContent = "Publishing...";
  spinner.hidden = false;

  try {
    const res = await fetch(`${API_BASE}/internships`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (res.status === 201) {
      showAlert(postAlert, "success", "✨ Internship successfully posted to InternshipChesko!");
      showToast("🚀 New internship posted live!");
      postForm.reset();

      // Refresh listings
      await fetchInternships();

      setTimeout(() => {
        postModal.hidden = true;
      }, 1800);
    } else {
      showAlert(postAlert, "error", data.error?.message || "Failed to publish internship.");
    }
  } catch (err) {
    showAlert(postAlert, "error", "Network error while publishing internship.");
  } finally {
    submitPostBtn.disabled = false;
    btnText.textContent = "Publish Internship ✨";
    spinner.hidden = true;
  }
});

// -------------------------------------------------------------
// 7. My Applications Tracker
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
        <div style="font-size:0.85rem; color:#6c757d; margin-bottom:6px;">${a.company} · ${a.location} (${a.work_mode})</div>
        <div style="font-size:0.8rem; color:#868e96;">Applied on: ${formatDate(a.created_at)} · Reference #${a.id}</div>
      </div>
    `).join("");
  } catch (err) {
    listEl.innerHTML = `<p style="color:var(--danger); text-align:center; margin:20px 0;">Failed to load applications.</p>`;
  }
}

// -------------------------------------------------------------
// 8. Bookmarking & Share
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
  localStorage.setItem("internship_chesko_saved", JSON.stringify(savedIds));
  renderListings();
}

function shareInternship(id) {
  const item = allInternships.find((i) => i.id === Number(id));
  if (!item) return;
  const shareText = `Check out this opening on InternshipChesko 🎯: ${item.title} at ${item.company} (${item.work_mode}, ${item.location})!`;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(shareText);
    showToast("Position details copied to clipboard! 📋");
  } else {
    showToast(shareText);
  }
}

// -------------------------------------------------------------
// 9. Event Wiring
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
  closeApplicantsModal.addEventListener("click", () => { applicantsModal.hidden = true; });

  window.addEventListener("click", (e) => {
    if (e.target === applyModal) closeApplyModalView();
    if (e.target === detailModal) detailModal.hidden = true;
    if (e.target === myAppsModal) myAppsModal.hidden = true;
    if (e.target === postModal) postModal.hidden = true;
    if (e.target === applicantsModal) applicantsModal.hidden = true;
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
