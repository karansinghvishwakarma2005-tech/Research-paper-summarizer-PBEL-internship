# 🎓 AI Research Paper Summarizer & Intelligence Assistant

> **PBEL Internship Project** | **Generative AI (Gen AI) Course**

An advanced, interactive academic dashboard and AI research assistant that leverages Google's **Gemini 3.7 Flash** to synthesize, analyze, and query scientific literature from PDF documents, ArXiv paper links, or raw text.

---

## 🌟 Project Overview

Developed as part of the **PBEL Internship** under the **Generative AI (Gen AI)** course curriculum, this project provides researchers, students, and practitioners with an automated tool to parse complex scientific papers, extract structured insights, generate benchmark comparisons, and perform interactive multi-turn Q&A.

---

## 🛠️ Key Technologies

- **Language**: Python 3.10+
- **Framework**: [Streamlit](https://streamlit.io/) (Interactive Web Dashboard & Multi-Turn Chat UI)
- **Generative AI Model**: Google Gemini API via `google-genai` SDK (`gemini-3.7-flash` with automatic fallback to `gemini-3.6-flash`)
- **Document Processing**: `pypdf` for PDF text extraction & `xml.etree.ElementTree` for ArXiv REST API metadata fetching
- **Environment & Dependency Manager**: `uv` & `python-dotenv`

---

## ✨ Features

- **📄 Multi-Source Paper Ingestion**: Upload PDF research papers, fetch directly via ArXiv URL/ID (e.g. `1706.03762`), or paste raw paper text.
- **🎯 Multi-Level Analysis Modes**:
  - *Standard Academic Breakdown*
  - *Deep Dive & Mathematical Foundations*
  - *Critical Peer Reviewer Critique*
  - *ELI5 (Explain Like I'm 5)*
  - *Methodology & Algorithmic Focus*
- **👥 Audience Tailoring**: Customizes output depth for Researchers, Students, Industry Practitioners, or Executives.
- **📊 Structured Scientific Extraction**:
  - 1-Minute Executive TL;DR
  - Problem Statement & Core Novelty
  - Detailed Methodology & Key Algorithms
  - Quantitative Benchmark Metrics & Findings
  - Limitations & Future Research Directions
  - Industry Applications & Core Concept Definitions
- **📖 Academic Citations Generator**: Automatic BibTeX, APA, and IEEE style citations.
- **📜 Paper History Management**: Automatically saves analyzed papers locally (`paper_history.json`) with instant 1-click restoration of summaries and chat logs.
- **💬 Interactive Chat Assistant**: Multi-turn Q&A chat grounded directly in the paper's full content.
- **🔒 Environment & API Security**: Complete masking of API keys from the UI and automatic `.gitignore` protection.

---

## 🚀 Quick Setup & Execution

### 1. Prerequisites
Ensure you have Python 3.10+ and [uv](https://github.com/astral-sh/uv) installed.

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```bash
GEMINI_API_KEY="your_google_gemini_api_key_here"
```

### 3. Run the Application
To automatically set up the virtual environment, install dependencies, and launch the Streamlit dashboard:

```bash
uv run streamlit run app.py
```

*(Alternatively, with standard Python pip)*:
```bash
pip install -r requirements.txt
streamlit run app.py
```

### 4. Access the Dashboard
Open your browser and navigate to:
```
http://localhost:8501
```

---

## 📁 Repository Structure

```
├── app.py                  # Main Streamlit Application Logic
├── requirements.txt        # Python Dependencies List
├── .env.example            # Environment Variable Template
├── .gitignore              # Git Exclusion Rules (Protects secrets & cache)
└── README.md               # Project Documentation
```

---

## 🎓 Internship & Course Attribution
- **Program**: PBEL Internship
- **Domain**: Generative AI (Gen AI) Course
- **Repository**: [Research-paper-summarizer-PBEL-internship](https://github.com/karansinghvishwakarma2005-tech/Research-paper-summarizer-PBEL-internship)
