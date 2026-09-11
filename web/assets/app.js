const form = document.querySelector("#search-form");
const input = document.querySelector("#search-input");
const button = document.querySelector("#search-button");
const workspace = document.querySelector("#workspace");
const dialog = document.querySelector("#details-dialog");
const detailsContent = document.querySelector("#details-content");

const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"}[char]));
const money = (value) => value == null ? "Not established" : `KSh ${Number(value).toLocaleString()}`;
const domain = (url) => { try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return "Source unavailable"; } };
const statusClass = (status) => String(status || "NEUTRAL").toLowerCase();

function stateFor(survivor) {
  const status = survivor.verification?.status;
  if (status === "CONFLICT") return ["CONFLICT", "conflict"];
  if (["UNKNOWN", "UNVERIFIED"].includes(status)) return ["NEEDS VERIFICATION", "unknown"];
  return ["VERIFIED", "verified"];
}

function evidenceRows(listing) {
  const rows = listing.evidence || [];
  if (!rows.length) return `<p class="muted">No evidence was extracted from this source.</p>`;
  return `<div class="evidence-list">${rows.map((item) => `<div class="evidence-row"><strong>${escapeHtml(item.claim)}</strong><span class="evidence-status ${statusClass(item.status)}">${escapeHtml(item.status)}</span><q>${escapeHtml(item.evidence_text || "No source text found")}</q></div>`).join("")}</div>`;
}

function contactRows(listing) {
  const contacts = listing.contacts || [];
  if (!contacts.length) return `<p class="property-meta">No public contact method established.</p>`;
  return `<div class="contact-list">${contacts.map((contact) => {
    const value = contact.value || "Number not established";
    const link = contact.type === "EMAIL" && contact.value ? `<a href="mailto:${escapeHtml(contact.value)}">${escapeHtml(value)}</a>` : escapeHtml(value);
    return `<div class="contact-row"><strong>${escapeHtml(contact.type || contact.kind)}</strong><span>${link}</span><small>${escapeHtml(contact.contact_scope || "UNKNOWN")}</small></div>`;
  }).join("")}</div>`;
}

function openDetails(survivor) {
  const listing = survivor.listing;
  const [label, css] = stateFor(survivor);
  const source = listing.url ? `<a class="source-link details-source" href="${escapeHtml(listing.url)}" target="_blank" rel="noreferrer">Open original listing <span aria-hidden="true">&#8599;</span></a>` : "<p>Source URL unavailable.</p>";
  const flags = survivor.red_flags?.length ? `<div class="notice">${survivor.red_flags.map(escapeHtml).join("<br>")}</div>` : "";
  detailsContent.innerHTML = `<div class="details-header"><div><p class="eyebrow">Evidence inspection</p><h2 id="details-title">${escapeHtml(listing.location || "Location unknown")}</h2><p class="property-meta">${listing.beds ?? "?"} bedrooms · ${escapeHtml(listing.source || "Source unknown")}</p></div><span class="state ${css}">${label}</span></div><p class="rent">${money(listing.rent)} <small>/ month</small></p>${flags}<h3>Contactability</h3><p class="property-meta">${escapeHtml(listing.contactability || "UNKNOWN")}</p>${contactRows(listing)}<h3>Evidence</h3>${evidenceRows(listing)}<h3>Freshness</h3><p class="property-meta">${escapeHtml(listing.freshness?.explanation || "Freshness not established.")}</p>${source}`;
  dialog.showModal();
}

