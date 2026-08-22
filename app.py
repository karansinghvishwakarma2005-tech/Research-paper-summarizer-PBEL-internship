import streamlit as st
import os
import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from google import genai
from google.genai import types
import pypdf
from dotenv import load_dotenv

# Load local .env file if present
load_dotenv()

# Persistence for Paper History
HISTORY_FILE = "paper_history.json"

def load_persistent_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_persistent_history(history_list):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_list, f, indent=2)
    except Exception:
        pass

# Initialize session state for history
if "paper_history" not in st.session_state:
    st.session_state["paper_history"] = load_persistent_history()

# Set Page Config
st.set_page_config(
    page_title="AI Research Paper Summarizer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling for rich academic aesthetics and theme-aware contrast coordination
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap');
    
    :root {
        --card-bg: #FFFFFF;
        --card-border: #E2E8F0;
        --card-text: #1E293B;
        --card-subtext: #475569;
        --title-color: #0F172A;
        --tldr-bg: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
        --tldr-border: #10B981;
        --tldr-title: #065F46;
        --tldr-text: #064E3B;
    }

    @media (prefers-color-scheme: dark) {
        :root {
            --card-bg: #1E293B;
            --card-border: #334155;
            --card-text: #F8FAFC;
            --card-subtext: #94A3B8;
            --title-color: #F8FAFC;
            --tldr-bg: linear-gradient(135deg, #064E3B 0%, #022C22 100%);
            --tldr-border: #34D399;
            --tldr-title: #A7F3D0;
            --tldr-text: #ECFDF5;
        }
    }

    /* Fallback for explicit dark theme containers */
    [data-theme="dark"], [data-testid="stAppViewContainer"][data-theme="dark"] {
        --card-bg: #1E293B;
        --card-border: #334155;
        --card-text: #F8FAFC;
        --card-subtext: #94A3B8;
        --title-color: #F8FAFC;
        --tldr-bg: linear-gradient(135deg, #064E3B 0%, #022C22 100%);
        --tldr-border: #34D399;
        --tldr-title: #A7F3D0;
        --tldr-text: #ECFDF5;
    }

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    .main-header {
        font-family: 'Playfair Display', serif;
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366F1 0%, #06B6D4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }

    .sub-header {
        font-size: 1.1rem;
        color: var(--card-subtext);
        margin-bottom: 2rem;
        font-weight: 400;
    }

    .tldr-card {
        background: var(--tldr-bg);
        border-left: 5px solid var(--tldr-border);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.06);
        color: var(--tldr-text);
    }

    .tldr-title {
        font-weight: 700;
        color: var(--tldr-title);
        font-size: 1.15rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .tldr-content {
        color: var(--tldr-text);
        font-size: 1.05rem;
        line-height: 1.6;
    }

    .section-card {
        background-color: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 16px;
        padding: 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.04);
        color: var(--card-text);
    }

    .section-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.5rem;
        color: var(--title-color);
        font-weight: 700;
        border-bottom: 2px solid var(--card-border);
        padding-bottom: 0.6rem;
        margin-bottom: 1.2rem;
    }

    .card-content {
        color: var(--card-text);
        font-size: 1.05rem;
        line-height: 1.65;
    }

    .metric-badge {
        background-color: rgba(99, 102, 241, 0.12);
        color: #6366F1;
        font-weight: 600;
        padding: 0.3rem 0.8rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        border: 1px solid rgba(99, 102, 241, 0.25);
    }
</style>
""", unsafe_allow_html=True)

# Helper Functions
def init_gemini_client(api_key):
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize Gemini Client: {e}")
        return None

def generate_content_with_fallback(client, contents, config=None):
    models = ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest"]
    last_error = None
    
    for model in models:
        # Try 2 attempts per model for temporary high demand (503) or rate limits (429)
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
                return response, model
            except Exception as e:
                last_error = e
                err_msg = str(e)
                err_msg_upper = err_msg.upper()
                
                # Fatal auth errors raise immediately
                if "API_KEY_INVALID" in err_msg_upper or "API KEY NOT VALID" in err_msg_upper:
                    raise e
                
                # If 503 UNAVAILABLE or 429 high demand on 1st attempt, wait 1.5s and retry same model
                if ("503" in err_msg or "UNAVAILABLE" in err_msg_upper or "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg_upper) and attempt == 0:
                    time.sleep(1.5)
                    continue
                
                # If retries exhausted for this model, show a clean toast notification before trying fallback
                if model != models[-1]:
                    st.toast(f"ℹ️ {model} is experiencing temporary high demand. Switching to backup model ({models[models.index(model)+1]})...", icon="🔄")
                break
    raise last_error

def extract_text_from_pdf(uploaded_file):
    try:
        reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text
    except Exception as e:
        st.error(f"Failed to read PDF file: {e}")
        return ""

def fetch_arxiv_data(arxiv_query):
    try:
        # Extract arXiv ID
        match = urllib.parse.urlparse(arxiv_query)
        path_parts = match.path.split('/')
        # E.g. check if url has /pdf/ or /abs/ or is just raw ID
        arxiv_id = arxiv_query.strip()
        if 'arxiv.org' in arxiv_query:
            for part in path_parts:
                if part and not part.endswith('.pdf') and part not in ['abs', 'pdf']:
                    arxiv_id = part.replace('.pdf', '')
                    break
                elif part.endswith('.pdf'):
                    arxiv_id = part.replace('.pdf', '')
                    break
        
        # Build export query URL
        url = f"https://export.arxiv.org/api/query?id_list={urllib.parse.quote(arxiv_id)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entry = root.find('atom:entry', ns)
        if entry is not None:
            title = entry.find('atom:title', ns)
            summary = entry.find('atom:summary', ns)
            published = entry.find('atom:published', ns)
            
            title_text = title.text.strip().replace('\n', ' ') if title is not None else "Unknown Title"
            abstract_text = summary.text.strip().replace('\n', ' ') if summary is not None else "No Abstract"
            year_text = published.text[:4] if published is not None else "Unknown Year"
            
            authors = []
            for author_node in entry.findall('atom:author', ns):
                name_node = author_node.find('atom:name', ns)
                if name_node is not None:
                    authors.append(name_node.text.strip())
            
            return {
                "arxivId": arxiv_id,
                "title": title_text,
                "abstract": abstract_text,
                "authors": authors,
                "year": year_text,
                "pdfUrl": f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            }
        else:
            st.error("No paper found for the given arXiv ID/URL.")
    except Exception as e:
        st.error(f"Error fetching ArXiv metadata: {e}")
    return None

# App Layout
st.markdown('<div class="main-header">🎓 AI Research Paper Summarizer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Synthesis and interactive exploration of scientific literature powered by Gemini 3.7 Flash</div>', unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.markdown("### 🔑 API Access Status")
    env_api_key = os.environ.get("GEMINI_API_KEY", "")
    
    if env_api_key:
        api_key = env_api_key
        st.success("🔒 API Key Configured & Protected")
        st.caption("Loaded securely from `.env`. Fully restricted from UI.")
    else:
        api_key_input = st.text_input("Gemini API Key", type="password", help="Enter your Google Gemini API key here")
        api_key = api_key_input
        if not api_key:
            st.warning("⚠️ No API key detected. Please configure `GEMINI_API_KEY` in `.env` file.")
    
    st.markdown("---")
    st.markdown("### ⚙️ Synthesizer Settings")
    
    summary_mode = st.selectbox(
        "Analysis Mode",
        options=[
            ("Standard Academic", "standard"),
            ("Deep Dive & Mathematical Foundations", "deep_dive"),
            ("Critical Peer Reviewer Critique", "critical_review"),
            ("ELI5 (Explain Like I'm 5)", "eli5"),
            ("Methodology & Equations Focus", "methodology_focus")
        ],
        format_func=lambda x: x[0]
    )
    
    target_audience = st.selectbox(
        "Target Audience",
        options=[
            ("Researcher / Domain Expert", "researcher"),
            ("Student / Learner", "student"),
            ("Industry Practitioner / Software Engineer", "practitioner"),
            ("Executive / Decision Maker", "executive")
        ],
        format_func=lambda x: x[0]
    )
    
    custom_focus = st.text_input(
        "Special Focus Area (Optional)", 
        placeholder="e.g. Memory constraints, Ablation studies..."
    )
    
    st.markdown("---")
    st.markdown("### 📜 Saved Paper History")
    
    history_list = st.session_state.get("paper_history", [])
    if not history_list:
        st.caption("No papers saved in history yet. Upload a PDF or search arXiv to populate history.")
    else:
        st.caption(f"Total Saved: **{len(history_list)}** paper(s)")
        
        paper_titles = [f"{idx+1}. {item['title'][:38]}..." if len(item['title']) > 38 else f"{idx+1}. {item['title']}" for idx, item in enumerate(history_list)]
        selected_idx = st.selectbox(
            "Select a paper to restore:",
            options=range(len(paper_titles)),
            format_func=lambda i: paper_titles[i],
            key="history_select_dropdown"
        )
        
        btn_col1, btn_col2 = st.columns([3, 1])
        with btn_col1:
            if st.button("📂 Load Paper", use_container_width=True, type="primary"):
                selected_item = history_list[selected_idx]
                st.session_state["summary_data"] = selected_item["summary_data"]
                st.session_state["full_paper_text"] = selected_item.get("full_paper_text", "")
                st.session_state["chat_history"] = selected_item.get("chat_history", [])
                st.toast(f"Loaded: {selected_item['title'][:30]}...", icon="📄")
                st.rerun()
        with btn_col2:
            if st.button("🗑️", help="Delete selected paper from history"):
                del history_list[selected_idx]
                st.session_state["paper_history"] = history_list
                save_persistent_history(history_list)
                st.toast("Paper removed from history", icon="🗑️")
                st.rerun()
                
        if st.button("Clear All History", use_container_width=True):
            st.session_state["paper_history"] = []
            save_persistent_history([])
            st.toast("Cleared all paper history", icon="🗑️")
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 🚀 About")
    st.caption("This application utilizes Google's **Gemini 3.7 Flash** to parse and analyze complex research documents, extracting key mathematical foundations, quantitative metrics, and structured claims.")

# Main content: Input Section
tab_upload, tab_arxiv, tab_text = st.tabs([
    "📂 Upload PDF Document", 
    "🔗 Fetch ArXiv Paper", 
    "✍️ Paste Paper Content"
])

paper_text = ""
paper_metadata = {}

with tab_upload:
    uploaded_pdf = st.file_uploader("Upload PDF file", type=["pdf"], help="Upload the full PDF of your research paper.")
    if uploaded_pdf is not None:
        with st.spinner("Extracting text from PDF..."):
            extracted_text = extract_text_from_pdf(uploaded_pdf)
            if extracted_text:
                paper_text = extracted_text
                paper_metadata["title"] = uploaded_pdf.name
                st.success(f"Successfully loaded and parsed {len(extracted_text.split())} words from {uploaded_pdf.name}.")

with tab_arxiv:
    arxiv_url_id = st.text_input("arXiv Paper URL or ID", placeholder="e.g. 1706.03762 or https://arxiv.org/abs/2305.18290")
    if st.button("Fetch and Parse Paper"):
        if arxiv_url_id:
            with st.spinner("Fetching paper details from ArXiv..."):
                details = fetch_arxiv_data(arxiv_url_id)
                if details:
                    st.session_state["arxiv_details"] = details
                    st.success(f"Loaded: **{details['title']}**")
        else:
            st.warning("Please enter a valid arXiv URL or ID first.")
            
    if "arxiv_details" in st.session_state:
        det = st.session_state["arxiv_details"]
        st.markdown(f"**Title**: {det['title']}")
        st.markdown(f"**Authors**: {', '.join(det['authors'])}")
        st.markdown(f"**Year**: {det['year']}")
        st.markdown(f"**Abstract Preview**: {det['abstract'][:350]}...")
        paper_text = f"Title: {det['title']}\nAuthors: {', '.join(det['authors'])}\nYear: {det['year']}\n\nAbstract:\n{det['abstract']}"
        paper_metadata = {
            "title": det["title"],
            "authors": det["authors"],
            "year": det["year"],
            "venueOrArxiv": f"arXiv:{det['arxivId']}"
        }

with tab_text:
    pasted_input = st.text_area("Paste paper full-text or abstract", height=250, placeholder="Paste the text content here...")
    if pasted_input:
        paper_text = pasted_input
        paper_metadata["title"] = "Pasted Text Analysis"

# Execute Summarization Button
st.markdown("---")
summarize_col1, summarize_col2 = st.columns([1, 4])
with summarize_col1:
    trigger_summary = st.button("🚀 Generate AI Summary", type="primary", use_container_width=True)

# Main action execution
if trigger_summary:
    if not api_key:
        st.error("⚠️ Gemini API Key not found. Please input your Gemini API Key in the sidebar or set it in your environment/`.env` file.")
    elif not paper_text:
        st.warning("⚠️ No paper content detected. Please upload a PDF, fetch an arXiv paper, or paste text to summarize.")
    else:
        # Initialize Gemini Client
        client = init_gemini_client(api_key)
        if client:
            with st.spinner("Analyzing research paper and generating synthesis..."):
                # Configure prompts based on user choices
                mode_label, mode_val = summary_mode
                audience_label, audience_val = target_audience
                
                mode_instructions = {
                    "standard": "Provide a balanced, high-fidelity academic breakdown with executive takeaways and structured deep-dive sections.",
                    "deep_dive": "Provide an exhaustive, highly detailed academic deep dive covering background, mathematical formulas, ablation results, and technical nuances.",
                    "critical_review": "Act as a critical peer reviewer. Rigorously scrutinize the methodology, compute constraints, sample sizes, baselines, and overall validity of the paper's claims.",
                    "eli5": "Explain Like I'm 5 (ELI5). Use clear, everyday analogies and metaphors. Avoid impenetrable academic jargon and explain why this matters in simple human terms.",
                    "methodology_focus": "Deep Engineering and Algorithmic Focus. Focus heavily on equations, architectures, algorithms, hyperparameters, training objectives, and hardware configurations."
                }
                
                system_instruction = f"""You are a world-class AI research scientist, peer reviewer, and academic synthesizer.
Your task is to analyze the provided research paper (via PDF text or abstract) and generate a pristine, exhaustive, and structured summary.

Tone & Perspective: {mode_instructions[mode_val]}
Target Audience: {audience_label}
{f"Special Focus Area: {custom_focus}" if custom_focus else ""}

Return a strictly valid JSON response adhering to the exact schema requested. Do not wrap in markdown blocks, output raw JSON."""

                prompt = f"""Analyze the research paper provided and produce a thorough, high-quality structured summary in JSON format:
{f"Paper Metadata: {json.dumps(paper_metadata)}" if paper_metadata else ""}

Paper Content / Extract (up to 70k characters):
{paper_text[:70000]}

Ensure:
1. Accurate paper metadata (title, authors array, publication year, venue/arxiv if found).
2. 'tldr': A crisp 2-3 sentence executive synopsis.
3. 'problemStatement': Exactly what bottleneck or gap in literature this paper addresses.
4. 'coreContribution': What the authors introduced that is novel.
5. 'methodology': An overview, keyTechniques array, and architectureOrWorkflow explanation.
6. 'resultsAndFindings': Summary, keyMetrics list (with metric name, score, baseline comparison), and detailed findings (claim, evidence, significance).
7. 'limitations': List of real limitations, edge cases, or compute costs acknowledged or evident.
8. 'practicalImplications': How practitioners or industry can apply this.
9. 'futureDirections': Promising next steps.
10. 'keyConcepts': Array of key specialized terms with beginner-friendly explanations and category tags.
11. 'bibtex', 'apaCitation', 'ieeeCitation': Generated academic citations.
"""
                # JSON Schema for validation
                schema_definition = {
                    "type": types.Type.OBJECT,
                    "properties": {
                        "title": {"type": types.Type.STRING, "description": "Paper title"},
                        "authors": {
                            "type": types.Type.ARRAY,
                            "items": {"type": types.Type.STRING},
                            "description": "List of authors",
                        },
                        "year": {"type": types.Type.STRING, "description": "Publication year"},
                        "venueOrArxiv": {"type": types.Type.STRING, "description": "Venue, journal, or ArXiv ID"},
                        "tldr": {"type": types.Type.STRING, "description": "2-3 sentence executive summary"},
                        "problemStatement": {"type": types.Type.STRING, "description": "The core research problem and motivation"},
                        "coreContribution": {"type": types.Type.STRING, "description": "The novel innovation introduced"},
                        "methodology": {
                            "type": types.Type.OBJECT,
                            "properties": {
                                "overview": {"type": types.Type.STRING},
                                "keyTechniques": {"type": types.Type.ARRAY, "items": {"type": types.Type.STRING}},
                                "architectureOrWorkflow": {"type": types.Type.STRING},
                            },
                            "required": ["overview", "keyTechniques"],
                        },
                        "resultsAndFindings": {
                            "type": types.Type.OBJECT,
                            "properties": {
                                "summary": {"type": types.Type.STRING},
                                "keyMetrics": {
                                    "type": types.Type.ARRAY,
                                    "items": {
                                        "type": types.Type.OBJECT,
                                        "properties": {
                                            "metric": {"type": types.Type.STRING},
                                            "score": {"type": types.Type.STRING},
                                            "baselineOrComparison": {"type": types.Type.STRING},
                                        },
                                        "required": ["metric", "score"],
                                    },
                                },
                                "findings": {
                                    "type": types.Type.ARRAY,
                                    "items": {
                                        "type": types.Type.OBJECT,
                                        "properties": {
                                            "claim": {"type": types.Type.STRING},
                                            "evidence": {"type": types.Type.STRING},
                                            "significance": {"type": types.Type.STRING},
                                        },
                                        "required": ["claim", "evidence", "significance"],
                                    },
                                },
                            },
                            "required": ["summary", "keyMetrics", "findings"],
                        },
                        "limitations": {"type": types.Type.ARRAY, "items": {"type": types.Type.STRING}},
                        "practicalImplications": {"type": types.Type.ARRAY, "items": {"type": types.Type.STRING}},
                        "futureDirections": {"type": types.Type.ARRAY, "items": {"type": types.Type.STRING}},
                        "keyConcepts": {
                            "type": types.Type.ARRAY,
                            "items": {
                                "type": types.Type.OBJECT,
                                "properties": {
                                    "name": {"type": types.Type.STRING},
                                    "explanation": {"type": types.Type.STRING},
                                    "category": {"type": types.Type.STRING},
                                },
                                "required": ["name", "explanation", "category"],
                            },
                        },
                        "bibtex": {"type": types.Type.STRING, "description": "BibTeX citation entry"},
                        "apaCitation": {"type": types.Type.STRING, "description": "APA formatted citation"},
                        "ieeeCitation": {"type": types.Type.STRING, "description": "IEEE formatted citation"},
                    },
                    "required": [
                        "title",
                        "authors",
                        "tldr",
                        "problemStatement",
                        "coreContribution",
                        "methodology",
                        "resultsAndFindings",
                        "limitations",
                        "practicalImplications",
                        "futureDirections",
                        "keyConcepts",
                        "bibtex",
                    ],
                }

                try:
                    config = types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=schema_definition
                    )
                    response, used_model = generate_content_with_fallback(client, prompt, config)
                    
                    # Parse output JSON
                    json_data = json.loads(response.text)
                    st.session_state["summary_data"] = json_data
                    st.session_state["full_paper_text"] = paper_text
                    st.session_state["chat_history"] = [] # Reset chat history for new paper

                    # Save to paper history
                    paper_title = json_data.get("title") or paper_metadata.get("title") or "Untitled Paper"
                    new_entry = {
                        "title": paper_title,
                        "timestamp": datetime.now().strftime("%b %d, %H:%M"),
                        "source": paper_metadata.get("title", "Uploaded Document"),
                        "summary_data": json_data,
                        "full_paper_text": paper_text,
                        "chat_history": []
                    }
                    existing_hist = [p for p in st.session_state.get("paper_history", []) if p.get("title") != paper_title]
                    existing_hist.insert(0, new_entry)
                    st.session_state["paper_history"] = existing_hist
                    save_persistent_history(existing_hist)

                    st.success(f"✨ Analysis synthesis generated successfully using {used_model}!")
                except Exception as ex:
                    st.error(f"Error communicating with Gemini: {ex}")
                    # Attempt printing raw response for diagnostics if possible
                    if 'response' in locals() and hasattr(response, 'text'):
                        st.text_area("Raw Response Diagnostics", value=response.text, height=200)

# Display Results & Interactive Panels
if "summary_data" in st.session_state:
    data = st.session_state["summary_data"]
    
    st.markdown("---")
    
    # Header paper details
    st.markdown(f"## 📄 {data.get('title', 'Unknown Title')}")
    authors_str = ", ".join(data.get("authors", []))
    year_str = data.get("year", "")
    venue_str = data.get("venueOrArxiv", "")
    metadata_sub = f"**Authors**: {authors_str}"
    if year_str:
        metadata_sub += f" | **Year**: {year_str}"
    if venue_str:
        metadata_sub += f" | **Venue/ID**: {venue_str}"
    st.markdown(metadata_sub)
    
    # Executive TL;DR Highlight Card
    st.markdown(f"""
    <div class="tldr-card">
        <div class="tldr-title">⚡ 1-Minute Executive TL;DR Summary</div>
        <div class="tldr-content">{data.get('tldr', 'No TL;DR summary available.')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabbed detailed results
    tab_synth, tab_meth, tab_res, tab_lim_fut, tab_concepts, tab_cit = st.tabs([
        "🎯 Key Synthesis",
        "⚙️ Methodology",
        "📊 Results & Findings",
        "⚠️ Limitations & Future",
        "💡 Implications & Concepts",
        "📖 Citations & References"
    ])
    
    with tab_synth:
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">Research Question & Motivation</div>
            <div class="card-content">{data.get("problemStatement", "N/A")}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">Core Contribution & Novelty</div>
            <div class="card-content">{data.get("coreContribution", "N/A")}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with tab_meth:
        meth_data = data.get("methodology", {})
        
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">Methodology Overview</div>
            <div class="card-content">{meth_data.get("overview", "N/A")}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">Workflow / Architecture Details</div>
            <div class="card-content">{meth_data.get("architectureOrWorkflow", "N/A")}</div>
        </div>
        """, unsafe_allow_html=True)
        
        techniques_list = "".join([f"<li><b>{tech}</b></li>" for tech in meth_data.get("keyTechniques", [])])
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">Key Techniques & Algorithms</div>
            <div class="card-content">
                <ul>{techniques_list if techniques_list else "<li>N/A</li>"}</ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with tab_res:
        res_data = data.get("resultsAndFindings", {})
        
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">Results Overview</div>
            <div class="card-content">{res_data.get("summary", "N/A")}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quantitative Metric Badges
        metrics_list = res_data.get("keyMetrics", [])
        if metrics_list:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Quantitative Benchmarks & Metrics</div>', unsafe_allow_html=True)
            
            metric_cols = st.columns(min(len(metrics_list), 4))
            for idx, item in enumerate(metrics_list):
                col_idx = idx % 4
                with metric_cols[col_idx]:
                    st.metric(
                        label=item.get("metric", "Metric"), 
                        value=item.get("score", "N/A"),
                        delta=item.get("baselineOrComparison", None)
                    )
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Qualitative Claims & Findings
        findings_list = res_data.get("findings", [])
        if findings_list:
            findings_html = ""
            for item in findings_list:
                findings_html += f"""
                <div style="margin-bottom: 1rem; border-bottom: 1px dashed var(--card-border); padding-bottom: 0.8rem;">
                    <div style="font-weight: 700; color: var(--title-color); font-size: 1.1rem; margin-bottom: 0.3rem;">🔍 Claim: {item.get('claim', 'Claim Details')}</div>
                    <div><b>Evidence</b>: {item.get('evidence', 'Evidence Details')}</div>
                    <div><b>Significance</b>: {item.get('significance', 'Significance Details')}</div>
                </div>
                """
            st.markdown(f"""
            <div class="section-card">
                <div class="section-title">Key Scientific Findings</div>
                <div class="card-content">{findings_html}</div>
            </div>
            """, unsafe_allow_html=True)

    with tab_lim_fut:
        limitations_list = "".join([f"<li>{lim}</li>" for lim in data.get("limitations", [])])
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">⚠️ Limitations & Vulnerabilities</div>
            <div class="card-content">
                <ul>{limitations_list if limitations_list else "<li>N/A</li>"}</ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        directions_list = "".join([f"<li>{direction}</li>" for direction in data.get("futureDirections", [])])
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">🚀 Future Research Directions</div>
            <div class="card-content">
                <ul>{directions_list if directions_list else "<li>N/A</li>"}</ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with tab_concepts:
        implications_list = "".join([f"<li>{imp}</li>" for imp in data.get("practicalImplications", [])])
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">💡 Industry & Practical Applications</div>
            <div class="card-content">
                <ul>{implications_list if implications_list else "<li>N/A</li>"}</ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🔑 Core Concepts & Definitions</div>', unsafe_allow_html=True)
        for concept in data.get("keyConcepts", []):
            with st.expander(f"📚 {concept.get('name')} ({concept.get('category', 'General')})"):
                st.write(concept.get("explanation", "N/A"))
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab_cit:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Academic Citations</div>', unsafe_allow_html=True)
        
        st.markdown("#### BibTeX")
        st.code(data.get("bibtex", "@article{...}"), language="latex")
        
        st.markdown("#### APA Style")
        st.code(data.get("apaCitation", "APA Citation Details"), language="text")
        
        st.markdown("#### IEEE Style")
        st.code(data.get("ieeeCitation", "IEEE Citation Details"), language="text")
        st.markdown('</div>', unsafe_allow_html=True)

    # Multi-turn Interactive Q&A chat
    st.markdown("---")
    st.markdown("### 💬 Chat with the Research Assistant")
    st.caption("Ask questions about the paper's benchmarks, math models, ablation studies, or general claims. The assistant references the full paper content.")

    # Show previous messages
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt_input := st.chat_input("Ask a question about the paper..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt_input)
        st.session_state["chat_history"].append({"role": "user", "content": prompt_input})
        
        # Display assistant message spinner
        with st.chat_message("assistant"):
            with st.spinner("Synthesizing response from paper..."):
                client = init_gemini_client(api_key)
                if client:
                    chat_system_instruction = f"""You are an expert scientific researcher helping a user understand a specific research paper.
Answer the user's question accurately, citing evidence from the paper context where available.
If the answer is not explicitly stated in the paper, clearly state that while offering sound domain knowledge if relevant.
Keep answers structured, insightful, and concise.

Paper Context:
{json.dumps(data)}
"""
                    # Prepare history context for multi-turn conversation
                    contents = []
                    # We limit context history length to prevent token bloat
                    for h_msg in st.session_state["chat_history"][-6:-1]:
                        role = "model" if h_msg["role"] == "assistant" else "user"
                        contents.append({"role": role, "parts": [{"text": h_msg["content"]}]})
                    
                    # Add current user prompt
                    contents.append({"role": "user", "parts": [{"text": prompt_input}]})
                    
                    try:
                        config = types.GenerateContentConfig(
                            system_instruction=chat_system_instruction
                        )
                        response_chat, used_model = generate_content_with_fallback(client, contents, config)
                        answer = response_chat.text
                        st.markdown(answer)
                        st.session_state["chat_history"].append({"role": "assistant", "content": answer})
                        
                        # Sync chat history to persistent paper history
                        if "summary_data" in st.session_state:
                            cur_title = st.session_state["summary_data"].get("title")
                            for p in st.session_state.get("paper_history", []):
                                if p.get("title") == cur_title:
                                    p["chat_history"] = st.session_state["chat_history"]
                                    save_persistent_history(st.session_state["paper_history"])
                                    break
                    except Exception as err:
                        st.error(f"Chat error: {err}")
                else:
                    st.error("Gemini API key is required to use the chat assistant.")
        st.rerun()
