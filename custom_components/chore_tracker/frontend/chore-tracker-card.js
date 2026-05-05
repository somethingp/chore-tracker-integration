/**
 * Chore Tracker Card — Home Assistant Lovelace Custom Card
 * Communicates with the Chore Tracker integration via WebSocket.
 * Requires the Chore Tracker integration to be installed.
 *
 * Config:
 *   type: custom:chore-tracker-card
 *   title: Chores   (optional)
 */

const VERSION = "2.0.0";
const MS_DAY = 86_400_000;

// ── Helpers ───────────────────────────────────────────────────────────────────
function daysAgo(ts) {
  return ts == null ? Infinity : (Date.now() - ts) / MS_DAY;
}
function getStatus(chore) {
  const ago = daysAgo(chore.lastDone);
  if (ago < chore.freqDays)     return "ok";
  if (ago < chore.freqDays * 2) return "due";
  return "overdue";
}
function freqLabel(d) {
  if (d === 1)  return "daily";
  if (d === 7)  return "weekly";
  if (d === 14) return "bi-weekly";
  if (d === 30) return "monthly";
  return `every ${d}d`;
}
function timeLabel(chore) {
  if (!chore.lastDone) return "never done";
  const ago = daysAgo(chore.lastDone);
  if (ago < 1 / 24) return "just now";
  if (ago < 1)      return `${Math.round(ago * 24)}h ago`;
  if (ago < 2)      return "yesterday";
  return `${Math.floor(ago)}d ago`;
}
function statusText(chore) {
  const s = getStatus(chore);
  const t = timeLabel(chore);
  if (s === "ok")  return t;
  if (s === "due") return `overdue · ${t}`;
  return `way overdue · ${t}`;
}

