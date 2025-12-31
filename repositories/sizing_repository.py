from PyQt6.QtSql import *
from pathlib import Path
from database import db_service, DatabaseConnection
from helpers.logger import logger


class SizingRepository:
    __size_qty_sql_filepath = Path(__file__).parent.resolve() / "./sql/get_size_qty.sql"

    @staticmethod
    def find_size_qty(params: dict) -> list[dict]:
        return db_service.execute_query(
            connection_type=DatabaseConnection.ERP,
            sql_query=db_service.get_raw_sql(SizingRepository.__size_qty_sql_filepath),
            bind_values={
                "mo_no": params["mo_no"],
                "mo_noseq": None if params["mo_noseq"] == "all" else params["mo_noseq"],
            },
        )

    @staticmethod
    def migrate_to_suborder(data: list[dict]) -> int:
        """
        Migrate combined EPC from
        """
        connection = None
        query = None
        if (
            data["mo_no"] is None
            or data["mo_noseq"] == "all"
            or data["mo_noseq"] is None
            or data["mo_noseq"] == "001"
            or data["additional_qty"] <= 0
        ):
            return 0
        try:
            connection = db_service.get_connection(DatabaseConnection.DATA_LAKE)
            query = QSqlQuery(connection)
            query.prepare(
                f"""--sql
                    DECLARE @MoNo NVARCHAR(20) = :mo_no;
                    DECLARE @SizeNumCode NVARCHAR(20) = :size_numcode;
                    DECLARE @AdditionalQty INT = :additional_qty;
                    DECLARE @TargetSubOrder NVARCHAR(20) = :mo_noseq;

                    UPDATE TOP(@AdditionalQty) dv_rfidmatchmst
                    SET mo_noseq = @TargetSubOrder
                    WHERE mo_no = @MoNo
                        AND mo_noseq = '001'
                        AND size_numcode = @SizeNumCode
                        AND ri_cancel = 0
                        AND ri_type = 'A'
                        AND sole_tag = 'A'
                        AND isactive = 'Y'
                """
            )
            query.bindValue(":mo_no", data["mo_no"])
            query.bindValue(":size_numcode", data["size_numcode"])
            query.bindValue(":additional_qty", data["additional_qty"])
            query.bindValue(":mo_noseq", data["mo_noseq"])

            if not query.exec():
                raise Exception(query.lastError().text())

            return query.numRowsAffected()
        except Exception as e:
            raise Exception(e.args[0])
