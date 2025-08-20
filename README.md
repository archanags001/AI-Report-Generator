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
## Architecture

Our **AI Data Analyst & Report Generator** is built upon a robust and modular multi-agent architecture, with **LangGraph** serving as the central orchestration framework. This design fosters a highly extensible and maintainable system where specialized AI agents autonomously collaborate to accomplish the intricate task of end-to-end report generation.

### Core Architectural Components

- **GraphState**  
  The central, shared state object acting as the single source of truth for the entire workflow. It carries all relevant data, user instructions, intermediate analytical results, generated artifacts (like charts), and status updates across all agents, ensuring seamless information flow and consistent context.

- **Agent Nodes**  
  Each stage of the data analysis and reporting process is encapsulated within a dedicated AI agent, implemented as a node within the LangGraph workflow. Every node has a clearly defined responsibility, promoting separation of concerns.

- **Directed Edges**  
  LangGraph defines the flow of information and control between agent nodes via directed edges. These ensure a logical progression through the analytical pipeline.

- **Conditional Edges**  
  Conditional edges enable dynamic decision-making. For example, the system can decide whether to generate visualizations or proceed directly to insight extraction, depending on the analysis plan.


---

## Agent Roles and Responsibilities

Each agent in the LangGraph workflow plays a distinct role in automating the report generation process.

---

### 📊 Data Profiling Agent

- **Role**: Initial data ingestion, cleaning, and profiling.
- **Responsibilities**:
  - Reads CSV data.
  - Identifies data types.
  - Calculates descriptive statistics (mean, median, std, unique counts, missing values).
  - Flags potential data quality issues.
- **Output**: `DataProfile` object containing metadata and initial observations.

---

### 🧠 Analysis Planning Agent

- **Role**: Formulates a strategic analysis and visualization plan.
- **Responsibilities**:
  - Interprets the `DataProfile` and user instructions.
  - Determines analytical approaches.
  - Identifies key relationships.
  - Specifies required visualizations (chart types, axes, titles).
- **Output**: 
  - List of `VisualGenerationInstruction` objects.
  - A high-level `analysis_approach` string.

---

### 📈 Visual Generation Agent

- **Role**: Creates data visualizations based on the analysis plan.
- **Responsibilities**:
  - Uses Pandas, Matplotlib, and Seaborn to generate charts (bar, line, scatter, histogram, boxplot).
  - Saves charts as PNG files.
- **Output**: List of `GeneratedVisual` objects containing file paths and descriptions.

---

### 🔍 Insight Extraction Agent

- **Role**: Extracts meaningful insights and conclusions.
- **Responsibilities**:
  - Analyzes `DataProfile`, visuals, and user instructions.
  - Identifies trends, anomalies, and key findings.
- **Output**: List of `AnalysisInsight` objects with titles, narratives, and figure references.

---

### 📝 Report Drafting Agent

- **Role**: Drafts the structured text of the report.
- **Responsibilities**:
  - Writes an introduction and insight narratives.
  - References visuals using placeholders (e.g., `[FIGURE X]`).
  - Summarizes key takeaways and adds a conclusion.
- **Output**: `ReportSectionsDraft` object with all textual components.

---

### 📄 Report Finalization Agent

- **Role**: Compiles the final report into publishable formats.
- **Responsibilities**:
  - Replaces figure placeholders with actual numbers.
  - Embeds chart images.
  - Compiles the report into:
    - Markdown
    - HTML
    - PDF
- **Output**: `ReportFormat` object with file paths to `.md`, `.html`, and `.pdf` versions.

___

## Workflow Diagram

The following diagram illustrates the flow of data and the interaction between the different agents within the system:

```
graph TD
    A[User Uploads CSV] --> B(Data Ingestion Agent);
    B --> C{Data Validation & Cleaning};
    C -->|Invalid Data & Instructions| I(Notify User of Errors);
    C -->|Valid Data & Instructions| D(Data Analysis Agent);
    D --> E(Visualization Agent);
    E --> F(Report Drafting Agent);
    F --> G(Safety and Accuracy Check);
    G --> |If Pass| H[Downloadable PDF Report];
    G --> |If Fail & Retries Remaining| F;
    G --> |If Fail & No Retries| J(Notify User of Errors);
    I --> A;
    J --> A;

```

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
<img src="https://raw.githubusercontent.com/archanags001/AI-Report-Generator/main/images/improved_architecture.png" alt="architecture report gen" width="700">


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
├── packages.txt
├── src/ # Source code directory for the core logic.
│   ├── init.py # Initializes the Python package.
│   ├── agents/ # Contains individual AI agent nodes.
│   │   ├── data_analysis_node.py # Handles initial data profiling.
│   │   ├── analysis_planning_node.py # Plans the analytical steps.
│   │   ├── visual_generation_node.py # Generates data visualizations.
│   │   ├── insight_extraction_node.py # Extracts key insights from data and visuals.
│   │   ├── report_drafting_node.py # Drafts the textual content of the report.
│   │   ├── safety_node.py # Check the safety of darafts
│   │   └── report_finalization_node.py # Assembles and finalizes the report in PDF format.
│   ├── graph/ # Defines the LangGraph workflow and shared state.
│   │   ├── init.py
│   │   ├── graph.py # Defines the main LangGraph workflow definition.
│   │   └── state.py # Defines the GraphState TypedDict, the shared state object.
│   ├── schemas/ # Pydantic models for structured data and LLM output.
│   │     └── messages.py # Data structures used across agents.
│   └── streamlit_app.py
├── tests
│    ├── test_data_analysis_node.py # Tests the individual agent nodes.
│    ├── test_analysis_planning_node.py 
│    ├── test_visual_generation_node.py 
│    ├── test_insight_extraction_node.py 
│    ├── test_report_drafting_node.py
│    ├── test_safety_node.py
│    ├── test_report_finalization_node.py
│    ├── test_builder.py
│    ├── test_integration.py
│    ├── test_e2e_workflow.py
│    └── health_check.py
│        
│
└── images
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
4. Run the AI Data Analyst & Report Generator

1. Open your terminal
2. Run this command:
 `streamlit run src/streamlit_app.py`
This command will open the **AI Data Analyst & Report Generator** in your default web browser at [http://localhost:8501](http://localhost:8501)
3. Upload Your Data:
In the Streamlit interface, use the file uploader to select your CSV file.

4. Provide Instructions:
In the text area, enter clear instructions on what you want to analyze or find in

---

## Running Tests

To ensure the project is working as expected and to verify any changes you make, you can run the test suite. This section provides instructions on how to execute tests and view coverage reports.

To run the entire test suite, use the following command from the root directory of the project:

```
PYTHONPATH=./src pytest
```

The PYTHONPATH=./src part of this command temporarily adds the project's src directory to Python's import path. This ensures that the test runner can correctly find and import the source code modules it needs to test.

Running Specific Tests

If you are working on a particular feature or bug and only want to run a specific test file, you can do so by providing the file path:

```
PYTHONPATH=./src pytest path/to/your/test-file.py
```

___

Here's a quick example 

<img src="https://github.com/archanags001/AI-Report-Generator/blob/48a61d00c5fccaaa0ed53233db8d45c5add79be8/images/report_ai_generated.png" alt="report gen" width="700">



## License

This project is licensed under the MIT License – see the [LICENSE](https://github.com/archanags001/AI-Report-Generator/blob/main/License) file for details.

## Contact
archanags001@gmail.com






