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
<img src="https://github.com/archanags001/AI-Report-Generator/blob/e442097159d8e8aa5a667f320333ea3d4df1b00d/images/architecture_report_gen.png" alt="architecture report gen" width="700">


---

## 🧰 Technologies Used

- **Frontend Interface**: [Streamlit](https://streamlit.io/)
- **AI Orchestration**: [LangGraph](https://www.langgraph.dev/)
- **Data Manipulation**: [Pandas](https://pandas.pydata.org/)
- **Data Visualization**: [Matplotlib](https://matplotlib.org/) & [Seaborn](https://seaborn.pydata.org/)
- **LLM**: Google Gemini 2.5 Flash (via `langchain-google-genai`)
- **PDF Generation**: [WeasyPrint](https://weasyprint.org/)


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

---

Here's a quick example 

<img src="https://github.com/archanags001/AI-Report-Generator/blob/48a61d00c5fccaaa0ed53233db8d45c5add79be8/images/report_ai_generated.png" alt="report gen" width="700">



## License

This project is licensed under the MIT License – see the [LICENSE](https://github.com/archanags001/streamlit-ai-guide/blob/main/LICENSE) file for details.

## Contact
archanags001@gmail.com






