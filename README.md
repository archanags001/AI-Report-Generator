# 🧠 AI Data Analyst & Report Generator

Welcome to **AI Data Analyst & Report Generator** — an intelligent system that helps you analyze data and create reports easily.

This project offers an AI-powered way to automate the entire process of transforming raw data into clear, professional reports, complete with visualizations and key insights. It significantly reduces manual effort and time, allowing users to quickly derive actionable value from their data and focus on strategic decision-making.

---

## 💬 Example Instructions You Can Provide

- "Analyze sales trends for the last quarter."
- "Summarize customer demographics and buying patterns."
- "Find out why our website traffic dropped last month."
- "Generate a comprehensive report on product performance."

Let’s make data analysis simple and direct!

---

## ✨ Features

- **Intelligent Instruction Validation**: Validates user instructions and provides polite feedback if they're out of scope.
- **Automated Data Profiling**: Automatically profiles uploaded CSVs, showing column types, value counts, and descriptive stats.
- **Intelligent Visualization Generation**: Suggests and creates charts (bar, line, scatter, histogram, box) tailored to the analysis.
- **Insight Extraction**: Highlights key trends, patterns, and actionable insights using AI-driven logic.
- **Automated Report Drafting**: Generates structured reports with sections like Introduction, Analysis, Key Takeaways, and Conclusion.
- **PDF Report Export**: Finalized reports are exported as high-quality PDF documents for sharing.
- **User-Friendly Interface**: Built with Streamlit for an interactive and intuitive web experience.
- **Multi-Agent Orchestration**: Each task is handled by a dedicated AI agent using LangGraph for modularity and efficiency.

---

This architecture promotes clarity and simplifies debugging. It also provides a flexible foundation for future enhancements, allowing for the addition or modification of individual agents without needing a complete overhaul of the system.