// ── Styles ────────────────────────────────────────────────────────────────────
const STYLES = `
  :host {
    --c-ok:       #4a7c3f;
    --c-ok-bg:    #eaf3de;
    --c-due:      #7c5a1a;
    --c-due-bg:   #fdf3dc;
    --c-over:     #8b2a2a;
    --c-over-bg:  #fdeaea;
    --c-bar-ok:   #639922;
    --c-bar-due:  #d4850a;
    --c-bar-over: #d94040;
    font-family: var(--primary-font-family, sans-serif);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  .card { padding: 16px; }
  .card-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 12px; flex-wrap: wrap; gap: 8px;
  }
  .card-title { font-size: 16px; font-weight: 500; color: var(--primary-text-color); }
  .current-user {
    font-size: 12px; color: var(--secondary-text-color);
    background: var(--secondary-background-color, #f5f5f5);
    padding: 3px 10px; border-radius: 14px;
    border: 1px solid var(--divider-color, #e0e0e0);
  }
  .legend { display: flex; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }
  .leg { display: flex; align-items: center; gap: 4px; font-size: 11px; color: var(--secondary-text-color); }
  .leg-dot { width: 7px; height: 7px; border-radius: 50%; }
  .chore-list { display: flex; flex-direction: column; gap: 5px; }
  .chore-row {
    display: flex; align-items: center; gap: 10px; padding: 9px 12px;
    border-radius: 8px; background: var(--secondary-background-color, #f5f5f5);
    transition: opacity 0.25s;
  }
  .chore-row.just-done { opacity: 0.5; }
  .status-bar { width: 3px; height: 36px; border-radius: 2px; flex-shrink: 0; }
  .bar-ok   { background: var(--c-bar-ok); }
  .bar-due  { background: var(--c-bar-due); }
  .bar-over { background: var(--c-bar-over); }
  .chore-info { flex: 1; min-width: 0; }
  .chore-name {
    font-size: 13px; font-weight: 500; color: var(--primary-text-color);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .chore-sub { font-size: 11px; color: var(--secondary-text-color); margin-top: 1px; }
  .status-pill {
    font-size: 11px; font-weight: 500; padding: 2px 8px;
    border-radius: 10px; flex-shrink: 0; white-space: nowrap;
  }
  .pill-ok   { background: var(--c-ok-bg);   color: var(--c-ok);   }
  .pill-due  { background: var(--c-due-bg);  color: var(--c-due);  }
  .pill-over { background: var(--c-over-bg); color: var(--c-over); }
  .row-actions { display: flex; gap: 5px; align-items: center; flex-shrink: 0; }
  .undo-btn {
    background: transparent; border: 1px solid var(--divider-color, #e0e0e0);
    border-radius: 6px; padding: 2px 7px; font-size: 13px; cursor: pointer;
    color: var(--secondary-text-color); font-family: inherit; line-height: 1.6;
  }
  .undo-btn:hover { background: var(--divider-color, #e0e0e0); }
  .del-btn {
    background: transparent; border: none; cursor: pointer;
    color: var(--secondary-text-color); font-size: 15px;
    padding: 2px 4px; border-radius: 4px; line-height: 1;
    opacity: 0; transition: opacity 0.15s;
  }
  .chore-row:hover .del-btn { opacity: 1; }
  .del-btn:hover { color: var(--c-over); }
  .check-btn {
    width: 28px; height: 28px; border-radius: 50%;
    border: 1.5px solid var(--divider-color, #ccc);
    background: transparent; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; transition: background 0.15s, border-color 0.15s;
    color: transparent; font-size: 14px;
  }
  .check-btn:hover { border-color: var(--c-bar-ok); color: var(--c-bar-ok); }
  .check-btn.done { background: var(--c-bar-ok); border-color: var(--c-bar-ok); color: #fff; }
  .check-btn::after { content: "✓"; }
  .divider { height: 1px; background: var(--divider-color, #e0e0e0); margin: 12px 0 10px; }
  .add-label {
    font-size: 11px; font-weight: 500; color: var(--secondary-text-color);
    text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 7px;
  }
  .add-section { display: flex; gap: 6px; flex-wrap: wrap; }
  .add-section input, .add-section select {
    padding: 6px 9px; border-radius: 7px;
    border: 1px solid var(--divider-color, #ccc);
    background: var(--secondary-background-color, #f5f5f5);
    color: var(--primary-text-color); font-size: 12px; font-family: inherit; outline: none;
  }
  .add-section input { flex: 1; min-width: 110px; }
  .add-section input:focus, .add-section select:focus { border-color: var(--primary-color, #03a9f4); }
  .add-btn {
    padding: 6px 12px; border-radius: 7px; border: none;
    background: var(--primary-color, #03a9f4); color: #fff;
    font-size: 12px; font-weight: 500; cursor: pointer; font-family: inherit;
  }
  .add-btn:hover { opacity: 0.88; }
  .status-bar-loading {
    display: flex; align-items: center; gap: 8px; padding: 12px 0;
    font-size: 13px; color: var(--secondary-text-color);
  }
  .spinner {
    width: 14px; height: 14px;
    border: 2px solid var(--divider-color, #ccc);
    border-top-color: var(--primary-color, #03a9f4);
    border-radius: 50%; animation: spin 0.7s linear infinite; flex-shrink: 0;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .error-msg {
    font-size: 12px; color: var(--c-over); padding: 8px 10px;
    background: var(--c-over-bg); border-radius: 6px; margin-bottom: 8px;
    line-height: 1.5;
  }
  .empty { text-align: center; font-size: 13px; color: var(--secondary-text-color); padding: 16px 0; }
`;

