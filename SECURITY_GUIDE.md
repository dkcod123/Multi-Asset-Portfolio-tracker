# 🔒 Security Guide

## ⚠️ **CRITICAL: Never Commit API Keys to GitHub**

This guide ensures your API keys and sensitive data remain secure when sharing code on GitHub.

## 🛡️ **Security Best Practices**

### 1. **Environment Variables**
Always use environment variables for sensitive data:

```bash
# ✅ CORRECT - Use environment variables
FYERS_APP_ID=your_actual_key_here
FYERS_APP_SECRET=your_actual_secret_here

# ❌ WRONG - Never hardcode in source code
app_id = "your_actual_key_here"
```

### 2. **File Structure**
```
portfolio-tracker/
├── backend/
│   ├── .env              # ❌ NEVER commit this (contains real keys)
│   ├── env.example       # ✅ SAFE to commit (contains placeholders)
│   └── app.py
└── .gitignore            # ✅ Ensures .env files are ignored
```

### 3. **GitHub-Safe Files**

#### ✅ **Safe to Commit:**
- `env.example` - Template with placeholder values
- `README.md` - Documentation
- Source code files
- Configuration templates

#### ❌ **Never Commit:**
- `.env` files with real API keys
- `secrets.json`
- `credentials.json`
- Any file containing actual API keys

## 🔧 **Setup Instructions**

### Step 1: Create Environment File
```bash
# Copy the example file
cp backend/env.example backend/.env

# Edit with your real API keys
nano backend/.env
```

### Step 2: Get FYERS API Keys
1. Visit https://api.fyers.in/
2. Create a new app
3. Get your App ID and App Secret
4. Add them to your `.env` file

### Step 3: Verify .gitignore
Ensure `.gitignore` contains:
```gitignore
# Environment files
.env
backend/.env
*.env
```

## 🚨 **Security Checklist**

Before pushing to GitHub:

- [ ] `.env` file is in `.gitignore`
- [ ] No API keys in source code
- [ ] `env.example` has placeholder values
- [ ] README has setup instructions
- [ ] No credentials in commit history

## 🔍 **Verify Security**

### Check What Will Be Committed:
```bash
# See what files will be committed
git status

# Check if .env is being tracked
git ls-files | grep env

# Should return nothing for .env files
```

### Test Environment Loading:
```bash
# Test that your app loads environment variables
python -c "import os; print('FYERS_APP_ID:', os.getenv('FYERS_APP_ID'))"
```

## 🛠️ **Production Deployment**

### For Production Servers:
1. **Set environment variables directly:**
   ```bash
   export FYERS_APP_ID=your_production_key
   export FYERS_APP_SECRET=your_production_secret
   ```

2. **Use Docker secrets:**
   ```yaml
   # docker-compose.yml
   environment:
     - FYERS_APP_ID_FILE=/run/secrets/fyers_app_id
   secrets:
     - fyers_app_id
   ```

3. **Use cloud provider secrets:**
   - AWS Secrets Manager
   - Azure Key Vault
   - Google Secret Manager

## 🔐 **API Key Management**

### Development:
```bash
# Local development
cp backend/env.example backend/.env
# Edit .env with your keys
```

### Testing:
```bash
# Use test keys for CI/CD
export FYERS_APP_ID=test_app_id
export FYERS_APP_SECRET=test_secret
```

### Production:
```bash
# Use production keys
export FYERS_APP_ID=prod_app_id
export FYERS_APP_SECRET=prod_secret
```

## 🚨 **Emergency: If You Accidentally Commit Keys**

### Immediate Actions:
1. **Revoke the keys immediately** on the FYERS developer portal
2. **Generate new keys**
3. **Update your .env file**
4. **Remove from git history:**

```bash
# Remove file from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/.env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push to remove from remote
git push origin --force --all
```

## 📋 **Environment Variables Reference**

### Required Variables:
```bash
# Database
MONGODB_URI=mongodb://admin:password123@mongodb:27017/portfolio_tracker?authSource=admin

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production

# FYERS API
FYERS_APP_ID=your_fyers_app_id_here
FYERS_APP_SECRET=your_fyers_app_secret_here

# Other APIs
FREEAPI_KEY=your_freeapi_key_here
DATAJOCKEY_API_KEY=your_datajockey_api_key_here

# Configuration
PORTFOLIO_REFRESH_INTERVAL=300
```

## 🔍 **Security Monitoring**

### Regular Checks:
1. **Scan for hardcoded keys:**
   ```bash
   grep -r "your_actual_key" .
   ```

2. **Check git history:**
   ```bash
   git log --all --full-history -- backend/.env
   ```

3. **Verify .gitignore:**
   ```bash
   git check-ignore backend/.env
   ```

## 📞 **Support**

If you accidentally expose API keys:
1. **Immediately revoke them** on the provider's website
2. **Generate new keys**
3. **Update your environment**
4. **Check git history** for any other exposures

---

**Remember: Security is everyone's responsibility. Always double-check before committing sensitive data!** 