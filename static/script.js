/**
 * InternshipChesko 🎯 Full Platform Client Script
 * Complete integration:
 * - 2 Dedicated Panels: Intern Portal & Admin Dashboard
 * - Real-time Panel Switching
 * - Intern Registration & Profile Persistence
 * - 5 Milestone Task Submissions, Admin Reviews, and Approvals
 * - Verified Certificate Generation, Verification & Print/PDF Engine
 * - Public Job Board, Filters, and Job Applications
 */

const API_BASE = window.location.origin.includes(":80") ? window.location.origin : "http://127.0.0.1:8000";

// App State
let allInternships = [];
let savedIds = JSON.parse(localStorage.getItem("internship_chesko_saved") || "[]");
let activeCategory = "";
let currentInternUser = JSON.parse(localStorage.getItem("internship_chesko_user") || "null");
let currentViewingCertificate = null;

// DOM Utilities
const $ = (id) => document.getElementById(id);

function showToast(message) {
  const container = $("toastContainer");
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => { toast.remove(); }, 3200);
}

// -------------------------------------------------------------
// 1. Navigation Panel Switcher
// -------------------------------------------------------------
function switchView(targetViewId) {
  document.querySelectorAll(".portal-view").forEach((v) => v.classList.remove("active"));
  document.querySelectorAll(".nav-tab").forEach((t) => t.classList.remove("active"));

  const targetView = $(targetViewId);
  if (targetView) targetView.classList.add("active");

  const activeTab = document.querySelector(`.nav-tab[data-view="${targetViewId}"]`);
  if (activeTab) activeTab.classList.add("active");

  window.scrollTo({ top: 0, behavior: "smooth" });

  if (targetViewId === "view-admin") {
    loadAdminDashboard();
  } else if (targetViewId === "view-intern") {
    refreshInternPortal();
  } else if (targetViewId === "view-browse") {
    if (allInternships.length === 0) fetchInternships();
  }
}

document.querySelectorAll(".nav-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    const viewId = tab.getAttribute("data-view");
    switchView(viewId);
  });
});

// -------------------------------------------------------------
// 2. Intern Portal: Registration, Tasks & Progress
// -------------------------------------------------------------
function refreshInternPortal() {
  const authSec = $("internAuthSection");
  const dashSec = $("internDashboardSection");
  const navBadge = $("internNavBadge");

  if (!currentInternUser) {
    authSec.hidden = false;
    dashSec.hidden = true;
    navBadge.hidden = true;
  } else {
    authSec.hidden = true;
    dashSec.hidden = false;
    navBadge.hidden = false;
    navBadge.textContent = currentInternUser.name.split(" ")[0];

    // Populate Profile Header
    $("profileName").textContent = currentInternUser.name;
    $("profileDomain").textContent = currentInternUser.domain || "Full Stack Web Development";
    $("profileCollege").textContent = currentInternUser.college || "Engineering College";
    $("profileEmail").textContent = currentInternUser.email;

    // Fetch Milestone Tasks for User
    loadInternTasks();
  }
}

$("internRegForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = $("internName").value.trim();
  const email = $("internEmail").value.trim().toLowerCase();
  const phone = $("internPhone").value.trim();
  const college = $("internCollege").value.trim();
  const domain = $("internDomain").value;

  if (!name || !email || !college) {
    showToast("Please fill in all required registration fields.");
    return;
  }

  const payload = { name, email, phone, college, domain, role: "intern" };
  const regBtn = $("internRegBtn");
  regBtn.disabled = true;
  regBtn.textContent = "Registering...";

  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const json = await res.json();

    if (res.ok) {
      currentInternUser = json.data;
      localStorage.setItem("internship_chesko_user", JSON.stringify(currentInternUser));
      showToast(`Welcome, ${currentInternUser.name}! 🎯`);
      refreshInternPortal();
    } else {
      showToast(json.error?.message || "Registration failed.");
    }
  } catch (err) {
    showToast("Network error during registration.");
  } finally {
    regBtn.disabled = false;
    regBtn.textContent = "Enter My Intern Dashboard 🚀";
  }
});

