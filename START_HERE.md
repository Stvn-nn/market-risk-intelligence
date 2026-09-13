# Open your Market Risk Intelligence project

You have the full source code. You do not need GitHub to run it first.

## 1. Extract the download

Right-click `Market_risk_project.zip` → **Extract All**. Open the extracted folder until you can see `app.py`, `requirements.txt`, and `START_WINDOWS.bat` together. Do not run the project from inside the ZIP.

## 2. Install Python 3.12 if needed

Use the official [Python downloads](https://www.python.org/downloads/) and choose Python 3.12. On Windows, include the Python launcher when installing. Open a new terminal after installation.

Check it in PowerShell:

```powershell
py -3.12 --version
```

## 3. Open a terminal in the project folder

In File Explorer, open the folder containing `app.py`, click the address bar, type `powershell`, and press Enter. The terminal should start in that folder.

Copy these commands one at a time:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The first command creates an isolated Python environment. The second installs this project's libraries. The third launches the dashboard. Initial installation requires internet access and may take a few minutes.

Your browser should open the dashboard. If it doesn't, open the local address shown in the terminal. Keep the terminal open while using the app. Press **Ctrl+C** in that terminal to stop it.

After setup, double-click `START_WINDOWS.bat` whenever you want to reopen it.

## 4. Try a ticker

The opening screen is labeled **SYNTHETIC DEMO** so you can immediately explore the interface.

1. Leave the sidebar on **Market lookup**.
2. Type a symbol such as `TSLA`, `MSFT`, `VTI`, or `BRK-B`.
3. Leave `SPY` as the benchmark to start.
4. Click **Load market data**.
5. Confirm that the large ticker, source, and last observation date match your request.
6. Change the analysis window and explore the five tabs.

You can type symbols beyond these examples. Use the provider's symbol format: an international listing may require a suffix such as `.T`. A ticker can have prices without SEC financial ratios. Provider coverage is not universal.

To see company ratios, enter your SEC contact identifier and load them in the Company financials tab. For economic indicators, enter your FRED key and load them in the Economic context tab. The price charts do not require either of these inputs.

## 5. Save a research snapshot

Go to **Scenarios & report**, select **Prepare HTML report**, then **Download prepared HTML snapshot**. Open the downloaded HTML file in a browser. Charts display as embedded images without scripts, internet access, or a running Python app. For zooming and hovering, use the dashboard. This is a snapshot; it does not fetch new prices or update its ticker.

## If something goes wrong

| Message or problem | What to do |
| --- | --- |
| `py` is not recognized | Install Python with its launcher, then reopen the terminal. |
| Python 3.12 not found | Install that version, or use a compatible environment you already maintain. |
| `requirements.txt` not found | You are in the wrong folder; locate the folder containing `app.py`. |
| No usable history / request timed out | Check the symbol and network; the provider may be unavailable. Try later or use CSV/sample data. |
| Benchmark unavailable | Stock charts still work. Choose another benchmark or upload matching dates. |
| Financial ratios unavailable | The company may not have compatible SEC facts; funds/foreign filers can differ. |
| FRED key rejected | Check that you entered your own 32-character key. |
| Port already used | Stop the other app or append `--server.port 8502` to the launch command. |
| Nothing changes after typing a ticker | Click **Load market data**. The form doesn't fetch while you type. |

When ready, follow [docs/GITHUB_GUIDE.md](docs/GITHUB_GUIDE.md). You should upload the source folder contents, not only a ZIP or a screenshot.
