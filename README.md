# BTC Spot Price History

This repository automatically fetches and stores Bitcoin spot price history daily using GitHub Actions.

## Features

- Daily automated BTC price data collection from CoinGecko API
- CSV format with date and price columns
- GitHub Pages hosting with stable URL for latest data
- Historical data archive

## Access the Data

- **Latest data (always updated):** `https://dailysatprice.com/data/latest.csv`
- **Specific date:** `https://dailysatprice.com/data/btc_spot_YYYYMMDD.csv`

## Setup Instructions

1. Create a new GitHub repository
2. Push this code to the repository
3. Enable GitHub Pages:
   - Go to Settings → Pages
   - Source: Deploy from a branch
   - Branch: main
   - Folder: / (root)
4. Enable GitHub Actions (should be automatic)
5. The workflow will run daily at midnight UTC or can be triggered manually

## Manual Execution

Run locally:
```bash
pip install -r requirements.txt
python fetch_btc_data.py
```

## Files

- `fetch_btc_data.py` - Main script to fetch BTC data
- `.github/workflows/update_btc_data.yml` - GitHub Action for daily updates
- `data/` - Directory containing all CSV files
- `index.html` - GitHub Pages entry point with redirect to latest data