import mariadb
from datetime import datetime
import pandas as pd
import os

#--------------------------------------------------------------------
# Handles connecting and disconnnecting from the database

def connect_to_database(username, password, host, database, ssl_enabled=False, ssl_path=None):
    """
    Connects to the database with optional SSL.
    Generic SSL file matching by extension only (.crt, .pem, .key).
    """
    try:
        connection_kwargs = {
            "user": username,
            "password": password,
            "host": host,
            "database": database
        }

        if ssl_enabled and ssl_path:
            files = os.listdir(ssl_path)
            print("Files in SSL directory:", files)

            # Sort to maintain consistent selection order
            files = sorted(files)

            # Get absolute paths for matching
            full_paths = [os.path.join(ssl_path, f) for f in files]

            ssl_ca = next((f for f in full_paths if f.endswith(('.crt', '.pem'))), None)
            ssl_cert = next((f for f in full_paths if f.endswith(('.crt', '.pem')) and f != ssl_ca), None)
            ssl_key = next((f for f in full_paths if f.endswith(('.key', '.pem'))), None)

            print("Matched ssl_ca:", ssl_ca)
            print("Matched ssl_cert:", ssl_cert or ssl_ca)  # fallback to ca if needed
            print("Matched ssl_key:", ssl_key)

            if not ssl_ca or not ssl_key:
                raise Exception("Missing required SSL files: CA or key file not found.")

            connection_kwargs.update({
                "ssl_ca": ssl_ca,
                "ssl_cert": ssl_cert or ssl_ca,  # fallback to ca if no separate cert
                "ssl_key": ssl_key
            })

        conn = mariadb.connect(**connection_kwargs)
        cursor = conn.cursor()
        return conn, cursor

    except mariadb.Error as e:
        raise Exception(f"Database connection failed: {e}")

def close_connection(conn=None, cursor=None):
    """Safely closes DB cursor and connection if they exist."""
    if cursor:
        try:
            cursor.close()
        except Exception:
            pass

    if conn:
        try:
            conn.close()
        except Exception:
            pass

    return None, None

#--------------------------------------------------------------------
#--------------------------------------------------------------------
#Fetching data

def fetch_primary_key_column(cursor, table_name):
    cursor.execute(f"SHOW KEYS FROM {table_name} WHERE Key_name = 'PRIMARY'")
    pk_info = cursor.fetchone()
    return pk_info[4] if pk_info else None

def fetch_tables(cursor):
    """
    Fetches and returns a list of tables from the database.
    """
    try:
        cursor.execute("SHOW TABLES;")
        tables = [table[0] for table in cursor.fetchall()]
        return tables
    except mariadb.Error as e:
        raise Exception(f"Failed to retrieve tables: {e}")

def fetch_data(cursor, table_name, limit=50, offset=0):
    """
    Fetch data in batches from the specified table in the database.

    Args:
        cursor (mariadb.cursor): The database cursor.
        table_name (str): Name of the table to fetch data from.
        limit (int): Number of records to fetch.
        offset (int): Offset for pagination.

    Returns:
        list: Fetched records or an empty list on error.
    """
    try:
        query = f"SELECT * FROM {table_name} ORDER BY 1 DESC LIMIT %s OFFSET %s"
        cursor.execute(query, (limit, offset))
        return cursor.fetchall()
    except mariadb.Error as e:
        print(f"Database Error: {e}")
        return []

def fetch_table_data(cursor, table_name, limit=50, offset=0, order_by=None, descending=True):
    order_clause = ""
    if order_by:
        order_clause = f"ORDER BY {order_by} {'DESC' if descending else 'ASC'}"

    query = f"SELECT * FROM {table_name} {order_clause} LIMIT {limit} OFFSET {offset}"
    cursor.execute(query)
    return cursor.fetchall()

def fetch_table_data_with_columns(cursor, table_name, limit=50, offset=0, order_by=None, descending=True):
    """
    Fetches rows and column names from a table. Use for UI rendering.
    """
    rows = fetch_table_data(cursor, table_name, limit, offset, order_by, descending)
    columns = [desc[0] for desc in cursor.description]
    return rows, columns

