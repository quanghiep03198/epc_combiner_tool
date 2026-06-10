import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum

from dotenv import load_dotenv
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import *

from constants import DB_DRIVER
from helpers.configuration import ConfigService
from helpers.logger import logger

load_dotenv()


class DataSources(Enum):
    DATA_LAKE = "DV_DATA_LAKE"
    ERP = "wuerp_vnrd"
    SYSCLOUD = "syscloud_vn"


class DatabaseConnection(Enum):
    DATA_LAKE = "DATA_LAKE"
    ERP = "ERP"
    SYSCLOUD = "SYSCLOUD"


configuration = ConfigService.load_configs()


class DatabaseService:
    __instance = None
    __lock = threading.Lock()
    __connection_pools = {}
    __connections = {}

    def __new__(cls):
        if cls.__instance is None:
            with cls.__lock:
                if cls.__instance is None:
                    cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.__init_connection_pools()

    def __init_connection_pools(self):
        """Initialize connection pools for each database"""
        for conn_type in DatabaseConnection:
            self.__connection_pools[conn_type.value] = []

    def __create_connection(self, server: str, database: str, connection_name: str):
        """Create a single database connection"""
        if not any(
            value == "" for key, value in configuration.items() if key.startswith("DB")
        ):
            try:
                database_name = (
                    f"DRIVER={DB_DRIVER};"
                    f"SERVER={server};"
                    f"PORT={configuration.get('DB_PORT')};"
                    f"DATABASE={database};"
                    f"UID={configuration.get('DB_UID')};"
                    f"PWD={configuration.get('DB_PWD')};"
                    f"MARS_Connection=yes;"
                )

                # Generate unique connection name for thread safety
                unique_conn_name = (
                    f"{connection_name}_{threading.current_thread().ident}"
                )

                if QSqlDatabase.contains(unique_conn_name):
                    QSqlDatabase.removeDatabase(unique_conn_name)

                data_source = QSqlDatabase.addDatabase("QODBC", unique_conn_name)
                data_source.setDatabaseName(database_name)

                if data_source.open():
                    logger.info(f"Connected to database: {unique_conn_name}")
                    return data_source
                else:
                    error = data_source.lastError().text()
                    logger.error(f"Failed to connect: {error}")
                    return None

            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                return None
        return None

    def get_connection(self, connection_type: DatabaseConnection):
        """Get connection from pool or create new one - thread-safe"""
        # Create a unique connection for each thread to avoid ODBC conflicts
        thread_id = threading.current_thread().ident
        connection_key = f"{connection_type.value}_{thread_id}"

        with self.__lock:
            # Check if we already have a connection for this thread
            if connection_key in self.__connections:
                conn = self.__connections[connection_key]
                if conn and conn.isOpen():
                    return conn
                else:
                    # Remove invalid connection
                    del self.__connections[connection_key]

            # Create new connection for this thread
            if connection_type == DatabaseConnection.ERP:
                conn = self.__create_connection(
                    server=configuration.get("DB_SERVER"),
                    database=DataSources.ERP.value,
                    connection_name=f"Thread_{connection_type.value}_{thread_id}",
                )
            elif connection_type == DatabaseConnection.DATA_LAKE:
                conn = self.__create_connection(
                    server=configuration.get("DB_SERVER"),
                    database=DataSources.DATA_LAKE.value,
                    connection_name=f"Thread_{connection_type.value}_{thread_id}",
                )
            elif connection_type == DatabaseConnection.SYSCLOUD:
                conn = self.__create_connection(
                    server=configuration.get("DB_SERVER"),
                    database=DataSources.SYSCLOUD.value,
                    connection_name=f"Thread_{connection_type.value}_{thread_id}",
                )
            else:
                return None

            if conn:
                self.__connections[connection_key] = conn
            return conn

    def execute_query(
        self, connection_type: DatabaseConnection, sql_query: str, bind_values=None
    ):
        """
        Execute single query with optional parameter binding

        Args:
            connection_type: Database connection type
            sql_query: SQL query string (can contain ? placeholders or :named placeholders)
            bind_values: Parameters to bind to query
                        - List/tuple for positional parameters (?)
                        - Dict for named parameters (:name)
                        - None for queries without parameters

        Returns:
            List of dictionaries containing query results, or None if failed

        Examples:
            # Positional parameters
            execute_query(conn, "SELECT * FROM users WHERE id = ? AND name = ?", [1, "John"])

            # Named parameters
            execute_query(conn, "SELECT * FROM users WHERE id = :id AND name = :name", {"id": 1, "name": "John"})

            # No parameters
            execute_query(conn, "SELECT * FROM users")
        """
        connection = self.get_connection(connection_type)
        if not connection:
            logger.error(f"Failed to get connection for {connection_type}")
            return None

        try:
            query = QSqlQuery(connection)

            # Prepare query if we have bind values
            if bind_values is not None:
                if not query.prepare(sql_query):
                    logger.error(
                        f"Query preparation failed: {query.lastError().text()}"
                    )
                    return None

                # Bind values based on type
                if isinstance(bind_values, (list, tuple)):
                    # Positional parameters (?)
                    for i, value in enumerate(bind_values):
                        query.bindValue(i, value)
                        logger.debug(f"Bound positional parameter {i}: {value}")

                elif isinstance(bind_values, dict):
                    # Named parameters (:name)
                    for key, value in bind_values.items():
                        # Add colon prefix if not present
                        param_name = key if key.startswith(":") else f":{key}"
                        query.bindValue(param_name, value)
                        logger.debug(f"Bound named parameter {param_name}: {value}")
                else:
                    logger.warning(f"Unsupported bind_values type: {type(bind_values)}")
                    return None

                # Execute prepared query
                success = query.exec()
            else:
                # Execute query without parameters
                success = query.exec(sql_query)

            if success:
                results = []
                while query.next():
                    record = {}
                    for i in range(query.record().count()):
                        field_name = query.record().fieldName(i)
                        field_value = query.value(i)
                        record[field_name] = field_value
                    results.append(record)

                logger.debug(
                    f"Query executed successfully, returned {len(results)} rows"
                )
                return results
            else:
                error_text = query.lastError().text()
                logger.error(f"Query execution failed: {error_text}")
                logger.error(f"SQL: {sql_query}")
                if bind_values:
                    logger.error(f"Parameters: {bind_values}")
                return None

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            logger.error(f"SQL: {sql_query}")
            if bind_values:
                logger.error(f"Parameters: {bind_values}")
            return None

    def execute_parallel_queries(self, query_configs: list, max_workers: int = 3):
        """
        Execute multiple queries in parallel with parameter binding support

        Args:
            query_configs: List of dict with keys:
                          - 'connection_type': DatabaseConnection enum
                          - 'sql_query': SQL query string
                          - 'query_name': Unique identifier for this query
                          - 'bind_values': Optional parameters to bind (list/tuple for positional, dict for named)
            max_workers: Maximum number of parallel threads

        Returns:
            Dict with query results mapped by query_name

        Example:
            query_configs = [
                {
                    'connection_type': DatabaseConnection.ERP,
                    'sql_query': 'SELECT * FROM orders WHERE status = ? AND date > ?',
                    'bind_values': ['active', '2024-01-01'],
                    'query_name': 'active_orders'
                },
                {
                    'connection_type': DatabaseConnection.DATA_LAKE,
                    'sql_query': 'SELECT COUNT(*) as total FROM products WHERE category = :cat',
                    'bind_values': {'cat': 'electronics'},
                    'query_name': 'product_count'
                }
            ]
        """
        results = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all queries
            future_to_query = {}
            for config in query_configs:
                # Extract bind_values if present
                bind_values = config.get("bind_values", None)

                future = executor.submit(
                    self.execute_query,
                    config["connection_type"],
                    config["sql_query"],
                    bind_values,
                )
                future_to_query[future] = config["query_name"]

            # Collect results as they complete
            for future in as_completed(future_to_query):
                query_name = future_to_query[future]
                try:
                    result = future.result()
                    results[query_name] = result
                    logger.info(f"Query '{query_name}' completed successfully")
                except Exception as e:
                    logger.error(f"Query '{query_name}' failed: {e}")
                    results[query_name] = None

        return results

    def execute_non_query(
        self, connection_type: DatabaseConnection, sql_query: str, bind_values=None
    ):
        """
        Execute INSERT, UPDATE, DELETE operations with parameter binding

        Args:
            connection_type: Database connection type
            sql_query: SQL query string (INSERT/UPDATE/DELETE)
            bind_values: Parameters to bind to query

        Returns:
            Number of affected rows, or -1 if failed

        Examples:
            # Insert with positional parameters
            execute_non_query(conn, "INSERT INTO users (name, email) VALUES (?, ?)", ["John", "john@email.com"])

            # Update with named parameters
            execute_non_query(conn, "UPDATE users SET email = :email WHERE id = :id", {"email": "new@email.com", "id": 1})

            # Delete
            execute_non_query(conn, "DELETE FROM users WHERE id = ?", [1])
        """
        connection = self.get_connection(connection_type)
        if not connection:
            logger.error(f"Failed to get connection for {connection_type}")
            return -1

        try:
            query = QSqlQuery(connection)

            # Prepare query if we have bind values
            if bind_values is not None:
                if not query.prepare(sql_query):
                    logger.error(
                        f"Query preparation failed: {query.lastError().text()}"
                    )
                    return -1

                # Bind values based on type
                if isinstance(bind_values, (list, tuple)):
                    # Positional parameters (?)
                    for i, value in enumerate(bind_values):
                        query.bindValue(i, value)

                elif isinstance(bind_values, dict):
                    # Named parameters (:name)
                    for key, value in bind_values.items():
                        param_name = key if key.startswith(":") else f":{key}"
                        query.bindValue(param_name, value)
                else:
                    logger.warning(f"Unsupported bind_values type: {type(bind_values)}")
                    return -1

                # Execute prepared query
                success = query.exec()
            else:
                # Execute query without parameters
                success = query.exec(sql_query)

            if success:
                affected_rows = query.numRowsAffected()
                logger.debug(
                    f"Non-query executed successfully, affected {affected_rows} rows"
                )
                return affected_rows
            else:
                error_text = query.lastError().text()
                logger.error(f"Non-query execution failed: {error_text}")
                logger.error(f"SQL: {sql_query}")
                if bind_values:
                    logger.error(f"Parameters: {bind_values}")
                return -1

        except Exception as e:
            logger.error(f"Error executing non-query: {e}")
            logger.error(f"SQL: {sql_query}")
            if bind_values:
                logger.error(f"Parameters: {bind_values}")
            return -1

    def execute_batch(
        self, connection_type: DatabaseConnection, sql_query: str, batch_values: list
    ):
        """
        Execute batch operations (multiple rows with same query)

        Args:
            connection_type: Database connection type
            sql_query: SQL query string with placeholders
            batch_values: List of parameter sets to execute

        Returns:
            Number of successful executions, or -1 if failed

        Example:
            # Batch insert
            sql = "INSERT INTO products (name, price, category) VALUES (?, ?, ?)"
            batch_data = [
                ["Product 1", 100.0, "Electronics"],
                ["Product 2", 200.0, "Books"],
                ["Product 3", 150.0, "Electronics"]
            ]
            execute_batch(conn, sql, batch_data)
        """
        connection = self.get_connection(connection_type)
        if not connection:
            logger.error(f"Failed to get connection for {connection_type}")
            return -1

        if not batch_values:
            logger.warning("No batch values provided")
            return 0

        try:
            query = QSqlQuery(connection)

            if not query.prepare(sql_query):
                logger.error(
                    f"Batch query preparation failed: {query.lastError().text()}"
                )
                return -1

            successful_executions = 0

            # Execute for each set of parameters
            for i, values in enumerate(batch_values):
                try:
                    # Clear previous bindings
                    query.clear()

                    # Bind values for this iteration
                    if isinstance(values, (list, tuple)):
                        for j, value in enumerate(values):
                            query.bindValue(j, value)
                    elif isinstance(values, dict):
                        for key, value in values.items():
                            param_name = key if key.startswith(":") else f":{key}"
                            query.bindValue(param_name, value)
                    else:
                        logger.error(
                            f"Unsupported batch value type at index {i}: {type(values)}"
                        )
                        continue

                    if query.exec():
                        successful_executions += 1
                        logger.debug(f"Batch execution {i+1} successful")
                    else:
                        logger.error(
                            f"Batch execution {i+1} failed: {query.lastError().text()}"
                        )
                        logger.error(f"Values: {values}")

                except Exception as e:
                    logger.error(f"Error in batch execution {i+1}: {e}")
                    logger.error(f"Values: {values}")

            logger.info(
                f"Batch execution completed: {successful_executions}/{len(batch_values)} successful"
            )
            return successful_executions

        except Exception as e:
            logger.error(f"Error executing batch: {e}")
            return -1

    @staticmethod
    def get_raw_sql(file_path):
        try:
            with open(file_path, "r", -1, "utf-8") as file:
                return file.read()
        except Exception as e:
            logger.error(f"[DatabaseService] Error reading SQL file: {e}")
            return None

    def close_all_connections(self):
        """Close all connections in pools"""
        with self.__lock:
            # Close thread-specific connections
            for conn in self.__connections.values():
                if conn and conn.isOpen():
                    conn.close()
            self.__connections.clear()

            # Close pool connections
            for pool in self.__connection_pools.values():
                for conn in pool:
                    if conn.isOpen():
                        conn.close()
            self.__connection_pools.clear()


# Initialize singleton instance
db_service = DatabaseService()
