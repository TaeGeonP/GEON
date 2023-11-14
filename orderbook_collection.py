import time
import requests
from datetime import datetime
import csv
import os
import traceback
import logging

logging.basicConfig(filename="error.log", level=logging.ERROR)


def fetch_order_book():
    response = requests.get(
        "https://api.upbit.com/v1/orderbook", params={"markets": "KRW-BTC"}
    )
    if response.status_code == 200:
        return response.json()
    else:
        error_message = f"Failed to get data: {response.status_code}"
        logging.error(error_message)
        print(error_message)
        return []


def write_to_csv(data, timestamp):
    current_time = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
    current_date = timestamp.strftime("%Y-%m-%d")
    filename = f"{current_date}-upbit-btc-orderbook.csv"

    if not os.path.exists(filename):
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["price", "quantity", "type", "timestamp"])

    with open(filename, mode="a", newline="") as file:
        writer = csv.writer(file)
        for order in data:
            for bid in order["orderbook_units"][:5]:  # Top 5 bids
                writer.writerow([bid["bid_price"], bid["bid_size"], 0, current_time])
            for ask in order["orderbook_units"][:5]:  # Top 5 asks
                writer.writerow([ask["ask_price"], ask["ask_size"], 1, current_time])


def main():
    timestamp = last_update_time = datetime.now()

    while True:
        timestamp = datetime.now()
        if (timestamp - last_update_time).total_seconds() < 1.0:
            continue
        last_update_time = timestamp
        book = {}
        book = fetch_order_book()
        if book:
            write_to_csv(book, timestamp)
            print(f"data is written - {timestamp}")
        else:
            print(f"No data to write. - {timestamp}")


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            error_message = f"{datetime.now()} | An error occurred: {e}"
            logging.error(error_message)
            print(error_message)
            traceback.print_exc()
            print("Waiting a bit before retrying...")
            time.sleep(10)
