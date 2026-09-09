import html
import json
import re

import streamlit as st
import api_client

st.set_page_config(
    page_title="SpecWise",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Design System & UI Patch
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
:root {
    --sw-bg: #0b1020;
    --sw-surface: #11182b;
    --sw-surface-2: #17213a;
    --sw-border: #273451;
    --sw-text: #edf2ff;
    --sw-muted: #98a6c5;
    --sw-accent: #7c5cff;
    --sw-accent-2: #22d3ee;
    --sw-success: #34d399;
    --sw-warning: #fbbf24;
    --sw-danger: #ef4444;
    --sw-danger-rgb: 239, 68, 68;
}

/* 1. Fix Top White Header Gap */
header[data-testid="stHeader"] {
    background-color: #0b1020 !important;
    border-bottom: 1px solid #1a233a !important;
    height: 2.75rem !important;
}
[data-testid="stDecoration"] {
    display: none !important;
    height: 0 !important;
}
div[data-testid="stAppViewContainer"] > .main {
    padding-top: 0 !important;
}
div[data-testid="stMainBlockContainer"] {
    padding-top: 1.1rem !important;
}

/* App background */
.stApp {
    background:
        radial-gradient(circle at 15% 0%, rgba(124,92,255,.13), transparent 28%),
        radial-gradient(circle at 90% 10%, rgba(34,211,238,.08), transparent 24%),
        #0b1020;
    color: var(--sw-text);
}

.block-container {
    max-width: 1420px;
    padding-top: 1.1rem !important;
    padding-bottom: 4rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1324 0%, #0a0f1c 100%) !important;
    border-right: 1px solid #202b45 !important;
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 1rem !important;
}

/* Typography */
h1, h2, h3, h4, h5 {
    color: var(--sw-text) !important;
    letter-spacing: -0.02em;
}
p, label, .stCaption {
    color: var(--sw-muted);
}

/* Standard Buttons */
.stButton > button,
.stFormSubmitButton > button {
    border: 1px solid #2b3958 !important;
    border-radius: 10px !important;
    background: #141d33 !important;
    color: #eaf0ff !important;
    font-weight: 600 !important;
    min-height: 38px;
    transition: all .18s ease;
}
.stButton > button:hover,
.stFormSubmitButton > button:hover {
    border-color: var(--sw-accent) !important;
    background: #1b2540 !important;
    transform: translateY(-1px);
}

/* Primary buttons */
button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7657ff, #5b45d9) !important;
    border-color: #8d78ff !important;
}

/* -------------------------------------------------------------------- */
/* Danger / Delete Zone — clear warning-red styling, subtle hover        */
/* -------------------------------------------------------------------- */
.danger-btn button {
    background: rgba(var(--sw-danger-rgb), 0.12) !important;
    border: 1px solid rgba(var(--sw-danger-rgb), 0.45) !important;
    color: #fca5a5 !important;
    font-weight: 600 !important;
}
.danger-btn button:hover {
    background: rgba(var(--sw-danger-rgb), 0.22) !important;
    border-color: var(--sw-danger) !important;
    color: #ffffff !important;
    transform: none;
}
.danger-btn button:focus-visible {
    outline: 2px solid var(--sw-danger) !important;
    outline-offset: 1px;
}

/* Popover delete confirmation theme */
[data-testid="stPopoverBody"] {
    background: #0f172a !important;
    border: 1px solid var(--sw-danger) !important;
    box-shadow: 0 16px 36px rgba(0,0,0,0.6) !important;
    border-radius: 12px !important;
}

.danger-box {
    background: rgba(var(--sw-danger-rgb), 0.10);
    border: 1px solid rgba(var(--sw-danger-rgb), 0.35);
    color: #fecaca;
    padding: 12px 14px;
    border-radius: 8px;
    font-size: 0.88rem;
    margin-bottom: 12px;
    font-weight: 500;
    display: flex;
    align-items: flex-start;
    gap: 8px;
}

/* Small icon-only delete buttons (e.g. remove a document) */
.delete-doc-btn button {
    width: 38px !important;
    height: 38px !important;
    padding: 0 !important;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 9px !important;
}