$("switchUserBtn").addEventListener("click", () => {
  if (confirm("Do you want to switch or log out of this intern account?")) {
    currentInternUser = null;
    localStorage.removeItem("internship_chesko_user");
    refreshInternPortal();
    showToast("Logged out of intern account");
  }
});

async function loadInternTasks() {
  if (!currentInternUser) return;
  const listEl = $("tasksList");
  listEl.innerHTML = `<p class="text-muted text-center" style="margin:20px 0;">Loading assigned milestone tasks...</p>`;

  try {
    const res = await fetch(`${API_BASE}/users/${currentInternUser.id}/tasks`);
    const json = await res.json();
    const data = json.data || {};
    const tasks = data.tasks || [];

    // Update Progress Bar
    const pct = data.progress_percent || 0;
    $("progressPercentText").textContent = `${pct}%`;
    $("tasksScoreText").textContent = `${data.approved_count}/${data.total_tasks} Approved`;
    $("progressBarFill").style.width = `${pct}%`;

    // Check Certificate Status
    const certBox = $("certUnlockedBox");
    if (data.certificate_unlocked && data.certificate) {
      certBox.hidden = false;
      currentViewingCertificate = data.certificate;
    } else {
      certBox.hidden = true;
    }

    // Render Milestone Tasks
    listEl.innerHTML = tasks.map((t) => {
      const status = t.submission_status;
      let badgeClass = "badge-status-closed";
      let statusLabel = "Not Submitted";
      let btnLabel = "Submit Task Solution 🚀";

      if (status === "approved") {
        badgeClass = "badge-status-open";
        statusLabel = "✅ Approved";
        btnLabel = "Update Submission";
      } else if (status === "pending") {
        badgeClass = "badge-mode";
        statusLabel = "⏳ Under Review";
        btnLabel = "Edit Submission";
      } else if (status === "rejected") {
        badgeClass = "badge-danger";
        statusLabel = "❌ Changes Requested";
        btnLabel = "Re-submit Solution 🚀";
      }

      return `
        <article class="task-item-card ${status}">
          <div class="task-card-header">
            <div>
              <span class="modal-badge">Milestone ${t.task_num} of 5</span>
              <h4 class="task-card-title">${t.title}</h4>
            </div>
            <span class="badge ${badgeClass}">${statusLabel}</span>
          </div>

          <p class="task-obj"><strong>Objective:</strong> ${t.objective}</p>
          <p class="task-deliverable"><strong>Deliverable:</strong> ${t.deliverable}</p>

          ${t.submission_url ? `
            <div class="task-submission-info">
              <div><strong>Submitted URL:</strong> <a href="${t.submission_url}" target="_blank" rel="noopener">${t.submission_url}</a></div>
              ${t.submission_notes ? `<div style="margin-top:4px;"><strong>Notes:</strong> ${t.submission_notes}</div>` : ""}
            </div>
          ` : ""}

          ${t.submission_feedback ? `
            <div class="task-feedback-box">
              <strong>Admin Feedback:</strong> ${t.submission_feedback}
            </div>
          ` : ""}

          <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:12px;">
            <button class="btn btn-outline btn-sm" data-action="submit-task" data-task-id="${t.id}" data-task-title="${t.title}" data-url="${t.submission_url || ""}" data-notes="${t.submission_notes || ""}">
              ${btnLabel}
            </button>
          </div>
        </article>
      `;
    }).join("");
  } catch (err) {
    listEl.innerHTML = `<p style="color:var(--danger); text-align:center;">Failed to load tasks.</p>`;
  }
}

// Task Submission Modal Handling
$("tasksList").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-action='submit-task']");
  if (!btn) return;
  const taskId = btn.getAttribute("data-task-id");
  const taskTitle = btn.getAttribute("data-task-title");
  const url = btn.getAttribute("data-url");
  const notes = btn.getAttribute("data-notes");

  $("submitTaskId").value = taskId;
  $("submitTaskModalSubtitle").textContent = taskTitle;
  $("taskSubmissionUrl").value = url;
  $("taskNotes").value = notes;
  $("err-taskSubmissionUrl").textContent = "";
  $("taskSubmitAlert").hidden = true;

  $("submitTaskModal").hidden = false;
  $("taskSubmissionUrl").focus();
});

