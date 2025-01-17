import os
import csv
from datetime import datetime


def write_data(data):
    data_folder = "data"
    mo_no_folder = os.path.join(data_folder, data["mo_no"])

    # Check if the folder exists, if not, create it
    if not os.path.exists(mo_no_folder):
        os.makedirs(mo_no_folder)

    # Create the CSV file name
    current_date = datetime.now().strftime("%Y%m%d")
    csv_filename = f"s{data['size_numcode']}__{current_date}.csv"
    csv_filepath = os.path.join(mo_no_folder, csv_filename)

    # Write the CSV file with the specified columns
    with open(csv_filepath, mode="w", newline="", encoding="utf-8-sig") as csv_file:
        fieldnames = ["EPC", "Chỉ Lệnh", "Size", "Thời Gian Phối", "Người Thực Hiện"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for epc in data["epcs"]:
            writer.writerow(
                {
                    "EPC": epc,
                    "Chỉ Lệnh": data["mo_no"],
                    "Size": data["size_numcode"],
                    "Thời Gian Phối": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Người Thực Hiện": data["created_by"],
                }
            )
