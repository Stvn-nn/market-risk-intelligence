# Put the project on your GitHub

Run the app locally first. Publishing source on GitHub does not automatically host a live Python dashboard.

## 1. Create an empty repository

Sign in to [GitHub](https://github.com/) and choose **New repository**. A clear name is `market-risk-intelligence`.

Suggested description: `Python dashboard for stock charts, benchmark analysis, anomaly detection, and explainable market-risk research.`

Choose Public if you want recruiters to view it. Leave the new repository's README, .gitignore, and license initialization options off: this folder already includes its README and .gitignore. Copy the repository's HTTPS URL after creation. These steps follow [GitHub's official local-code guide](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).

## 2. Open a terminal in the extracted project folder

The folder should directly contain `app.py` and `README.md`. Install Git if your computer does not have it. Check with:

```bash
git --version
```

Initialize version control:

```bash
git init -b main
git status
```

`git init` starts a local change history. `main` is the branch name. `git status` shows which files Git sees.

If Git asks for your identity when committing, set it for this project using your own values:

```bash
git config user.name "Your Name"
git config user.email "YOUR_GITHUB_COMMIT_EMAIL"
```

Your GitHub account's email settings can provide a private commit email if you prefer not to publish your regular address.

## 3. Review and make your first commit

The supplied `.gitignore` excludes the virtual environment, secrets files, caches, and Python-generated files. Credentials typed into the app are not part of the source. Review the files before publishing.

```bash
git add .
git diff --cached --stat
git commit -m "Add market risk dashboard and automated tests"
```

A **commit** is a named snapshot of the source. This local commit has not yet uploaded anything.

## 4. Connect to your repository and upload

Replace `YOUR_USERNAME` and the repository name with your actual values from step 1:

```bash
git remote add origin https://github.com/YOUR_USERNAME/market-risk-intelligence.git
git push -u origin main
```

Use the normal browser sign-in prompt if your Git installation opens one. Do not put a password or token in source files. `origin` names the remote repository; `push` uploads your commits. The `-u` option remembers the branch connection.

If `origin` already exists, inspect it with `git remote -v` before changing anything. If the push is rejected because the remote already contains files, do not force-push over them; start with the empty repository described above or reconcile the remote changes deliberately.

## 5. Verify the result on GitHub

Refresh the repository. You should see `app.py`, the `market_risk/` directory, documentation, and a rendered README. Open **Actions** to see the test workflow result. Local passing tests do not guarantee a remote run until it finishes.

The project includes a synthetic HTML report with embedded charts. You can add your own screenshot to the README after running the app. Keep the data-source label visible.

Pin the repository on your profile if you want it easy to find. Link to this repository from your resume only after you can explain and demonstrate it.

## 6. Make later updates

After changing and running the code:

```bash
git status
git add .
git commit -m "Explain the specific improvement"
git push
```

Use useful commit messages such as `Add sector benchmark presets`, not `stuff`.

## What each file does

| File or directory | Why it belongs in the repository |
| --- | --- |
| `app.py` | Dashboard interface and user flow |
| `market_risk/` | Reusable data, analytics, charts, cache, report, and API code |
| `requirements.txt` | Runtime package versions |
| `requirements-dev.txt` | Tests and optional API packages |
| `tests/` | Calculation and behavior checks |
| `docs/` | Methods, learning guide, example report, validation, GitHub instructions |
| `data/` | Explicitly synthetic CSV examples |
| `.github/workflows/tests.yml` | Runs tests after pushes and pull requests |
| `.streamlit/config.toml` | Dark theme settings |
| `.gitignore` | Keeps local environments and secrets out of commits |

A software license has not been selected for you. Add one when you decide how others may reuse your original project code; keep third-party package notices intact.