$("closeSubmitTaskModal").addEventListener("click", () => { $("submitTaskModal").hidden = true; });
$("cancelSubmitTaskBtn").addEventListener("click", () => { $("submitTaskModal").hidden = true; });

$("taskSubmitForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const taskId = $("submitTaskId").value;
  const submissionUrl = $("taskSubmissionUrl").value.trim();
  const notes = $("taskNotes").value.trim();

  if (!submissionUrl || !/^https?:\/\/.+/i.test(submissionUrl)) {
    $("err-taskSubmissionUrl").textContent = "Please provide a valid URL starting with http:// or https://";
    return;
  }

  const confirmBtn = $("confirmSubmitTaskBtn");
  const btnText = confirmBtn.querySelector(".btn-text");
  const spinner = confirmBtn.querySelector(".spinner");
  confirmBtn.disabled = true;
  btnText.textContent = "Submitting...";
  spinner.hidden = false;

  try {
    const res = await fetch(`${API_BASE}/users/${currentInternUser.id}/tasks/${taskId}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ submission_url: submissionUrl, notes }),
    });
    const json = await res.json();

    if (res.ok) {
      showToast("🚀 Task milestone submitted for Admin review!");
      $("submitTaskModal").hidden = true;
      loadInternTasks();
    } else {
      showToast(json.error?.message || "Failed to submit task.");
    }
  } catch (err) {
    showToast("Network error during task submission.");
  } finally {
    confirmBtn.disabled = false;
    btnText.textContent = "Submit for Admin Review 🚀";
    spinner.hidden = true;
  }
});

// View Certificate Button
$("viewMyCertBtn").addEventListener("click", () => {
  if (currentViewingCertificate) {
    renderCertificate(currentViewingCertificate);
  }
});

// -------------------------------------------------------------
// 3. Admin Dashboard & Review Hub (Panel 2)
// -------------------------------------------------------------
async function loadAdminDashboard() {
  loadAdminMetrics();
  loadAdminSubmissions();
  loadAdminInterns();
  loadAdminApplications();
}

async function loadAdminMetrics() {
  try {
    const res = await fetch(`${API_BASE}/admin/metrics`);
    const json = await res.json();
    const m = json.data || {};
    $("kpiInterns").textContent = m.total_interns || 0;
    $("kpiPending").textContent = m.pending_task_reviews || 0;
    $("adminPendingCount").textContent = m.pending_task_reviews || 0;
    $("kpiCertificates").textContent = m.certificates_issued || 0;
    $("kpiApplications").textContent = m.total_applications || 0;

    const navBadge = $("adminPendingBadge");
    if (m.pending_task_reviews > 0) {
      navBadge.hidden = false;
      navBadge.textContent = `${m.pending_task_reviews} Pending`;
    } else {
      navBadge.hidden = true;
    }
  } catch (err) {
    console.error("Failed to load admin metrics:", err);
  }
}

async function loadAdminSubmissions() {
  const tbody = $("adminSubmissionsTbody");
  tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">Loading submissions...</td></tr>`;

  try {
    const res = await fetch(`${API_BASE}/admin/submissions`);
    const json = await res.json();
    const items = json.data || [];

    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted" style="padding:24px;">No intern task submissions recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map((sub) => {
      let statusBadge = `<span class="badge badge-mode">⏳ Under Review</span>`;
      if (sub.status === "approved") statusBadge = `<span class="badge badge-status-open">✅ Approved</span>`;
      if (sub.status === "rejected") statusBadge = `<span class="badge badge-danger">❌ Rejected</span>`;

      return `
        <tr>
          <td>
            <strong>${sub.intern_name}</strong>
            <div style="font-size:0.8rem; color:#868e96;">${sub.college}</div>
          </td>
          <td>
            <strong>Task ${sub.task_num}:</strong> ${sub.task_title}
          </td>
          <td>
            <a href="${sub.submission_url}" target="_blank" rel="noopener" style="color:var(--primary); font-weight:600;">
              🔗 View Deliverable
            </a>
            ${sub.notes ? `<div style="font-size:0.8rem; color:#6c757d; margin-top:2px;">"${sub.notes}"</div>` : ""}
          </td>
          <td>${statusBadge}</td>
          <td style="font-size:0.82rem; color:#868e96;">${formatDate(sub.submitted_at)}</td>
          <td>
            <div style="display:flex; gap:6px;">
              <button class="btn btn-success btn-sm" data-action="review-sub" data-sub-id="${sub.id}" data-decision="approved" title="Approve Task">
                ✅ Approve
              </button>
              <button class="btn btn-outline btn-sm" data-action="review-sub" data-sub-id="${sub.id}" data-decision="rejected" title="Request Changes">
                ❌ Reject
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Failed to load submissions.</td></tr>`;
  }
}

// Admin Submissions Action Handler
$("adminSubmissionsTbody").addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-action='review-sub']");
  if (!btn) return;
  const subId = btn.getAttribute("data-sub-id");
  const decision = btn.getAttribute("data-decision");

  let feedback = "";
  if (decision === "rejected") {
    feedback = prompt("Enter feedback / reason for requesting changes:", "Please verify all task requirements and re-test.") || "";
  }

  btn.disabled = true;
  try {
    const res = await fetch(`${API_BASE}/admin/submissions/${subId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: decision, feedback }),
    });
    const json = await res.json();

    if (res.ok) {
      showToast(json.message);
      loadAdminDashboard();
      if (currentInternUser) loadInternTasks();
    } else {
      showToast(json.error?.message || "Failed to submit review.");
    }
  } catch (err) {
    showToast("Network error during review.");
  }
});

async function loadAdminInterns() {
  const tbody = $("adminInternsTbody");
  try {
    const res = await fetch(`${API_BASE}/admin/interns`);
    const json = await res.json();
    const interns = json.data || [];

    if (interns.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted" style="padding:24px;">No interns registered yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = interns.map((i) => `
      <tr>
        <td>
          <strong>${i.name}</strong>
          <div style="font-size:0.8rem; color:#868e96;">${i.email} · ${i.phone || "No phone"}</div>
        </td>
        <td>${i.college}</td>
        <td><span class="badge badge-category">${i.domain}</span></td>
        <td><strong>${i.approved_tasks} / 5</strong> Approved</td>
        <td>
          ${i.has_certificate ? `<span class="badge badge-status-open">🎓 Issued</span>` : `<span class="badge badge-status-closed">Pending</span>`}
        </td>
        <td>
          <div style="display:flex; gap:6px;">
            <button class="btn btn-outline btn-sm" data-action="view-intern-cert" data-user-id="${i.id}">
              ${i.has_certificate ? "View Certificate" : "Issue Certificate"}
            </button>
          </div>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Failed to load interns roster.</td></tr>`;
  }
}

// View Certificate from Admin Roster
$("adminInternsTbody").addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-action='view-intern-cert']");
  if (!btn) return;
  const userId = btn.getAttribute("data-user-id");

  try {
    let res = await fetch(`${API_BASE}/users/${userId}/certificate`);
    if (res.status === 404) {
      // Manual Issuance Option
      if (confirm("No certificate issued yet. Would you like to issue an official certificate now?")) {
        const issueRes = await fetch(`${API_BASE}/admin/certificates/issue`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: Number(userId), grade: "Outstanding (A+)" }),
        });
        const issueJson = await issueRes.json();
        if (issueRes.ok) {
          showToast("Certificate issued successfully! 🎓");
          renderCertificate(issueJson.data);
          loadAdminDashboard();
        }
      }
      return;
    }

    const json = await res.json();
    if (res.ok && json.data) {
      renderCertificate(json.data);
    }
  } catch (err) {
    showToast("Error retrieving certificate.");
  }
});

async function loadAdminApplications() {
  const tbody = $("adminApplicationsTbody");
  try {
    const res = await fetch(`${API_BASE}/internships?limit=100`);
    const json = await res.json();
    const internships = json.data || [];

    let allApps = [];
    for (const item of internships) {
      const appRes = await fetch(`${API_BASE}/internships/${item.id}/applications`);
      const appJson = await appRes.json();
      const apps = (appJson.data || []).map((a) => ({ ...a, role_title: item.title, role_company: item.company }));
      allApps.push(...apps);
    }

    if (allApps.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted" style="padding:24px;">No job applications submitted yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = allApps.map((a) => `
      <tr>
        <td>
          <strong>${a.full_name}</strong>
          <div style="font-size:0.8rem; color:#868e96;">Applying for: ${a.role_title} (${a.role_company})</div>
        </td>
        <td>
          <div>${a.email}</div>
          <div style="font-size:0.8rem; color:#868e96;">${a.phone}</div>
        </td>
        <td>
          <a href="${a.resume_url}" target="_blank" rel="noopener" style="color:var(--primary); font-weight:600;">
            📄 View Resume
          </a>
        </td>
        <td style="font-size:0.84rem; max-width:260px; color:#495057;">${a.cover_letter || "None"}</td>
        <td style="font-size:0.82rem; color:#868e96;">${formatDate(a.created_at)}</td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Failed to load applications.</td></tr>`;
  }
}

// Admin Subtabs Switching
document.querySelectorAll(".subtab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".subtab").forEach((s) => s.classList.remove("active"));
    document.querySelectorAll(".admin-tab-content").forEach((c) => c.classList.remove("active"));

    tab.classList.add("active");
    const targetId = tab.getAttribute("data-subtab");
    $(targetId).classList.add("active");
  });
});

$("refreshAdminBtn").addEventListener("click", () => {
  loadAdminDashboard();
  showToast("Dashboard synchronized! ↻");
});

// -------------------------------------------------------------
// 4. Authentic Verified Certificate Engine
// -------------------------------------------------------------
function renderCertificate(cert) {
  currentViewingCertificate = cert;

  $("certInternName").textContent = cert.intern_name.toUpperCase();
  $("certCollege").textContent = `from ${cert.college}`;
  $("certDomain").textContent = cert.domain;
  $("certStartDate").textContent = formatDate(cert.start_date || "2026-09-01");
  $("certEndDate").textContent = formatDate(cert.completion_date);
  $("certGrade").textContent = cert.grade || "Outstanding (A+)";
  $("certIdDisplay").textContent = cert.certificate_id;

  const verifyUrl = `${API_BASE}/certificates/${cert.certificate_id}`;
  $("certVerifyUrl").textContent = verifyUrl;

  $("certificateModal").hidden = false;
}

$("closeCertModal").addEventListener("click", () => { $("certificateModal").hidden = true; });

$("printCertBtn").addEventListener("click", () => {
  window.print();
});

$("copyCertLinkBtn").addEventListener("click", () => {
  if (currentViewingCertificate) {
    const url = `${API_BASE}/certificates/${currentViewingCertificate.certificate_id}`;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url);
      showToast("Verification link copied to clipboard! 📋");
    } else {
      showToast(url);
    }
  }
});

// -------------------------------------------------------------
// 5. Explore Internships (Public Board)
// -------------------------------------------------------------
async function fetchInternships() {
  $("loadingState").hidden = false;
  $("failureState").hidden = true;
  $("emptyState").hidden = true;
  $("internshipGrid").hidden = true;
  $("resultCount").textContent = "Connecting to InternshipChesko API...";

  $("apiStatusBadge").className = "api-badge connecting";
  $("apiStatusBadge").querySelector(".status-text").textContent = "Connecting API...";

  try {
    const res = await fetch(`${API_BASE}/internships?limit=100`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();
    allInternships = json.data || [];

    $("apiStatusBadge").className = "api-badge connected";
    $("apiStatusBadge").querySelector(".status-text").textContent = "API Live 🟢";

    $("loadingState").hidden = true;
    renderListings();
  } catch (err) {
    $("loadingState").hidden = true;
    $("internshipGrid").hidden = true;
    $("failureState").hidden = false;
    $("failureMessage").textContent = `Unable to connect to backend server (${err.message}). Ensure the server is running on ${API_BASE}.`;
    $("apiStatusBadge").className = "api-badge error";
    $("apiStatusBadge").querySelector(".status-text").textContent = "Offline 🔴";
  }
}

function renderListings() {
  const query = ($("search").value || "").trim().toLowerCase();
  const mode = $("workModeFilter").value;
  const status = $("statusFilter").value;
  const minStipend = Number($("stipendFilter").value) || 0;
  const sort = $("sortFilter").value;
  const savedOnly = $("savedOnly").checked;

  let items = allInternships.filter((item) => {
    if (query) {
      const skillsStr = Array.isArray(item.skills) ? item.skills.join(" ") : "";
      const text = [item.title, item.company, item.location, item.category, skillsStr, item.description].join(" ").toLowerCase();
      if (!text.includes(query)) return false;
    }
    if (activeCategory && item.category !== activeCategory) return false;
    if (mode && item.work_mode !== mode) return false;
    if (status && item.status !== status) return false;
    if (minStipend > 0 && (item.stipend || 0) < minStipend) return false;
    if (savedOnly && !savedIds.includes(item.id)) return false;
    return true;
  });

  if (sort === "stipend-high") {
    items.sort((a, b) => (b.stipend || 0) - (a.stipend || 0));
  } else if (sort === "deadline-soon") {
    items.sort((a, b) => {
      if (!a.deadline) return 1;
      if (!b.deadline) return -1;
      return new Date(a.deadline) - new Date(b.deadline);
    });
  } else {
    items.sort((a, b) => a.id - b.id);
  }

  $("resultCount").textContent = `${items.length} position${items.length === 1 ? "" : "s"} found`;
  $("savedCount").textContent = savedIds.length;

  if (items.length === 0) {
    $("emptyState").hidden = false;
    $("internshipGrid").hidden = true;
    return;
  }

  $("emptyState").hidden = true;
  $("internshipGrid").hidden = false;
  $("internshipGrid").innerHTML = "";

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
    $("internshipGrid").appendChild(card);
  });
}

// -------------------------------------------------------------
// 6. Apply to Internship Modal
// -------------------------------------------------------------
function openApplyModal(id) {
  const item = allInternships.find((i) => i.id === Number(id));
  if (!item) return;

  $("applyInternshipId").value = item.id;
  $("applyModalTitle").textContent = `Apply for ${item.title}`;
  $("applyModalSubtitle").textContent = `${item.company} · ${item.location} (${item.work_mode})`;

  $("applyForm").reset();
  if (currentInternUser) {
    $("fullName").value = currentInternUser.name;
    $("email").value = currentInternUser.email;
    $("phone").value = currentInternUser.phone || "";
  }
  $("applyAlert").hidden = true;
  $("applyModal").hidden = false;
  $("fullName").focus();
}

$("closeApplyModal").addEventListener("click", () => { $("applyModal").hidden = true; });
$("cancelApplyBtn").addEventListener("click", () => { $("applyModal").hidden = true; });

$("applyForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const internshipId = $("applyInternshipId").value;
  const fullName = $("fullName").value.trim();
  const email = $("email").value.trim().toLowerCase();
  const phone = $("phone").value.trim();
  const resumeUrl = $("resumeUrl").value.trim();
  const coverLetter = $("coverLetter").value.trim();

  if (!fullName || !email || !phone || !resumeUrl) {
    showToast("Please complete all required fields.");
    return;
  }

  const payload = { full_name: fullName, email, phone, resume_url: resumeUrl, cover_letter: coverLetter };
  const btn = $("submitApplyBtn");
  btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/internships/${internshipId}/apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const json = await res.json();

    if (res.status === 201) {
      showToast("🎉 Application submitted successfully!");
      $("applyModal").hidden = true;
    } else {
      showToast(json.error?.message || "Failed to submit application.");
    }
  } catch (err) {
    showToast("Network error during application.");
  } finally {
    btn.disabled = false;
  }
});

// -------------------------------------------------------------
// 7. Post an Internship Modal
// -------------------------------------------------------------
$("postInternshipBtn").addEventListener("click", () => {
  $("postForm").reset();
  const d = new Date();
  d.setDate(d.getDate() + 30);
  $("postDeadline").value = d.toISOString().split("T")[0];
  $("postAlert").hidden = true;
  $("postModal").hidden = false;
  $("postTitle").focus();
});

$("closePostModal").addEventListener("click", () => { $("postModal").hidden = true; });
$("cancelPostBtn").addEventListener("click", () => { $("postModal").hidden = true; });

$("postForm").addEventListener("submit", async (e) => {
  e.preventDefault();
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
    showToast("Please fill all required fields.");
    return;
  }

  const skills = rawSkills.split(",").map((s) => s.trim()).filter(Boolean);
  const payload = { title, company, category, location, work_mode: workMode, duration, stipend, skills, deadline, status, description };

  const btn = $("submitPostBtn");
  btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/internships`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (res.status === 201) {
      showToast("✨ New internship posted to InternshipChesko!");
      $("postModal").hidden = true;
      fetchInternships();
    } else {
      showToast("Failed to post internship.");
    }
  } catch (err) {
    showToast("Network error while posting.");
  } finally {
    btn.disabled = false;
  }
});