#--------------------------------------------------------------------
#--------------------------------------------------------------------
#Record Manipulation

def insert_record(cursor, conn, table_name, columns, values):
    """
    Inserts a record into the database.
    Returns True on success, False on failure.
    """
    try:
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        cursor.execute(query, values)
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ DB Insert Failed: {e}")
        return False

def update_column(cursor, conn, table_name, column_name, new_value, pk_column, pk_value):
    cursor.execute(
        f"UPDATE {table_name} SET {column_name} = %s WHERE {pk_column} = %s",
        (new_value, pk_value)
    )
    conn.commit()

def update_primary_key(cursor, conn, table_name, pk_column, old_pk, new_pk):
    cursor.execute(
        f"UPDATE {table_name} SET {pk_column} = %s WHERE {pk_column} = %s",
        (new_pk, old_pk)
    )
    conn.commit()

def update_status(cursor, conn, table_name, pk_column, pk_value, new_status):
    try:
        if new_status == "Completed":
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            query = f"""
                UPDATE {table_name}
                SET status = %s, EndDate = %s
                WHERE {pk_column} = %s
            """
            cursor.execute(query, (new_status, current_datetime, pk_value))
        else:
            query = f"""
                UPDATE {table_name}
                SET status = %s
                WHERE {pk_column} = %s
            """
            cursor.execute(query, (new_status, pk_value))

        conn.commit()
        return True

    except Exception as e:
        print(f"❌ ERROR in update_status: {e}")
        return False

def update_auto_increment_if_needed(cursor, conn, table_name, pk_column):
    cursor.execute(f"SELECT MAX({pk_column}) FROM {table_name}")
    max_pk = cursor.fetchone()[0]

    if max_pk is None:
        return

    cursor.execute(f"SHOW TABLE STATUS LIKE %s", (table_name,))
    table_status = cursor.fetchone()
    if table_status is None:
        return

    current_ai = table_status[10]
    new_ai = max_pk + 1

    if current_ai != new_ai:
        cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = {new_ai}")
        conn.commit()

def delete_record_by_id(conn, table_name, primary_key_column, primary_key_value):
    """Deletes a record safely and resets AUTO_INCREMENT if needed."""
    cursor = conn.cursor()

    # Check if record exists
    cursor.execute(
        f"SELECT COUNT(*) FROM {table_name} WHERE {primary_key_column} = %s;",
        (primary_key_value,)
    )
    if cursor.fetchone()[0] == 0:
        return False, "Record not found"

    # Delete the record
    cursor.execute(
        f"DELETE FROM {table_name} WHERE {primary_key_column} = %s;",
        (primary_key_value,)
    )
    conn.commit()

    # Reset AUTO_INCREMENT
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    remaining = cursor.fetchone()[0]

    if remaining > 0:
        cursor.execute(f"SELECT MAX({primary_key_column}) FROM {table_name};")
        max_id = cursor.fetchone()[0]
        if max_id:
            cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = {max_id + 1};")
    else:
        cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = 1;")

    conn.commit()
    return True, None

def delete_multiple_records(conn, table_name, primary_key_column, key_list):
    cursor = conn.cursor()
    try:
        placeholders = ','.join(['%s'] * len(key_list))
        query = f"DELETE FROM {table_name} WHERE {primary_key_column} IN ({placeholders});"
        cursor.execute(query, key_list)
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)

#--------------------------------------------------------------------
#--------------------------------------------------------------------
#Validation and checking

def check_primary_key_exists(cursor, table_name, pk_column, pk_value):
    cursor.execute(f"SELECT {pk_column} FROM {table_name} WHERE {pk_column} = %s", (pk_value,))
    result = cursor.fetchone()
    return result[0] if result else None

def check_duplicate_primary_key(cursor, table_name, pk_column, new_pk_value):
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {pk_column} = %s", (new_pk_value,))
    return cursor.fetchone()[0] > 0

#--------------------------------------------------------------------
#--------------------------------------------------------------------
# Pagination Wrapper