// ── Custom Element ─────────────────────────────────────────────────────────────
class ChoreTrackerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._chores = [];
    this._nextId = 1;
    this._hass = null;
    this._currentUser = null;
    this._loading = true;
    this._error = null;
    this._busy = new Set();
    this._loaded = false;
    this._refreshTimer = null;
  }

  connectedCallback() {
    this._refreshTimer = setInterval(() => this._render(), 60_000);
  }

  disconnectedCallback() {
    clearInterval(this._refreshTimer);
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._currentUser && hass.user?.name) {
      this._currentUser = hass.user.name;
    }
    if (!this._loaded) {
      this._loaded = true;
      this._fetchChores();
    }
  }

  setConfig(config) {
    if (!config) throw new Error("Invalid configuration");
    this._config = config;
    this._render();
  }

  static getStubConfig() {
    return { title: "Chores" };
  }

  getCardSize() {
    return Math.max(3, Math.ceil(this._chores.length / 2) + 3);
  }

  // ── WebSocket helpers ─────────────────────────────────────────────────────────
  async _send(msg) {
    return this._hass.connection.sendMessagePromise(msg);
  }

  async _fetchChores() {
    this._loading = true;
    this._render();
    try {
      const result = await this._send({ type: "chore_tracker/get_chores" });
      this._chores = result.chores || [];
      this._nextId = result.nextId || 1;
      this._error = null;
    } catch (e) {
      this._error = `Could not load chores. Is the Chore Tracker integration installed?\n${e.message || JSON.stringify(e)}`;
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _markDone(id) {
    if (this._busy.has(id)) return;
    this._busy.add(id);
    this._render();
    try {
      const updated = await this._send({
        type: "chore_tracker/complete_chore",
        chore_id: id,
        user: this._currentUser || "Unknown",
      });
      this._patchChore(updated);
      this._error = null;
    } catch (e) {
      this._error = `Failed to complete chore: ${e.message || JSON.stringify(e)}`;
    } finally {
      this._busy.delete(id);
      this._render();
    }
  }

  async _undo(id) {
    if (this._busy.has(id)) return;
    this._busy.add(id);
    this._render();
    try {
      const updated = await this._send({
        type: "chore_tracker/undo_chore",
        chore_id: id,
      });
      this._patchChore(updated);
      this._error = null;
    } catch (e) {
      this._error = `Failed to undo: ${e.message || JSON.stringify(e)}`;
    } finally {
      this._busy.delete(id);
      this._render();
    }
  }

  async _addChore(name, freqDays) {
    if (!name.trim()) return;
    try {
      const created = await this._send({
        type: "chore_tracker/add_chore",
        name: name.trim(),
        freq_days: freqDays,
      });
      this._chores.push(created);
      this._error = null;
    } catch (e) {
      this._error = `Failed to add chore: ${e.message || JSON.stringify(e)}`;
    }
    this._render();
  }

  async _deleteChore(id) {
    try {
      await this._send({ type: "chore_tracker/delete_chore", chore_id: id });
      this._chores = this._chores.filter(c => c.id !== id);
      this._error = null;
    } catch (e) {
      this._error = `Failed to delete chore: ${e.message || JSON.stringify(e)}`;
    }
    this._render();
  }

  _patchChore(updated) {
    const idx = this._chores.findIndex(c => c.id === updated.id);
    if (idx !== -1) this._chores[idx] = updated;
  }

  // ── Render ────────────────────────────────────────────────────────────────────
  _render() {
    const title = this._config.title || "Chores";
    const ORDER = { overdue: 0, due: 1, ok: 2 };
    const sorted = [...this._chores].sort((a, b) => ORDER[getStatus(a)] - ORDER[getStatus(b)]);
    const root = this.shadowRoot;

    root.innerHTML = `
      <style>${STYLES}</style>
      <ha-card class="card">
        <div class="card-header">
          <span class="card-title">${title}</span>
          ${this._currentUser ? `<span class="current-user">${this._currentUser}</span>` : ""}
        </div>
        ${this._error ? `<div class="error-msg">${this._error}</div>` : ""}
        ${this._loading
          ? `<div class="status-bar-loading"><div class="spinner"></div> Loading chores…</div>`
          : `
          <div class="legend">
            <span class="leg"><span class="leg-dot" style="background:var(--c-bar-ok)"></span>On time</span>
            <span class="leg"><span class="leg-dot" style="background:var(--c-bar-due)"></span>Overdue</span>
            <span class="leg"><span class="leg-dot" style="background:var(--c-bar-over)"></span>Way overdue</span>
          </div>
          <div class="chore-list">
            ${sorted.length === 0
              ? '<div class="empty">No chores yet — add one below.</div>'
              : sorted.map(c => {
                  const s = getStatus(c);
                  const barCls  = { ok:"bar-ok", due:"bar-due", overdue:"bar-over" }[s];
                  const pillCls = { ok:"pill-ok", due:"pill-due", overdue:"pill-over" }[s];
                  const justDone = c.lastDone && (Date.now() - c.lastDone) < 90_000;
                  const busy = this._busy.has(c.id);
                  const byLine = c.lastBy ? ` · ${c.lastBy}` : "";
                  return `
                    <div class="chore-row ${justDone ? "just-done" : ""}">
                      <div class="status-bar ${barCls}"></div>
                      <div class="chore-info">
                        <div class="chore-name">${c.name}</div>
                        <div class="chore-sub">${freqLabel(c.freqDays)}${byLine}</div>
                      </div>
                      <span class="status-pill ${pillCls}">${statusText(c)}</span>
                      <div class="row-actions">
                        <button class="del-btn" data-del="${c.id}" title="Delete chore">✕</button>
                        ${c.history?.length > 0
                          ? `<button class="undo-btn" data-undo="${c.id}" ${busy ? "disabled" : ""}>↩</button>`
                          : ""}
                        <button class="check-btn ${justDone ? "done" : ""}"
                                data-check="${c.id}"
                                title="Mark done"
                                ${busy ? "disabled" : ""}></button>
                      </div>
                    </div>`;
                }).join("")}
          </div>
          <div class="divider"></div>
          <div class="add-label">Add chore</div>
          <div class="add-section">
            <input id="newName" type="text" placeholder="Chore name" maxlength="60" />
            <select id="newFreq">
              <option value="1">Daily</option>
              <option value="2">Every 2 days</option>
              <option value="3">Every 3 days</option>
              <option value="7" selected>Weekly</option>
              <option value="14">Bi-weekly</option>
              <option value="30">Monthly</option>
            </select>
            <button class="add-btn" id="addBtn">+ Add</button>
          </div>`}
      </ha-card>
    `;

    root.querySelectorAll("[data-check]").forEach(btn =>
      btn.addEventListener("click", () => this._markDone(Number(btn.dataset.check)))
    );
    root.querySelectorAll("[data-undo]").forEach(btn =>
      btn.addEventListener("click", () => this._undo(Number(btn.dataset.undo)))
    );
    root.querySelectorAll("[data-del]").forEach(btn =>
      btn.addEventListener("click", () => {
        const chore = this._chores.find(c => c.id === Number(btn.dataset.del));
        if (chore && confirm(`Delete "${chore.name}"?`)) this._deleteChore(chore.id);
      })
    );
    const addBtn = root.getElementById("addBtn");
    const nameInput = root.getElementById("newName");
    if (addBtn && nameInput) {
      const doAdd = () => {
        const freq = parseInt(root.getElementById("newFreq").value, 10);
        this._addChore(nameInput.value, freq);
        nameInput.value = "";
      };
      addBtn.addEventListener("click", doAdd);
      nameInput.addEventListener("keydown", e => { if (e.key === "Enter") doAdd(); });
    }
  }
}

customElements.define("chore-tracker-card", ChoreTrackerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "chore-tracker-card",
  name: "Chore Tracker",
  description: "Track household chores with color-coded urgency. Requires the Chore Tracker integration.",
  preview: true,
  documentationURL: "https://github.com/somethingp/chore-tracker-card",
});

console.info(
  `%c CHORE-TRACKER-CARD %c v${VERSION} `,
  "color:#fff;background:#639922;padding:2px 4px;border-radius:3px 0 0 3px",
  "color:#639922;background:#eaf3de;padding:2px 4px;border-radius:0 3px 3px 0"
);