// -------------------------------------------------------------
// 8. Role Detail View
// -------------------------------------------------------------
function openDetailView(id) {
  const item = allInternships.find((i) => i.id === Number(id));
  if (!item) return;
  const isOpen = item.status === "open";
  const skills = Array.isArray(item.skills) ? item.skills : [];

  $("detailContent").innerHTML = `
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
    <div style="display:flex; justify-content:flex-end; gap:10px;">
      <button class="btn btn-outline" id="detailApplyBtn" ${!isOpen ? 'disabled' : ''}>
        ${isOpen ? 'Apply for this Role' : 'Applications Closed'}
      </button>
    </div>
  `;

  if (isOpen) {
    $("detailApplyBtn").addEventListener("click", () => {
      $("detailModal").hidden = true;
      openApplyModal(item.id);
    });
  }
  $("detailModal").hidden = false;
}

$("closeDetailModal").addEventListener("click", () => { $("detailModal").hidden = true; });

// -------------------------------------------------------------
// 9. Delegator & Global Events
// -------------------------------------------------------------
$("internshipGrid").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-action]");
  if (!btn) return;
  const action = btn.getAttribute("data-action");
  const id = btn.getAttribute("data-id");

  if (action === "apply") openApplyModal(id);
  else if (action === "detail") openDetailView(id);
  else if (action === "save") toggleSave(id);
  else if (action === "share") shareInternship(id);
});

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
  const shareText = `Check out this opening on InternshipChesko 🎯: ${item.title} at ${item.company} (${item.work_mode})!`;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(shareText);
    showToast("Position details copied to clipboard! 📋");
  } else {
    showToast(shareText);
  }
}