def paginate_table_data(fetch_function, table_name, limit, offset):
    """Handles pagination logic and returns the new offset and data."""
    new_offset = max(0, offset)
    data = fetch_function(table_name, limit, new_offset)
    return new_offset, data

#--------------------------------------------------------------------
#--------------------------------------------------------------------
#SQL Tools /Utilities

def execute_sql_query(cursor, conn, query):
    if not query:
        raise ValueError("Query is empty")

    query_lower = query.lower()
    if query_lower.startswith("select"):
        cursor.execute(query)
        results = cursor.fetchall()
        headers = [desc[0] for desc in cursor.description]
        return {"type": "select", "results": results, "headers": headers}
    else:
        cursor.execute(query)
        conn.commit()
        return {"type": "update", "rowcount": cursor.rowcount}

def export_query_results_to_excel(results, headers, file_path):
    df = pd.DataFrame(results, columns=headers)
    df.to_excel(file_path, index=False)

#--------------------------------------------------------------------
#--------------------------------------------------------------------
# Handles getting data for data visualisation in the dashboard

def get_customer_acquisition(cursor):
    cursor.execute("SELECT HowHeard, COUNT(*) FROM howheard GROUP BY HowHeard;")
    return [(src, cnt) for src, cnt in cursor.fetchall() if src and cnt]

def get_top_customers_by_jobs(cursor):
    cursor.execute("SELECT CustomerID, COUNT(*) FROM JOBS GROUP BY CustomerID ORDER BY COUNT(*) DESC LIMIT 10;")
    return [(cust, cnt) for cust, cnt in cursor.fetchall() if cust and cnt]

def get_most_frequent_device_brands(cursor):
    cursor.execute("SELECT DeviceBrand, COUNT(*) FROM JOBS GROUP BY DeviceBrand ORDER BY COUNT(*) DESC LIMIT 10;")
    return [(brand, cnt) for brand, cnt in cursor.fetchall() if brand and cnt]

def get_device_type_trends(cursor):
    cursor.execute("""
        SELECT DeviceType, COUNT(*) 
        FROM JOBS
        GROUP BY DeviceType
        ORDER BY COUNT(*) DESC
        LIMIT 10;
    """)
    return [(device, count) for device, count in cursor.fetchall() if device and count]

def get_job_status_distribution(cursor):
    cursor.execute("SELECT Status, COUNT(*) FROM JOBS GROUP BY Status;")
    return [(status, count) for status, count in cursor.fetchall() if status and count]

def get_avg_job_duration_by_technician(cursor):
    cursor.execute("""
        SELECT Technician, AVG(TIMESTAMPDIFF(DAY, StartDate, EndDate)) 
        FROM JOBS 
        WHERE StartDate IS NOT NULL AND EndDate IS NOT NULL
        GROUP BY Technician;
    """)
    return [(tech, avg) for tech, avg in cursor.fetchall() if tech and avg]

def get_top_device_issues(cursor):
    cursor.execute("""
        SELECT Issue, COUNT(*) 
        FROM JOBS
        GROUP BY Issue
        ORDER BY COUNT(*) DESC
        LIMIT 10;
    """)
    return [(issue, count) for issue, count in cursor.fetchall() if issue and count]

def get_technician_workload(cursor):
    cursor.execute("""
        SELECT Technician, COUNT(*) 
        FROM JOBS
        GROUP BY Technician
        ORDER BY COUNT(*) DESC;
    """)
    return [(tech, count) for tech, count in cursor.fetchall() if tech and count]

def get_avg_job_completion_time(cursor):
    cursor.execute("""
        SELECT AVG(TIMESTAMPDIFF(DAY, StartDate, EndDate)) 
        FROM JOBS
        WHERE StartDate IS NOT NULL AND EndDate IS NOT NULL;
    """)
    result = cursor.fetchone()
    return result[0] if result and result[0] is not None else None

def get_walkin_volume(cursor):
    cursor.execute("""
        SELECT DATE(WalkinDate), COUNT(*) 
        FROM walkins
        GROUP BY DATE(WalkinDate)
        ORDER BY DATE(WalkinDate);
    """)
    return [(date, count) for date, count in cursor.fetchall() if date and count]