/* Inputs */
.stTextInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div,
.stFileUploader section {
    background: #11182b !important;
    color: var(--sw-text) !important;
    border-color: #2a3857 !important;
    border-radius: 10px !important;
}

[data-testid="stChatInput"] {
    background: #11182b !important;
    border: 1px solid #334261 !important;
    border-radius: 14px !important;
}
/* Chat input text was invisible (defaulting to a light color on a dark
   field) — force it to the theme's text color explicitly. */
[data-testid="stChatInput"] textarea,
[data-testid="stChatInputTextArea"],
textarea[data-testid="stChatInputTextArea"] {
    color: #111827  !important;
    -webkit-text-fill-color: #111827 !important;
    background: transparent !important;
    caret-color: #111827 !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--sw-muted) !important;
    opacity: 1 !important;
    -webkit-text-fill-color: var(--sw-muted) !important;
}

/* Chat welcome state */
.sw-chat-empty {
    text-align: center;
    padding: 48px 20px 28px;
}

.sw-chat-empty-icon {
    width: 78px;
    height: 78px;
    margin: 0 auto 22px;
    border-radius: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(124,92,255,.20), rgba(34,211,238,.12));
    border: 1px solid #35466b;
    color: #d8d0ff;
    font-size: 34px;
    box-shadow: 0 14px 36px rgba(0,0,0,.16);
}

.sw-chat-empty-title {
    color: #f5f7ff;
    font-size: 1.8rem;
    font-weight: 760;
    line-height: 1.2;
    letter-spacing: -0.025em;
}

.sw-chat-empty-copy {
    color: #8f9dbb;
    max-width: 700px;
    margin: 12px auto 0;
    font-size: 1rem;
    line-height: 1.65;
}

@media (max-width: 700px) {
    .sw-chat-empty { padding-top: 32px; }
    .sw-chat-empty-title { font-size: 1.45rem; }
    .sw-chat-empty-copy { font-size: .9rem; }
}

/* Header & Logo */
.sw-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 20px;
    margin-bottom: 16px;
    margin-top: 30px;
    background: linear-gradient(135deg, rgba(23,33,58,.92), rgba(17,24,43,.95));
    border: 1px solid #2a3857;
    border-radius: 16px;
}
.sw-logo-wrap {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #7c5cff, #22d3ee);
    box-shadow: 0 6px 20px rgba(124,92,255,.3);
    flex-shrink: 0;
}
.sw-logo-svg {
    width: 24px;
    height: 24px;
}
.sw-title {
    font-size: 1.45rem;
    font-weight: 750;
    color: #f5f7ff;
}
.sw-subtitle {
    color: #98a6c5;
    font-size: .86rem;
}

/* 3. Centering Document Rows & Remove X Misalignment */
.doc-row-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
}
.sw-doc {
    padding: 10px 12px;
    border: 1px solid #222f4c;
    border-radius: 10px;
    background: rgba(17,24,43,.68);
    margin: 4px 0;
    min-height: 38px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.sw-doc-name {
    color: #e8edff;
    font-size: .82rem;
    font-weight: 600;
    overflow-wrap: anywhere;
}
.sw-doc-meta {
    color: #8190b0;
    font-size: .72rem;
    margin-top: 2px;
}
.sw-status {
    color: #74e7bb;
    font-size: .70rem;
    font-weight: 700;
}

/* Fix X Delete button alignment inside Streamlit column, regardless of
   how tall the neighbouring document card grows (long file names, 2 lines, etc.) */
div[data-testid="stHorizontalBlock"]:has(.delete-doc-btn) {
    align-items: center !important;
}
div[data-testid="column"]:has(.delete-doc-btn) {
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Grounded badge indicators */
.sw-grounded {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 4px 9px;
    border-radius: 6px;
    margin-bottom: 8px;
    background: rgba(52,211,153,.08);
    border: 1px solid rgba(52,211,153,.22);
    color: #8cebc5;
    font-size: .75rem;
    font-weight: 600;
}
.sw-no-source {
    background: rgba(var(--sw-danger-rgb), .08);
    border-color: rgba(var(--sw-danger-rgb), .25);
    color: #fda4af;
}

/* Context pills */
.sw-context {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin: 4px 0 16px;
}
.sw-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 11px;
    border-radius: 999px;
    background: #121b30;
    border: 1px solid #2a3857;
    color: #c9d3ea;
    font-size: .76rem;
    font-weight: 600;
}
.sw-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #34d399;
}