// Category Pills
$("categoryPills").addEventListener("click", (e) => {
  const pill = e.target.closest(".pill");
  if (!pill) return;
  document.querySelectorAll(".category-pills .pill").forEach((p) => p.classList.remove("active"));
  pill.classList.add("active");
  activeCategory = pill.getAttribute("data-category");
  renderListings();
});

// Filters & Search
$("search").addEventListener("input", renderListings);
$("workModeFilter").addEventListener("change", renderListings);
$("statusFilter").addEventListener("change", renderListings);
$("sortFilter").addEventListener("change", renderListings);
$("savedOnly").addEventListener("change", renderListings);
$("stipendFilter").addEventListener("input", (e) => {
  $("stipendLabel").textContent = `₹${Number(e.target.value).toLocaleString("en-IN")}/mo`;
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
$("retryBtn").addEventListener("click", fetchInternships);
$("refreshBtn").addEventListener("click", fetchInternships);

window.addEventListener("click", (e) => {
  if (e.target === $("applyModal")) $("applyModal").hidden = true;
  if (e.target === $("detailModal")) $("detailModal").hidden = true;
  if (e.target === $("postModal")) $("postModal").hidden = true;
  if (e.target === $("submitTaskModal")) $("submitTaskModal").hidden = true;
  if (e.target === $("certificateModal")) $("certificateModal").hidden = true;
});

// On Load
document.addEventListener("DOMContentLoaded", () => {
  fetchInternships();
  refreshInternPortal();
  loadAdminMetrics();
});
