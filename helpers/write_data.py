import os
import csv
from datetime import datetime
from helpers.configuration import ConfigService, ConfigSection
from helpers.logger import logger
from PyQt6.QtWidgets import QFileDialog
from i18n import I18nService
from helpers.disutils import strtobool


def __write_file(csv_filepath: str, data: dict):
    with open(csv_filepath, mode="w", newline="", encoding="utf-8-sig") as csv_file:
        fieldnames = [
            "EPC",
            I18nService.t("fields.mo_no"),
            I18nService.t("fields.size_numcode"),
            I18nService.t("fields.ri_date"),
            I18nService.t("fields.user_name_created"),
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for epc in data["epcs"]:
            writer.writerow(
                {
                    "EPC": epc,
                    I18nService.t("fields.mo_no"): data["mo_no"],
                    I18nService.t("fields.size_numcode"): data["size_numcode"],
                    I18nService.t("fields.ri_date"): datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    I18nService.t("fields.user_name_created"): data["created_by"],
                }
            )


def write_data(data: dict):
    """
    Write combination data to CSV file

    Args:
    - data (dict): Combination data
    """

    is_auto_save_enabled = ConfigService.get_conf(
        section=ConfigSection.DATA.value,
        key="auto_save",
        serializer=lambda value: strtobool(value),
    )

    if not is_auto_save_enabled:
        file_dialog = QFileDialog()
        options = QFileDialog.Options()
        file_dialog.setMinimumWidth(800)
        file_dialog.setDefaultSuffix("csv")
        csv_filepath, _ = file_dialog.getSaveFileName(
            parent=None,
            caption="Save CSV File",
            directory="",
            filter="CSV Files (*.csv);;All Files (*)",
            options=options,
        )
        if csv_filepath:
            try:
                __write_file(csv_filepath, data)
            except Exception as e:
                print(e)
    else:
        data_folder = "data"
        mo_no_folder = os.path.join(data_folder, data["mo_no"])

        # Check if the folder exists, if not, create it
        if not os.path.exists(mo_no_folder):
            os.makedirs(mo_no_folder)

        # Create the CSV file name
        current_date = datetime.now().strftime("%Y%m%d")
        csv_filename = f"s{data['size_numcode']}__{current_date}.csv"
        csv_filepath = os.path.join(mo_no_folder, csv_filename)
        __write_file(csv_filepath, data)