```html
<svg width="100%" height="850" viewBox="0 0 1200 850" xmlns="http://www.w3.org/2000/svg" font-family="Arial, sans-serif">
  <defs>
    <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
      <feOffset result="offOut" in="SourceAlpha" dx="4" dy="4" />
      <feGaussianBlur result="blurOut" in="offOut" stdDeviation="4" />
      <feBlend in="SourceGraphic" in2="blurOut" mode="normal" />
    </filter>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="8" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#34495E" />
    </marker>
  </defs>

  <!-- Title -->
  <text x="600" y="50" text-anchor="middle" font-size="36" font-weight="bold" fill="#2C3E50">AI Report Generator: System Architecture</text>

  <!-- User Input -->
  <rect x="100" y="100" width="200" height="80" rx="10" ry="10" fill="#ECF0F1" stroke="#3498DB" stroke-width="2" filter="url(#shadow)"/>
  <text x="200" y="140" text-anchor="middle" font-size="18" fill="#2C3E50">User Input</text>
  <text x="200" y="160" text-anchor="middle" font-size="14" fill="#2C3E50">(CSV, Instructions)</text>

  <!-- LangGraph Orchestration (Central Hub) -->
  <rect x="400" y="100" width="400" height="120" rx="15" ry="15" fill="#A7D9F2" stroke="#3498DB" stroke-width="3" filter="url(#shadow)"/>
  <text x="600" y="145" text-anchor="middle" font-size="28" font-weight="bold" fill="#2C3E50">LangGraph Orchestration</text>
  <text x="600" y="175" text-anchor="middle" font-size="18" fill="#2C3E50">(Agent Coordinator)</text>

  <!-- Arrows: User Input -> LangGraph -->
  <line x1="300" y1="140" x2="400" y2="140" stroke="#3498DB" stroke-width="2" marker-end="url(#arrowhead)" />
  <text x="350" y="130" text-anchor="middle" font-size="14" fill="#2C3E50">Initiate Analysis</text>

  <!-- Agent Workflow Pipeline -->
  <g filter="url(#shadow)">
    <!-- Data Profiling Agent -->
    <rect x="100" y="300" width="200" height="70" rx="8" ry="8" fill="#D4EDDA" stroke="#28A745" stroke-width="1.5"/>
    <text x="200" y="335" text-anchor="middle" font-size="16" fill="#216B30">Data Profiling</text>

    <!-- Analysis Planning Agent -->
    <rect x="350" y="300" width="200" height="70" rx="8" ry="8" fill="#FFF3CD" stroke="#FFC107" stroke-width="1.5"/>
    <text x="450" y="335" text-anchor="middle" font-size="16" fill="#A07200">Analysis Planning</text>

    <!-- Visual Generation Agent -->
    <rect x="600" y="300" width="200" height="70" rx="8" ry="8" fill="#F8D7DA" stroke="#DC3545" stroke-width="1.5"/>
    <text x="700" y="335" text-anchor="middle" font-size="16" fill="#8B0000">Visual Generation</text>

    <!-- Insight Extraction Agent -->
    <rect x="350" y="450" width="200" height="70" rx="8" ry="8" fill="#E0CCE9" stroke="#6F42C1" stroke-width="1.5"/>
    <text x="450" y="485" text-anchor="middle" font-size="16" fill="#4B0082">Insight Extraction</text>

    <!-- Report Drafting Agent -->
    <rect x="600" y="450" width="200" height="70" rx="8" ry="8" fill="#D1ECF1" stroke="#17A2B8" stroke-width="1.5"/>
    <text x="700" y="485" text-anchor="middle" font-size="16" fill="#0D6B7B">Report Drafting</text>

    <!-- Report Finalization Agent -->
    <rect x="600" y="600" width="250" height="80" rx="10" ry="10" fill="#D4EDDA" stroke="#28A745" stroke-width="2"/>
    <text x="720" y="640" text-anchor="middle" font-size="18" fill="#216B30">Report Finalization</text>
    <text x="720" y="660" text-anchor="middle" font-size="14" fill="#216B30">(PDF Only)</text>
  </g>

  <!-- Arrows: LangGraph -> First Agent (Conceptual Orchestration) -->
  <line x1="600" y1="220" x2="200" y2="300" stroke="#3498DB" stroke-width="2" marker-end="url(#arrowhead)" />
  <text x="400" y="260" text-anchor="middle" font-size="14" fill="#2C3E50">Orchestrates</text>
  <text x="400" y="280" text-anchor="middle" font-size="14" fill="#2C3E50">Workflow</text>


  <!-- Arrows between Agents (Conceptual Flow) -->
  <!-- Data Profiling -> Analysis Planning -->
  <line x1="300" y1="335" x2="350" y2="335" stroke="#3498DB" stroke-width="1.5" marker-end="url(#arrowhead)" />
  <text x="325" y="325" text-anchor="middle" font-size="12" fill="#2C3E50">Profiled Data</text>

  <!-- Analysis Planning -> Visual Generation -->
  <line x1="550" y1="335" x2="600" y2="335" stroke="#3498DB" stroke-width="1.5" marker-end="url(#arrowhead)" />
  <text x="575" y="325" text-anchor="middle" font-size="12" fill="#2C3E50">Planning Output</text>

  <!-- Analysis Planning -> Insight Extraction (Conditional Path: No Visuals Needed) -->
  <line x1="450" y1="370" x2="450" y2="450" stroke="#3498DB" stroke-width="2" marker-end="url(#arrowhead)" />
  <text x="460" y="410" text-anchor="start" font-size="12" fill="#2C3E50">No Visuals Needed</text>

  <!-- Visual Generation -> Insight Extraction -->
  <line x1="700" y1="370" x2="700" y2="450" stroke="#3498DB" stroke-width="2" marker-end="url(#arrowhead)" />
  <text x="710" y="410" text-anchor="start" font-size="12" fill="#2C3E50">Generated Visuals</text>

  <!-- Insight Extraction -> Report Drafting -->
  <line x1="550" y1="485" x2="600" y2="485" stroke="#3498DB" stroke-width="1.5" marker-end="url(#arrowhead)" />
  <text x="575" y="475" text-anchor="middle" font-size="12" fill="#2C3E50">Insights</text>

  <!-- Report Drafting -> Report Finalization -->
  <line x1="700" y1="520" x2="700" y2="600" stroke="#3498DB" stroke-width="1.5" marker-end="url(#arrowhead)" />
  <text x="710" y="550" text-anchor="start" font-size="12" fill="#2C3E50">Drafted Report</text>

  <!-- Final Report Output -->
  <rect x="600" y="750" width="250" height="80" rx="10" ry="10" fill="#E8F5E9" stroke="#66BB6A" stroke-width="2" filter="url(#shadow)"/>
  <text x="720" y="790" text-anchor="middle" font-size="20" font-weight="bold" fill="#2E7D32">Final Report Output</text>
  <text x="720" y="810" text-anchor="middle" font-size="16" fill="#2E7D32">(PDF Only)</text>
  <line x1="700" y1="680" x2="700" y2="750" stroke="#3498DB" stroke-width="1.5" marker-end="url(#arrowhead)" />

</svg>

---
## ⚙️ How It Works

The system operates through a sequential multi-agent pipeline managed by LangGraph:

1. **Instruction Validation**  
   Checks if the input is relevant to data analysis and provides immediate feedback.

2. **Data Loading & Profiling**  
   Loads uploaded CSV files into a Pandas DataFrame and generates a comprehensive profile.

3. **Analysis Planning**  
   Forms a strategy based on the data profile and the user’s instructions.

4. **Visualization Generation**  
   Dynamically selects and creates appropriate data visualizations.

5. **Insight Extraction**  
   Derives key findings and conclusions from the data and visualizations.

6. **Report Drafting**  
   Synthesizes all information into a cohesive, professional report.

7. **Report Finalization**  
   Converts the report into a downloadable PDF file.

---

## 🧰 Technologies Used

- **Frontend Interface**: [Streamlit](https://streamlit.io/)
- **AI Orchestration**: [LangGraph](https://www.langgraph.dev/)
- **Data Manipulation**: [Pandas](https://pandas.pydata.org/)
- **Data Visualization**: [Matplotlib](https://matplotlib.org/) & [Seaborn](https://seaborn.pydata.org/)
- **LLM**: Google Gemini 2.5 Flash (via `langchain-google-genai`)
- **PDF Generation**: [WeasyPrint](https://weasyprint.org/)
- **Environment Management**: [`python-dotenv`](https://pypi.org/project/python-dotenv/)

---
## 🗂 Project Structure
```
AI-Report-Generator/
├── .env # Environment variables (e.g., GOOGLE_API_KEY)
├── requirements.txt # Lists all Python dependencies required for the project.
└── src/ # Source code directory for the core logic.
├── init.py # Initializes the Python package.
├── agents/ # Contains individual AI agent nodes.
│ ├── data_analysis_node.py # Handles initial data profiling.
│ ├── analysis_planning_node.py # Plans the analytical steps.
│ ├── visual_generation_node.py # Generates data visualizations.
│ ├── insight_extraction_node.py # Extracts key insights from data and visuals.
│ ├── report_drafting_node.py # Drafts the textual content of the report.
│ └── report_finalization_node.py # Assembles and finalizes the report in PDF format.
├── graph/ # Defines the LangGraph workflow and shared state.
│ ├── init.py
│ ├── graph.py # Defines the main LangGraph workflow definition.
│ └── state.py # Defines the GraphState TypedDict, the shared state object.
└── schemas/ # Pydantic models for structured data and LLM output.
└── messages.py # Data structures used across agents.
├── streamlit_app.py 
```

---
---

## Installation & Setup
1. Clone the Repository
```
git clone https://github.com/your-username/AI-Report-Generator.git
cd AI-Report-Generator
```
2. Install Dependencies
Install all required Python packages from requirements.txt:
```
pip install -r requirements.txt
```
3.  Set Up Your Google Gemini API Key
Create a .env file in the root directory and add your API key:
```
GOOGLE_API_KEY="YOUR_GEMINI_API_KEY_HERE"
```
4. Run the Streamlit AI Guide

1. Open your terminal
2. Run this command:
 `streamlit run src/streamlit_app.py`
This command will open the **AI Data Analyst & Report Generator** in your default web browser at [http://localhost:8501](http://localhost:8501)
3. Upload Your Data:
In the Streamlit interface, use the file uploader to select your CSV file.

4. Provide Instructions:
In the text area, enter clear instructions on what you want to analyze or find in

