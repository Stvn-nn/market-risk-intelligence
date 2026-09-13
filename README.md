# market-risk-intelligence
Python dashboard for stock charts, risk analysis, and anomaly detection.

# Market Risk Intelligence Dashboard

A Python dashboard for exploring stock prices, comparing market performance, and understanding financial risk through interactive charts and explainable calculations.

## Project Purpose

This project connects my interests in computer science, finance, and data analytics. It brings price data, company financials, and economic indicators into one dashboard to help users explore what is happening in the market.

## Features

* **Custom ticker lookup:** Enter a supported ticker to request its price history.
* **Interactive charts:** Explore candlestick and line charts, trading volume, and moving averages.
* **Benchmark comparisons:** Compare an asset’s performance against SPY or another selected benchmark.
* **Risk metrics:** Calculate returns, volatility, beta, and maximum drawdown.
* **Anomaly detection:** Flag unusually large daily price movements using a rolling statistical method.
* **Explainable risk index:** View the factors and weights behind the displayed score.
* **Company financials:** Load supported annual financial ratios from SEC filings.
* **Economic indicators:** Explore Treasury yields, unemployment, and inflation through FRED.
* **Report exports:** Download price data and HTML reports with embedded charts.
* **Dark interface:** Green indicates increases, while red indicates decreases.

## Technologies

* **Python** — application logic
* **Pandas and NumPy** — data processing and calculations
* **Streamlit** — dashboard interface
* **Plotly** — interactive charts
* **Matplotlib** — report chart images
* **SQLite** — local data caching
* **pytest** — automated checks
* **FastAPI** — optional API

## Running the Dashboard

With Python 3.12 installed, open PowerShell in the project folder and run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The dashboard opens in your browser. Enter a ticker in the sidebar and select **Load market data**.

## Data and Project Status

The dashboard includes clearly labeled synthetic examples for exploring its features without connecting to a data provider.

Market history comes through yfinance, company financials through SEC EDGAR, and economic indicators through FRED. Coverage varies by ticker. SEC requests require a contact identifier, and FRED requires an API key.

Automated checks cover financial calculations, input validation, anomaly detection, and key dashboard interactions. Live integrations still require end-to-end verification.

The risk index uses illustrative formulas and weights; it is not a validated prediction model.

## Learning Focus

Developed with AI assistance as a hands-on project connecting Python programming, financial analysis, data visualization, and backend design.