function propertyCard(survivor, index) {
  const listing = survivor.listing;
  const [label, css] = stateFor(survivor);
  const image = listing.image_urls?.[0] ? `<img class="property-image" src="${escapeHtml(listing.image_urls[0])}" alt="Property photo from ${escapeHtml(listing.source || "source")}" loading="lazy">` : `<div class="image-empty">No source image available</div>`;
  const amenities = (listing.amenities || []).slice(0, 5).map((item) => `<span class="amenity">${escapeHtml(item)}</span>`).join("");
  const actions = survivor.verification?.required_actions || [];
  return `<article class="property-card"><div>${image}</div><div><div class="card-top"><div><p class="eyebrow">Candidate ${String(index + 1).padStart(2, "0")}</p><h3>${escapeHtml(listing.location || "Location unknown")}</h3><p class="property-meta">${listing.beds ?? "?"} bedrooms · ${escapeHtml(listing.source || "Source unknown")}</p></div><span class="state ${css}">${label}</span></div><p class="rent">${money(listing.rent)} <small>/ month</small></p><div class="amenities">${amenities || "<span class=\"property-meta\">Amenities not established</span>"}</div>${actions.length ? `<p class="property-meta">${escapeHtml(actions[0])}</p>` : ""}<div class="card-footer"><span class="source-domain">${escapeHtml(domain(listing.url))}</span><button type="button" data-index="${index}">Inspect evidence</button></div></div></article>`;
}

function renderResult(result) {
  const survivors = result.survivors || [];
  const conflicts = result.duplicate_conflicts || [];
  const rejected = result.rejected || [];
  workspace.innerHTML = `<div class="workspace-heading"><div><p class="eyebrow">Investigation result</p><h2>${survivors.length ? "Listings worth inspecting" : "No listing cleared the first check"}</h2></div><p>${result.discovered} source${result.discovered === 1 ? "" : "s"} checked · ${survivors.length} candidate${survivors.length === 1 ? "" : "s"}</p></div><div class="result-layout"><div class="results-list">${survivors.length ? survivors.map(propertyCard).join("") : `<div class="empty-state"><h2>The evidence needs more work.</h2><p>RouteGuard kept unresolved or over-budget listings out of the candidate list. Review the reasons beside this panel before deciding what to investigate next.</p></div>`}</div><aside class="side-panel"><section><h3>Source conflicts</h3>${conflicts.length ? conflicts.map((item) => `<div class="conflict-item"><strong>Conflict detected</strong>${escapeHtml((item.inconsistencies || item.signals || []).join(" · "))}</div>`).join("") : "<p>No duplicate-source conflicts were detected.</p>"}</section><section><details><summary>Why other listings were rejected (${rejected.length})</summary>${rejected.map((item) => { const contacts = (item.contacts || []).filter((contact) => contact.value).map((contact) => `${contact.type}: ${contact.value}`).join(" · "); return `<div class="rejected-item"><strong>${escapeHtml(item.reason || "Rejected")}</strong><span class="source-domain">${escapeHtml(domain(item.url))}</span>${item.contactability && item.contactability !== "NO_CONTACT" ? `<span class="rejected-contact">${escapeHtml(item.contactability)}${contacts ? ` · ${escapeHtml(contacts)}` : ""}</span>` : ""}</div>`; }).join("")}</details></section></aside></div>`;
  workspace.querySelectorAll("[data-index]").forEach((item) => item.addEventListener("click", () => openDetails(survivors[Number(item.dataset.index)])));
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  button.disabled = true;
  button.querySelector("span").textContent = "Investigating...";
  workspace.innerHTML = `<div class="loading-state"><span class="loading-mark" aria-hidden="true"></span><h2>Checking live listings.</h2><p>Searching sources, extracting evidence, and comparing candidate properties.</p></div>`;
  try {
    const response = await fetch("/api/search", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ request: input.value }) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "The search could not be completed.");
    renderResult(payload.result);
  } catch (error) {
    workspace.innerHTML = `<div class="error-state"><p class="eyebrow">Investigation paused</p><h2>We could not check the sources.</h2><p>${escapeHtml(error.message)}</p></div>`;
  } finally {
    button.disabled = false;
    button.querySelector("span").textContent = "Investigate";
  }
});

document.querySelector(".dialog-close").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });