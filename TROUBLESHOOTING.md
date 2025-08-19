# 🛠️ Troubleshooting and Maintenance Guide

This guide provides solutions to common issues you may encounter when using the **AI Report Generator**, along with best practices for keeping the project healthy and up to date.

---

## ⚡ Troubleshooting Common Issues

### 1. API Key Not Found or Invalid
**Issue:** You see an `AuthenticationError` or a similar message.  
**Cause:** The `GOOGLE_API_KEY` in your `.env` file is missing, misspelled, or expired.  
**Solution:**
- Ensure the `.env` file is in the project’s root directory.  
- Verify the variable name is exactly `GOOGLE_API_KEY`.  
- Check the Google Cloud console to confirm the key is active and has Gemini API permissions.  

---

### 2. Dependencies Not Installed
**Issue:** The app fails to start with `ImportError`.  
**Cause:** Required Python packages are missing.  
**Solution:**
```bash
pip install -r requirements.txt
```

### 3. Report Generation Takes Too Long
**Issue:** Report generation is very slow.  
**Causes:** Large datasets, high model latency, or network issues.  
**Solutions:**  
- For very large CSVs, sample a smaller, representative subset.  
- Use a smaller, faster model for simple tasks.  
- Check your internet connection.  

---

### 4. Inaccurate Information in Reports
**Issue:** Generated reports contain errors or “hallucinations.”  
**Cause:** LLMs may produce inaccurate or fabricated content.  
**Solutions:**  
- **Manual Review:** Always verify generated content before use.  
- **Prompt Engineering:** Refine agent prompts to be clearer and more specific.  
- **Add Context:** Provide more domain-specific reference data to reduce reliance on generalized knowledge.  

---

## 🛡️ Project Maintenance Guide

### 1. Updating Dependencies
Regularly update dependencies to benefit from new features and security patches.  
```bash
pip install --upgrade -r requirements.txt
```

### 2. Contributing to the Project
To contribute:  
1. **Fork** the repository and clone it locally.  
2. **Create a new branch** for your feature or bug fix.  
3. **Implement your changes** and add tests to cover new code.  
4. **Run the full test suite** to ensure no regressions:  
   ```bash
   PYTHONPATH=./src pytest
   ```
5. Commit your changes with a clear, descriptive message.
6. Push your branch to your forked repository.
7. Open a Pull Request (PR) against the main repository.
