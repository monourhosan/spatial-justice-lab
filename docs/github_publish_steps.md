# GitHub Publishing and Release Instructions

This repository is fully configured, tested, and prepared for publication on GitHub under the repository name:
`spatial-justice-mathematical-model`

---

## 1. Verify Local Repository Status

Before publishing, ensure all files are committed to Git:

```bash
git status
```

If any uncommitted changes remain:
```bash
git add .
git commit -m "feat: complete spatial justice mathematical model and empirical findings"
```

---

## 2. Authenticate with GitHub CLI (`gh`)

If you have not already logged in to your GitHub account:

```bash
gh auth login
```
*Follow the interactive prompts to authenticate via web browser or personal access token.*

---

## 3. Create Remote Repository and Push

### Option A: Create Public Repository (Recommended for open science)
```bash
gh repo create spatial-justice-mathematical-model --public --source=. --remote=origin --push
```

### Option B: Create Private Repository
```bash
gh repo create spatial-justice-mathematical-model --private --source=. --remote=origin --push
```

---

## 4. Manual Remote Configuration (Alternative to `gh`)

If you prefer to create the repository manually via the GitHub web UI:
1. Navigate to [https://github.com/new](https://github.com/new).
2. Set repository name to `spatial-justice-mathematical-model`.
3. Do not initialize with README, .gitignore, or license (these already exist locally).
4. Run the following commands from this repository directory:

```bash
git remote add origin https://github.com/<YOUR-USERNAME>/spatial-justice-mathematical-model.git
git branch -M main
git push -u origin main
```

---

## 5. Post-Publishing Verification

After pushing:
1. Confirm GitHub Actions CI passes at `https://github.com/<YOUR-USERNAME>/spatial-justice-mathematical-model/actions`.
2. Inspect the repository README, which contains links to derivations, figures, and reproducibility steps.