/* Sources */
.source-badge {
    display: inline-flex;
    align-items: center;
    background: #131d34;
    color: #dbe5ff;
    padding: 5px 9px;
    border-radius: 8px;
    font-size: .76rem;
    margin: 3px 5px 3px 0;
    border: 1px solid #2b3a5c;
    font-weight: 500;
}

/* Copy answer button */
.sw-copy-wrap {
    margin-top: 8px;
}
.sw-copy-btn {
    background: #141d33;
    border: 1px solid #2b3958;
    color: #c9d3ea;
    font-size: .74rem;
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: all .15s ease;
}
.sw-copy-btn:hover {
    border-color: var(--sw-accent);
    color: #eaf0ff;
    background: #1b2540;
}
.sw-copy-btn.sw-copied {
    border-color: var(--sw-success) !important;
    color: #8cebc5 !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session State
# ---------------------------------------------------------------------------
if "project_id" not in st.session_state:
    st.session_state.project_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

# SpecWise Logo — document + "spark" motif (AI reasoning over knowledge docs),
# instead of a plain placeholder letter.
LOGO_ICON_SVG = """
<svg class="sw-logo-svg" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M6 3.5h8.5L19 8v11a1.5 1.5 0 0 1-1.5 1.5H6A1.5 1.5 0 0 1 4.5 19V5A1.5 1.5 0 0 1 6 3.5Z"
          fill="#ffffff" fill-opacity="0.16" stroke="#ffffff" stroke-width="1.4" stroke-linejoin="round"/>
    <path d="M14.5 3.5V8H19" stroke="#ffffff" stroke-width="1.4" stroke-linejoin="round" stroke-linecap="round"/>
    <path d="M7.6 12.6h6M7.6 15.6h4" stroke="#ffffff" stroke-width="1.4" stroke-linecap="round"/>
    <path d="M18.1 11.6c.35.95.85 1.45 1.8 1.8-.95.35-1.45.85-1.8 1.8-.35-.95-.85-1.45-1.8-1.8.95-.35 1.45-.85 1.8-1.8Z"
          fill="#ffffff"/>
</svg>
"""


def _html(fragment: str) -> None:
    """Render a raw HTML/SVG fragment safely.

    Root cause of the raw-HTML-leaking-as-text bug: multi-line f-strings
    (especially ones interpolating LOGO_ICON_SVG, itself multi-line with
    its own indentation) end up with uneven leading whitespace once
    embedded inside Python's indented source code. Streamlit's markdown
    parser then mistakes those unevenly-indented lines for a fenced code
    block and prints the tags literally instead of rendering them.
    Collapsing all whitespace runs (including newlines) to single spaces
    removes any indentation for the parser to misread, while being a
    no-op for how the browser actually renders the HTML.
    """
    flat = re.sub(r"\s+", " ", fragment).strip()
    st.markdown(flat, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Answer rendering helpers
# ---------------------------------------------------------------------------
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_REFUSAL_RE = re.compile(
    r"no supporting document found|isn['\u2019]?t covered in|not covered in .*documents",
    re.IGNORECASE,
)
_ID_BEFORE_DOCS_RE = re.compile(r"\b[0-9a-fA-F]{6,}\b(?=\s*'?s uploaded documents)")


def _clean_answer_text(raw_answer: str, project_id: str | None, project_name: str) -> tuple[str, bool]:
    """Strip any raw HTML/JS, decode stray HTML entities, and hide internal
    project IDs before an answer is ever shown to the user."""
    if not raw_answer:
        return "", False

    text = html.unescape(str(raw_answer))
    text = _HTML_TAG_RE.sub("", text)

    if project_id:
        text = text.replace(str(project_id), project_name)
    text = _ID_BEFORE_DOCS_RE.sub(project_name, text)

    text = re.sub(r"[ \t]+\n", "\n", text).strip()
    is_refusal = bool(_REFUSAL_RE.search(text))
    return text, is_refusal


def _render_copy_button(text: str) -> None:
    if not text:
        return
    payload = json.dumps(text)
    onclick = (
        f"navigator.clipboard.writeText({payload});"
        "this.classList.add('sw-copied');"
        "this.innerText='✓ Copied';"
        "setTimeout(() => { this.innerText='📋 Copy answer'; this.classList.remove('sw-copied'); }, 1600);"
    )
    st.markdown(
        f'<div class="sw-copy-wrap"><button class="sw-copy-btn" onclick="{html.escape(onclick, quote=True)}">📋 Copy answer</button></div>',
        unsafe_allow_html=True,
    )


def _render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"📚 Sources & Citations ({len(sources)})"):
        badges_html = "".join(
            f"<span class='source-badge'>📄 {html.escape(str(s.get('doc_name', 'Document')))}"
            f"{' • ' + html.escape(str(s['section'])) if s.get('section') else ''}</span>"
            for s in sources
        )
        st.markdown(badges_html, unsafe_allow_html=True)


def _render_answer(raw_answer: str, sources: list[dict], project_id: str | None, project_name: str) -> None:
    """Single source of truth for showing an assistant answer: cleans the
    text, shows a proper grounded/refusal state, and never leaks raw HTML,
    escaped entities, or internal IDs into the chat."""
    cleaned, is_refusal = _clean_answer_text(raw_answer, project_id, project_name)

    if is_refusal or not sources:
        st.markdown(
            "<div class='sw-grounded sw-no-source'>⚠️ Not covered in this project's documents</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            cleaned or f"This question isn't addressed in **{project_name}**'s uploaded documents."
        )
    else:
        st.markdown(
            "<div class='sw-grounded'>● Grounded in Project Documentation</div>",
            unsafe_allow_html=True,
        )
        st.markdown(cleaned)
        _render_copy_button(cleaned)

    _render_sources(sources)


# ---------------------------------------------------------------------------
# Fetch Projects
# ---------------------------------------------------------------------------
projects_result = api_client.list_projects()
projects = projects_result.get("data", []) if projects_result["ok"] else []
project_map = {p["id"]: p for p in projects}

if st.session_state.project_id and st.session_state.project_id not in project_map:
    st.session_state.project_id = None

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    _html(
        f"""
        <div class="sw-header" style="padding:10px 12px; margin-bottom:16px;">
            <div class="sw-logo-wrap" style="width:38px;height:38px;">
                {LOGO_ICON_SVG}
            </div>
            <div>
                <div class="sw-title" style="font-size:1.15rem;">SpecWise</div>
                <div class="sw-subtitle">Docs Intelligence</div>
            </div>
        </div>
        """
    )

    with st.expander("➕ New Project", expanded=len(projects) == 0):
        with st.form("create_project_form", clear_on_submit=True):
            new_name = st.text_input("Project Name", placeholder="e.g. UDORM Core API")
            new_description = st.text_area(
                "Description",
                placeholder="Scope, architecture specs...",
                height=68,
            )
            submitted = st.form_submit_button("Create Project", use_container_width=True)
            if submitted:
                if not new_name.strip():
                    st.warning("Project name is required.")
                else:
                    with st.spinner("Creating..."):
                        result = api_client.create_project(
                            new_name.strip(),
                            new_description.strip() or None,
                        )
                    if result["ok"]:
                        st.session_state.project_id = result["data"]["id"]
                        st.session_state.chat_history = []
                        st.session_state.search_results = []
                        st.rerun()
                    else:
                        st.error(f"Failed: {result['error']}")

    st.divider()

    st.markdown("##### Projects")
    if projects:
        project_names = [p["name"] for p in projects]
        current_name = (
            project_map[st.session_state.project_id]["name"]
            if st.session_state.project_id
            else project_names[0]
        )
        selected_name = st.selectbox(
            "Select Project",
            project_names,
            index=project_names.index(current_name),
            label_visibility="collapsed",
        )
        selected_project = next(p for p in projects if p["name"] == selected_name)
        prev_proj_id = st.session_state.project_id
        st.session_state.project_id = selected_project["id"]

        if prev_proj_id != st.session_state.project_id:
            st.session_state.chat_history = []
            st.session_state.search_results = []

        with st.expander("⚙️ Settings & Delete"):
            st.markdown(f"**{html.escape(selected_project['name'])}**")
            if selected_project.get("description"):
                st.caption(selected_project["description"])

            with st.popover("🗑️ Delete Project", use_container_width=True):
                _html(
                    f"""
                    <div class="danger-box">
                        <span>⚠️</span>
                        <span><b>Warning:</b> Permanently delete <b>{html.escape(selected_project['name'])}</b>
                        and drop all Chroma vector embeddings? This cannot be undone.</span>
                    </div>
                    """
                )
                st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
                if st.button("🗑️ Yes, Permanently Delete", use_container_width=True):
                    with st.spinner("Deleting..."):
                        del_res = api_client.delete_project(selected_project["id"])
                    if del_res["ok"]:
                        st.session_state.project_id = None
                        st.session_state.chat_history = []
                        st.session_state.search_results = []
                        st.rerun()
                    else:
                        st.error(f"Error: {del_res['error']}")
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No projects yet.")

    st.divider()

    # Document management
    if st.session_state.project_id:
        st.markdown("##### Documents")
        docs_res = api_client.list_documents(st.session_state.project_id)
        docs = docs_res["data"] if docs_res["ok"] else []

        with st.expander("📤 Add Documents", expanded=not bool(docs)):
            uploaded_files = st.file_uploader(
                "Upload files",
                type=["md", "txt", "pdf"],
                accept_multiple_files=True,
                key="file_uploader",
                label_visibility="collapsed",
            )
            if uploaded_files and st.button(f"Index {len(uploaded_files)} File(s)", type="primary", use_container_width=True):
                progress = st.progress(0, text="Indexing...")
                for idx, file in enumerate(uploaded_files):
                    api_client.upload_document(
                        st.session_state.project_id,
                        file.name,
                        file.getvalue(),
                        file.type or "application/octet-stream",
                    )
                    progress.progress((idx + 1) / len(uploaded_files), text=f"Indexed {file.name}")
                st.success("Indexed successfully.")
                st.rerun()

        if docs:
            for doc in docs:
                col_info, col_del = st.columns([5, 1], vertical_alignment="center")
                with col_info:
                    _html(
                        f"""
                        <div class="sw-doc">
                            <div class="sw-doc-name">📄 {html.escape(str(doc['name']))}</div>
                            <div class="sw-doc-meta">
                                {doc['chunk_count']} chunks · <span class="sw-status">● Indexed</span>
                            </div>
                        </div>
                        """
                    )
                with col_del:
                    st.markdown('<div class="delete-doc-btn danger-btn">', unsafe_allow_html=True)
                    if st.button("✕", key=f"del_doc_{doc['name']}", help=f"Delete {doc['name']}"):
                        with st.spinner("Deleting..."):
                            api_client.delete_document(st.session_state.project_id, doc["name"])
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.caption("No documents indexed yet.")

# ---------------------------------------------------------------------------
# Main Area
# ---------------------------------------------------------------------------
if not st.session_state.project_id:
    _html(
        f"""
        <div style="text-align:center; padding: 60px 20px;">
            <div class="sw-logo-wrap" style="width:58px;height:58px;margin:0 auto 16px;">
                {LOGO_ICON_SVG}
            </div>
            <h2>Welcome to SpecWise</h2>
            <p>Multi-project RAG assistant for software engineering documentation</p>
        </div>
        """
    )
    st.info("👈 Select or create a project from the sidebar to begin.")
    st.stop()

active_proj = project_map.get(st.session_state.project_id)
docs_data = api_client.list_documents(st.session_state.project_id)
active_doc_count = len(docs_data["data"]) if docs_data["ok"] else 0

# Header
_html(
    f"""
    <div class="sw-header">
        <div class="sw-logo-wrap">
            {LOGO_ICON_SVG}
        </div>
        <div style="flex:1">
            <div class="sw-title">{html.escape(str(active_proj['name']))}</div>
            <div class="sw-subtitle">
                {html.escape(str(active_proj.get('description') or 'Multi-project RAG assistant for software engineering documentation'))}
            </div>
        </div>
    </div>
    """
)

# Context Pills
_html(
    f"""
    <div class="sw-context">
        <span class="sw-pill"><span class="sw-dot"></span> Active Project</span>
        <span class="sw-pill">📚 {active_doc_count} Document(s) Indexed</span>
        <span class="sw-pill">🔒 Isolated Knowledge Base</span>
    </div>
    """
)

# Top Bar Actions
col_new, col_clear = st.columns([1, 1])
with col_new:
    if st.button("＋ New Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
with col_clear:
    if st.button("🧹 Clear History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

tab_chat, tab_search = st.tabs(["💬 Chat", "🔍 Semantic Search"])

# ---------------------------------------------------------------------------
# Chat Tab
# ---------------------------------------------------------------------------
with tab_chat:
    for entry in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(entry["question"])

        with st.chat_message("assistant"):
            _render_answer(
                entry["answer"],
                entry.get("sources", []),
                st.session_state.project_id,
                active_proj["name"],
            )

    prompt_to_run = None
    if not st.session_state.chat_history:
        # Chat welcome state — visual-only change. All chat logic below remains unchanged.
        st.markdown(
            """
            <div class="sw-chat-empty">
                <div class="sw-chat-empty-icon">✦</div>
                <div class="sw-chat-empty-title">Ask your project anything</div>
                <div class="sw-chat-empty-copy">
                    Explore requirements, architecture, security rules, and other
                    indexed project documentation.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        q1, q2, q3 = st.columns(3)
        if q1.button("Functional Requirements", use_container_width=True):
            prompt_to_run = "What are the key functional requirements outlined in this project's documentation?"
        if q2.button("System Architecture", use_container_width=True):
            prompt_to_run = "Describe the system architecture and technical components."
        if q3.button("Security & Auth Rules", use_container_width=True):
            prompt_to_run = "What are the authentication and security rules specified?"

    user_input = st.chat_input(f"Ask about {active_proj['name']} documentation...")
    question = user_input or prompt_to_run

    if question:
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching documentation and synthesizing answer..."):
                result = api_client.query(question, st.session_state.project_id)

            if result["ok"]:
                data = result["data"]
                sources = data.get("sources", [])

                _render_answer(
                    data["answer"],
                    sources,
                    st.session_state.project_id,
                    active_proj["name"],
                )

                st.session_state.chat_history.append(
                    {
                        "question": question,
                        "answer": data["answer"],
                        "sources": sources,
                    }
                )
            else:
                st.error(f"Query failed: {result['error']}")

# ---------------------------------------------------------------------------
# Semantic Search Tab
# ---------------------------------------------------------------------------
with tab_search:
    st.caption("Find matching chunks from the project vector store without LLM synthesis.")
    col_input, col_k = st.columns([5, 1])
    with col_input:
        search_query = st.text_input(
            "Search query",
            placeholder="e.g. database schema, token expiry...",
            key="search_input",
            label_visibility="collapsed",
        )
    with col_k:
        k_val = st.slider("Top K", min_value=1, max_value=10, value=4, label_visibility="collapsed")

    if st.button("Search Vector Store", type="primary", use_container_width=True) and search_query.strip():
        with st.spinner("Retrieving chunks..."):
            result = api_client.search(search_query.strip(), st.session_state.project_id, k=k_val)

        if result["ok"]:
            st.session_state.search_results = result["data"]["results"]
            st.session_state.search_query = search_query.strip()
        else:
            st.error(f"Search failed: {result['error']}")

    results = st.session_state.search_results
    if st.session_state.search_query and not results:
        st.info("No matching chunks found.")

    for r in results:
        section = f" — {r['section']}" if r.get("section") else ""
        relevance_pct = max(0, min(100, round((1.0 - float(r["distance"])) * 100)))
        with st.container(border=True):
            st.markdown(
                f"**📄 {html.escape(str(r['doc_name']))}{html.escape(section)}** &nbsp; `Relevance: {relevance_pct}%`"
            )
            st.write(r["text"])