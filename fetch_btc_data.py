#!/usr/bin/env python3
"""Fetch BTC spot price history and save as CSV."""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

def load_existing_data():
    """Load existing historical data from the website or local file."""
    # Try to load from published website first
    website_url = "https://dailysatprice.com/data/latest.csv"
    local_path = "data/latest.csv"

    try:
        print(f"Loading existing data from {website_url}...")
        df = pd.read_csv(website_url)
        df['date'] = pd.to_datetime(df['date']).dt.date
        print(f"Loaded {len(df)} existing records from website")
        return df
    except Exception as e:
        print(f"Could not load from website: {e}")

        # Fall back to local file if it exists
        if os.path.exists(local_path):
            try:
                print(f"Loading existing data from {local_path}...")
                df = pd.read_csv(local_path)
                df['date'] = pd.to_datetime(df['date']).dt.date
                print(f"Loaded {len(df)} existing records from local file")
                return df
            except Exception as e:
                print(f"Could not load from local file: {e}")

        # Return empty DataFrame if nothing works
        print("Starting with empty dataset")
        return pd.DataFrame(columns=['date', 'price'])

def fetch_current_btc_price():
    """Fetch current BTC price from CoinGecko free API (no API key required)."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd"
    }

    try:
        print("Fetching current BTC price from CoinGecko free API...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        price = data['bitcoin']['usd']
        today = datetime.now().date()

        print(f"Current BTC price: ${price:,.2f}")
        return pd.DataFrame([{'date': today, 'price': price}])

    except requests.exceptions.RequestException as e:
        print(f"Error fetching current price: {e}")
        sys.exit(1)

def fetch_btc_history_coingecko_pro():
    """Fetch full BTC price history from CoinGecko Pro API (requires API key)."""
    api_key = os.environ.get('COINGECKO_API_KEY')

    if not api_key:
        print("No COINGECKO_API_KEY found, cannot backfill history")
        return None

    # Pro API endpoint for full history
    url = "https://pro-api.coingecko.com/api/v3/coins/bitcoin/market_chart/range"

    # Bitcoin first had price data around 2013 on CoinGecko
    from_timestamp = int(datetime(2013, 4, 28).timestamp())
    to_timestamp = int(datetime.now().timestamp())

    params = {
        "vs_currency": "usd",
        "from": from_timestamp,
        "to": to_timestamp
    }
    headers = {'x-cg-pro-api-key': api_key}

    try:
        print(f"Fetching entire BTC history from April 2013 to present using CoinGecko Pro...")
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Convert to DataFrame
        prices = data['prices']
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])

        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['date'] = df['timestamp'].dt.date

        # Keep only date and price
        df = df[['date', 'price']]

        print(f"Successfully fetched {len(df)} days of historical data")
        return df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical data from CoinGecko Pro: {e}")
        return None

def save_csv(df, output_dir='data'):
    """Save DataFrame to CSV with timestamp in filename."""
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename with current date
    timestamp = datetime.now().strftime('%Y%m%d')
    filename = f"btc_spot_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    # Save to CSV
    df.to_csv(filepath, index=False)
    print(f"Data saved to {filepath}")

    # Also save as latest.csv for easy reference
    latest_path = os.path.join(output_dir, 'latest.csv')
    df.to_csv(latest_path, index=False)
    print(f"Data also saved to {latest_path}")

    return filename

def update_index_html(latest_filename):
    """Update index.html to redirect to the latest CSV file."""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="0; url=data/latest.csv">
    <title>BTC Spot Price Data</title>
</head>
<body>
    <h1>BTC Spot Price Historical Data</h1>
    <p>Redirecting to the latest data...</p>
    <p>If not redirected, <a href="data/latest.csv">click here for the latest data</a></p>
    <p>Latest file: <a href="data/{latest_filename}">{latest_filename}</a></p>
    <p>Source code available on <a href="https://github.com/olddatasets/btc-spot-downloader">GitHub</a></p>
</body>
</html>"""

    with open('index.html', 'w') as f:
        f.write(html_content)
    print(f"Updated index.html to point to {latest_filename}")

def main():
    """Main execution function."""
    # Load existing historical data
    df_existing = load_existing_data()

    # If no existing data, try to backfill from CoinGecko Pro
    if df_existing.empty:
        print("No existing data found, attempting to backfill from CoinGecko Pro...")
        df_historical = fetch_btc_history_coingecko_pro()

        if df_historical is not None:
            # Use the full historical data
            df_existing = df_historical
            print(f"Successfully backfilled {len(df_existing)} days of historical data")
        else:
            print("Could not backfill historical data, starting fresh with today's price only")

    # Fetch today's price
    df_today = fetch_current_btc_price()
    today = df_today['date'].iloc[0]

    # Check if today's data already exists
    if today in df_existing['date'].values:
        print(f"Price for {today} already exists, updating...")
        # Remove existing entry for today
        df_existing = df_existing[df_existing['date'] != today]

    # Append today's price
    df = pd.concat([df_existing, df_today], ignore_index=True)

    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)

    print(f"Total records: {len(df)}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")

    # Save to CSV
    filename = save_csv(df)

    # Update index.html
    update_index_html(filename)

    print("Done!")

if __name__ == "__main__":
    main()