def get_walkin_service_types(cursor):
    cursor.execute("""
        SELECT Description, COUNT(*) 
        FROM walkins
        GROUP BY Description
        ORDER BY COUNT(*) DESC
        LIMIT 10;
    """)
    return [(desc, count) for desc, count in cursor.fetchall() if desc and count]

def get_jobs_per_day_by_week(cursor):
    cursor.execute("""
        SELECT WEEK(StartDate) AS WeekNumber, DAYOFWEEK(StartDate) AS DayOfWeek, COUNT(*) AS JobCount
        FROM JOBS
        WHERE StartDate IS NOT NULL AND DAYOFWEEK(StartDate) != 1
        GROUP BY WeekNumber, DayOfWeek
        ORDER BY WeekNumber, DayOfWeek;
    """)
    return cursor.fetchall()

def get_avg_jobs_per_day_by_week(cursor):
    cursor.execute("""SELECT MIN(StartDate) FROM jobs;""")
    start_date = cursor.fetchone()[0] or '2000-01-01'

    cursor.execute("""
        SELECT DAYOFWEEK(StartDate) AS DayOfWeek, COUNT(*) / COUNT(DISTINCT WEEK(StartDate)) AS AvgJobCount
        FROM jobs
        WHERE DAYOFWEEK(StartDate) != 1 AND StartDate >= %s
        GROUP BY DayOfWeek
        ORDER BY DayOfWeek;
    """, (start_date,))
    return [(day, avg) for day, avg in cursor.fetchall() if day and avg]

def get_job_start_times_in_minutes(cursor):
    cursor.execute("""
        SELECT TIMESTAMPDIFF(SECOND, DATE(StartDate), StartDate)
        FROM JOBS
        WHERE StartDate IS NOT NULL;
    """)
    return [row[0] / 60 for row in cursor.fetchall() if row[0] is not None]

def get_database_summary_counts(cursor):
    cursor.execute("SELECT COUNT(*) FROM customers;")
    customers = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs;")
    jobs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Walkins;")
    walkins = cursor.fetchone()[0]
    return customers, jobs, walkins

#--------------------------------------------------------------------
#--------------------------------------------------------------------
# Handles Search Customer logic

