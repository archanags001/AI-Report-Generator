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
