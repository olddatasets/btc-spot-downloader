#!/usr/bin/env python3
"""Fetch BTC spot price history and save as CSV."""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

def fetch_btc_history(days="max"):
    """Fetch BTC price history from CoinGecko API."""
    # Get API key from environment variable
    api_key = os.environ.get('COINGECKO_API_KEY')

    # Use range endpoint for full history
    if days == "max" and api_key:
        # Pro API endpoint
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
        print(f"Fetching entire BTC history from April 2013 to present...")
    else:
        # Use regular endpoint for specific days
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {
            "vs_currency": "usd",
            "days": days if days != "max" else 1825,  # ~5 years without API
            "interval": "daily"
        }
        headers = {'x-cg-pro-api-key': api_key} if api_key else {}
        print(f"Fetching {params['days']} days of BTC history")

    try:
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

        return df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)

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
    <p>All data files are available in the <a href="data/">data directory</a></p>
</body>
</html>"""

    with open('index.html', 'w') as f:
        f.write(html_content)
    print(f"Updated index.html to point to {latest_filename}")

def main():
    """Main execution function."""
    print("Fetching entire BTC spot price history...")
    df = fetch_btc_history(days="max")  # Get all available history

    print(f"Fetched {len(df)} days of data")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")

    # Save to CSV
    filename = save_csv(df)

    # Update index.html
    update_index_html(filename)

    print("Done!")

if __name__ == "__main__":
    main()