def get_customer_id_by_job(cursor, job_id):
    cursor.execute("SELECT CustomerID FROM Jobs WHERE JobID = %s", (job_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_customer_info(cursor, customer_id):
    cursor.execute("DESCRIBE Customers")
    columns = [col[0] for col in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM Customers WHERE CustomerID = %s", (customer_id,))
    data = cursor.fetchone()
    
    return columns, data

def get_jobs_by_customer(cursor, customer_id):
    cursor.execute("DESCRIBE Jobs")
    columns = [col[0] for col in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM Jobs WHERE CustomerID = %s", (customer_id,))
    data = cursor.fetchall()
    
    return columns, data

def get_all_table_names(cursor, exclude_tables=None):
    cursor.execute("SHOW TABLES;")
    all_tables = [t[0] for t in cursor.fetchall()]
    if exclude_tables:
        return [t for t in all_tables if t.lower() not in exclude_tables]
    return all_tables

def get_table_data_for_customer(cursor, table_name, customer_id):
    cursor.execute(f"DESCRIBE `{table_name}`")
    columns = [col[0] for col in cursor.fetchall()]
    
    cursor.execute(f"""
        SELECT * FROM `{table_name}`
        WHERE JobID IN (
            SELECT JobID FROM Jobs WHERE CustomerID = %s
        )
    """, (customer_id,))
    
    data = cursor.fetchall()
    return columns, data

#--------------------------------------------------------------------

# data_access/jobs.py

def get_job_notes(cursor, job_id):
    cursor.execute("SELECT notes, status, technician FROM jobs WHERE JOBID = %s", (job_id,))
    return cursor.fetchone()

def update_job_notes(cursor, job_id, notes, status, technician, end_date=None):
    if end_date:
        cursor.execute(
            "UPDATE jobs SET notes = %s, status = %s, technician = %s, EndDate = %s WHERE JOBID = %s",
            (notes, status, technician, end_date, job_id)
        )
    else:
        cursor.execute(
            "UPDATE jobs SET notes = %s, status = %s, technician = %s WHERE JOBID = %s",
            (notes, status, technician, job_id)
        )


# data_access/costs.py

def get_cost_columns(cursor):
    cursor.execute("SHOW COLUMNS FROM costs")
    return [col[0] for col in cursor.fetchall()]

def get_costs_by_job(cursor, job_id, columns):
    cursor.execute(f"SELECT {', '.join(columns)} FROM costs WHERE JOBID = %s", (job_id,))
    return cursor.fetchall()

def insert_cost(cursor, job_id, cost_type, amount, description):
    cursor.execute(
        "INSERT INTO costs (JobID, CostType, Amount, Description) VALUES (%s, %s, %s, %s)",
        (job_id, cost_type, amount, description)
    )

def delete_cost(cursor, cost_id):
    cursor.execute("DELETE FROM costs WHERE CostID = %s", (cost_id,))

# data_access/payments.py

def get_payments(cursor, job_id):
    cursor.execute("SELECT PaymentID, Amount, PaymentType, Date FROM payments WHERE JOBID = %s", (job_id,))
    return cursor.fetchall()

def insert_payment(cursor, job_id, amount, payment_type, payment_date):
    cursor.execute(
        "INSERT INTO payments (JobID, Amount, PaymentType, Date) VALUES (%s, %s, %s, %s)",
        (job_id, amount, payment_type, payment_date)
    )

def delete_payment(cursor, payment_id):
    cursor.execute("DELETE FROM payments WHERE PaymentID = %s", (payment_id,))

# data_access/communications.py

def get_customer_contact(cursor, job_id):
    cursor.execute("""
        SELECT customers.FirstName, customers.SurName, customers.Phone, customers.Email, customers.PostCode, customers.DoorNumber
        FROM customers 
        JOIN jobs ON customers.CustomerID = jobs.CustomerID 
        WHERE jobs.JOBID = %s
    """, (job_id,))
    return cursor.fetchone()

def get_communications(cursor, job_id):
    cursor.execute("""
        SELECT CommunicationID, DateTime, CommunicationType, Note 
        FROM communications 
        WHERE JOBID = %s
    """, (job_id,))
    return cursor.fetchall()

def insert_communication(cursor, job_id, comm_type, message):
    cursor.execute("""
        INSERT INTO communications (JobID, CommunicationType, Note) 
        VALUES (%s, %s, %s)
    """, (job_id, comm_type, message))

def delete_communication(cursor, comm_id):
    cursor.execute("DELETE FROM communications WHERE CommunicationID = %s", (comm_id,))

# data_access/orders.py

def get_orders(cursor, job_id):
    cursor.execute("""
        SELECT PartID, OrderDate, Description, Quantity, TotalCost 
        FROM orders 
        WHERE JOBID = %s
    """, (job_id,))
    return cursor.fetchall()

def insert_order(cursor, job_id, description, quantity, total_cost):
    cursor.execute("""
        INSERT INTO orders (JobID, OrderDate, Description, Quantity, TotalCost)
        VALUES (%s, NOW(), %s, %s, %s)
    """, (job_id, description, quantity, total_cost))

def delete_order(cursor, order_id):
    cursor.execute("DELETE FROM orders WHERE PartID = %s", (order_id,))

# data_access/job_details.py

def get_editable_columns(cursor):
    cursor.execute("SHOW COLUMNS FROM jobs")
    all_columns = [col[0] for col in cursor.fetchall()]
    excluded = {"JobID", "EndDate", "CustomerID", "Notes", "Technician", "Status"}
    return [col for col in all_columns if col not in excluded]

def get_job_data(cursor, job_id, columns):
    cursor.execute(f"SELECT {', '.join(columns)} FROM jobs WHERE JOBID = %s", (job_id,))
    return cursor.fetchone()

def update_job_data(cursor, job_id, columns, values):
    assignments = ', '.join(f"{col} = %s" for col in columns)
    query = f"UPDATE jobs SET {assignments} WHERE JOBID = %s"
    cursor.execute(query, (*values, job_id))
