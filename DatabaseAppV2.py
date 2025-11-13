# ─────────────────────────────────────────────────────────────────────────────
# 📦 Standard Library
import sys
import threading
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# 🛢 Database
import mariadb

# ─────────────────────────────────────────────────────────────────────────────
# 📊 Data Handling & Visualization
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# 🎨 PyQt5 Core & GUI
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QFont, QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrinterInfo
from PyQt5.QtWidgets import (
    QApplication,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
)

# ─────────────────────────────────────────────────────────────────────────────
# 🧩 Project Modules

# File operationsrootROOTroo
from FILE_OPS.file_ops import load_schedule_on_startup, run_scheduled_backups
from FILE_OPS.config import load_settings

# UI components
from UI.splashscreen import SplashScreen
from UI.initthread import InitializationThread
from UI.tabbed_dashboard import TabbedDashboard
from UI.ui import (
    add_record_dialog,
    create_login_page,
    create_settings_page,
    create_table_view_dialog,
    display_tables_ui,
    edit_selected_job,
    event_filter,
    handle_login,
    handle_logout,
    keyPressEvent,
    main_menu_page,
    refresh_page,
    save_settings,
    update_table_offset_ui,
    load_table,
    populate_table,
    confirm_deletion_bulk,
    confirm_deletion,
    show_info,
    create_customer_report_window,
)
from UI.ui_edit_notes import (
    JobDetailsDialog,
    JobNotesEditor,
    CommunicationsDialog,
    CostsDialog,
    PaymentsDialog,
    AddToOrdersDialog,
    OrdersDialog,
)

# Database access
from DB.data_access import (
    check_duplicate_primary_key,
    check_primary_key_exists,
    connect_to_database,
    fetch_data,
    fetch_primary_key_column,
    fetch_table_data_with_columns,
    fetch_tables,
    insert_record,
    update_auto_increment_if_needed,
    update_column,
    update_primary_key,
    update_status,
    get_customer_id_by_job,
    get_customer_info,
    get_jobs_by_customer,
    get_all_table_names,
    get_table_data_for_customer,
    get_customer_contact,
    get_job_notes,
    update_job_notes,
)

# Error handling
from UTILS.error_utils import handle_db_error, log_error

# Dashboard (Tabbed)
from UI.tabbed_dashboard import TabbedDashboard
from UI.ui import confirm_deletion, show_info

from UI.ui_edit_notes import JobDetailsDialog, JobNotesEditor, CommunicationsDialog, CostsDialog, PaymentsDialog, AddToOrdersDialog, OrdersDialog

from DB.data_access import get_job_notes, update_job_notes

from Templates.job_report_template import JOB_REPORT_TEMPLATE



class DatabaseApp(QMainWindow):

    #============================================
    #           Initialization & Setup
    #============================================

    SETTINGS_FILE = "settings.json"
    SCHEDULE_FILE_PATH = "backup_schedule.json"
    
    def __init__(self): #MAIN
        super().__init__()
        

        # ✅ Load and apply scheduled jobs
        load_schedule_on_startup(self)

        self.is_refreshing = False
        self.is_backup_running = False
        self.is_adding_new_record = False
        

        self.setWindowTitle("DBDoc V2 - Database Management System")
        self.setGeometry(100, 100, 500, 500)
        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E1E; }
            QLabel { color: #FFFFFF; font-size: 14px; }
            QLineEdit { background-color: #2A2A2A; color: #FFFFFF; border: 1px solid #444; padding: 5px; border-radius: 5px; }
            QPushButton { background-color: #3A9EF5; color: #FFFFFF; border-radius: 5px; padding: 10px; }
            QPushButton:hover { background-color: #1D7DD7; }
        """)

        # ✅ Load database settings
        self.database_config = load_settings()

        # ✅ UI Page setup
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.login_page = create_login_page(self)
        self.settings_page, self.host_entry, self.database_entry, self.ssl_checkbox, self.ssl_path_entry = create_settings_page(
            self.database_config,
            lambda: save_settings(self.database_config, self.host_entry, self.database_entry, self.ssl_checkbox, self.ssl_path_entry, self.SETTINGS_FILE, self.central_widget, self.login_page, self),
            lambda: self.central_widget.setCurrentWidget(self.login_page)
        )

        self.central_widget.addWidget(self.login_page)
        self.central_widget.addWidget(self.settings_page)

        # ✅ Start backup scheduler thread
        self.scheduler_stop_event = threading.Event()
        self.scheduler_thread = threading.Thread(
            target=run_scheduled_backups,
            args=(self.scheduler_stop_event,),
            daemon=True
        )
        self.scheduler_thread.start()
    
    #============================================
    #       Authentication / User Session
    #============================================
    
    def login(self): #MAIN
        handle_login(
            ui_instance=self,
            database_config=self.database_config,
            connect_func=connect_to_database,
            on_success_callback=main_menu_page
        )
    def logout(self): #MAIN
        handle_logout(self)

#---------------------------------------------------------------------------------
   
    #============================================
    #       Page Navigation & UI Control
    #============================================
    
    def dashboard_page(self): #MAIN
            dlg = TabbedDashboard(parent=self, cursor=self.cursor)
            dlg.exec_()
    def Customer_report(self, job_id=None):  # MAIN
        if job_id is None:
            job_id, ok = QInputDialog.getText(self, "🔍 Search Job", "Enter Job ID:")
            if not ok or not job_id.strip():
                return
            job_id = job_id.strip()

        customer_id = get_customer_id_by_job(self.cursor, job_id)
        if not customer_id:
            QMessageBox.critical(self, "Job Not Found", f"No job found with ID {job_id}.")
            return

        customer_columns, customer_info = get_customer_info(self.cursor, customer_id)
        job_columns, jobs_data = get_jobs_by_customer(self.cursor, customer_id)

        tables = get_all_table_names(self.cursor, exclude_tables=["customers", "jobs", "walkins"])
        related_tables_data = {
            table: get_table_data_for_customer(self.cursor, table, customer_id)
            for table in tables
        }

        window = create_customer_report_window(
            self, customer_id, customer_info, customer_columns,
            jobs_data, job_columns, related_tables_data
        )
        window.exec_()
    def view_notes(self, job_id=None):
        if job_id is None:
            job_id, ok = QInputDialog.getText(None, "🔍 Search Job", "Enter Job ID:")
            if not ok or not job_id:
                return

        job_id = str(job_id).strip()
        if not job_id.isdigit():
            QMessageBox.warning(None, "⚠ Invalid Input", "Job ID must be a number.")
            return

        result = get_job_notes(self.cursor, job_id)
        if not result:
            QMessageBox.critical(None, "❌ Job Not Found", f"No job found with ID {job_id}.")
            return

        dialog = JobNotesEditor(
                                    job_id,
                                    result,
                                    save_callback=lambda *args: update_job_notes(self.cursor, *args),
                                    cursor=self.cursor,
                                    conn=self.conn
                                )



        if dialog.exec_():
            self.conn.commit()
    def view_costs(self, job_id):
        dialog = CostsDialog(job_id, self.cursor, self.conn)
        dialog.exec_() 
    def view_communications(self, job_id):
        dialog = CommunicationsDialog(job_id, self.cursor, self.conn)
        dialog.exec_()
    def view_payments(self, job_id):
        dialog = PaymentsDialog(job_id, self.cursor, self.conn)
        dialog.exec_()
    def view_orders(self, job_id):
        dialog = OrdersDialog(job_id, self.cursor, self.conn)
        dialog.exec_()
    def view_edit_job_details(self, job_id):
        dialog = JobDetailsDialog(job_id, self.cursor, self.conn)
        dialog.exec_()

#---------------------------------------------------------------------------------

    #============================================
    #           Table Viewing & Pagination
    #============================================

    def view_tables(self): #MAIN
        try:
            tables = fetch_tables(self.cursor)
            display_tables_ui(tables, self.view_table_data)
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))
    
    def view_table_data(self, table_name): #MAIN
        self.table_name = table_name
        self.current_table_name = table_name
        self.table_offset = 0
        self.table_limit = 50

        try:
            data, columns = fetch_table_data_with_columns(
                self.cursor,
                table_name,
                limit=self.table_limit,
                offset=self.table_offset
            )
            self.columns = columns


            self.table_widget = QTableWidget()
            self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)

            self.table_widget.setColumnCount(len(columns))
            self.table_widget.setHorizontalHeaderLabels(columns)
            self.table_widget.setAlternatingRowColors(True)
            

            # ✅ Load table data
            load_table(
                table_widget=self.table_widget,
                cursor=self.cursor,
                table_name=table_name,
                update_status_callback=self.update_status_and_database,
                table_offset=self.table_offset,
                limit=self.table_limit,
                event_filter=self
            )

            self.pagination_label = QLabel()
            current_page = (self.table_offset // self.table_limit) + 1
            self.pagination_label.setText(f"Page {current_page}")

            # ✅ Create the dialog UI (next step)
            self.dialog, prev_btn, next_btn, self.refresh_button, self.status_bar = create_table_view_dialog(
            table_name=table_name,
            columns=columns,
            table_widget=self.table_widget,
            pagination_label=self.pagination_label,
            refresh_handler=self.refresh_table,
            search_handler=lambda col, val: self.search_table(col, val),
            prev_handler=lambda: self.update_table_offset(
                -self.table_limit,
                prev_button=prev_btn,
                next_button=next_btn
            ),
            next_handler=lambda: self.update_table_offset(
                self.table_limit,
                prev_button=prev_btn,
                next_button=next_btn
            ),
            add_handler=lambda: add_record_dialog(
                table_name=self.current_table_name,
                columns=self.columns,
                column_types=self.get_column_types(),  # You might need a helper
                db_insert_func=lambda t, c, v: insert_record(self.cursor, self.conn, t, c, v),
                refresh_callback=self.refresh_table,
                parent=self.dialog  # or self if you’re using QWidget
            ),

            edit_handler=lambda: edit_selected_job(self),
            delete_handler=lambda: self.handle_delete_record(table_name, self.table_widget, columns[0]),
            print_handler=lambda: self.handle_print_record(table_name, self.table_widget, columns[0]),
            close_handler=lambda: self.dialog.close()
        )
            self.table_widget.itemChanged.connect(self.update_database)


            self.dialog.exec_()

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load data for {table_name}: {e}")
    
    def get_column_types(self): #MAIN
            """
            Fetches a dictionary of column_name: column_type for the current table.
            """
            self.cursor.execute(f"DESCRIBE {self.current_table_name}")
            return {col[0]: col[1] for col in self.cursor.fetchall()}
    def update_table_offset(self, change, prev_button, next_button): #MAIN
        # ✅ Compute new offset safely
        new_offset = max(0, self.table_offset + change)
        self.table_offset = new_offset  # ✅ Store for future pages

        print(f"🔄 Current offset is now: {self.table_offset}")  # Debug log

        # ✅ Refresh the table with the correct offset
        update_table_offset_ui(
            table_widget=self.table_widget,
            pagination_label=self.pagination_label,
            prev_button=prev_button,
            next_button=next_button,
            fetch_function=self.fetch_data,  # Must reflect the new offset!
            table_name=self.table_name,
            current_offset=self.table_offset,
            limit=self.table_limit,
            change=0,  # We've already applied it
            refresh_callback=lambda: refresh_page(self),
            parent=self
        )
    def refresh_table(self, suppress_status=False): #MAIN
        """UI logic to refresh the table."""
        if self.is_refreshing:
            print("❌ Refresh is already in progress. Please wait...")
            self.status_bar.setText("⏳ Refresh already in progress...")
            return
        
        if not suppress_status:
            self.is_refreshing = True
            self.refresh_button.setEnabled(False)
            self.status_bar.setText("🔄 Refreshing table...")

        try:
            self.table_widget.itemChanged.disconnect(self.update_database)
            self.table_widget.setRowCount(0)

            load_table(
                table_widget=self.table_widget,
                cursor=self.cursor,
                table_name=self.current_table_name,
                update_status_callback=self.update_status_and_database,
                table_offset=self.table_offset,
                limit=50,
                event_filter=self
            )

            print(f"✅ Table {self.current_table_name} refreshed successfully.")
            if not suppress_status:
                now = datetime.now().strftime("%H:%M:%S")
                self.status_bar.setText(f"✅ Refreshed '{self.current_table_name}' at {now}")


        except Exception as e:
            print(f"❌ ERROR: Failed to refresh table {self.current_table_name}: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to refresh table: {e}")
            self.status_bar.setText("❌ Failed to refresh table.")

        finally:
            self.table_widget.itemChanged.connect(self.update_database)
            self.is_refreshing = False
            self.refresh_button.setEnabled(True)
    def search_table(self, selected_columns, search_text):#MAIN
        """Search using multiple tokens across selected columns."""

        if not selected_columns or not search_text.strip():
            self.status_bar.setText("ℹ️ Select column(s) and enter search text.")
            return

        try:
            tokens = [word.strip() for word in search_text.strip().split() if word.strip()]
            if not tokens:
                self.status_bar.setText("ℹ️ No valid keywords entered.")
                return

            now = datetime.now().strftime("%H:%M:%S")

            # Build WHERE clause: each token must match at least one column
            conditions = []
            params = []

            for token in tokens:
                token_conditions = [f"`{col}` LIKE %s" for col in selected_columns]
                conditions.append(f"({' OR '.join(token_conditions)})")
                params.extend([f"%{token}%"] * len(selected_columns))

            where_clause = " AND ".join(conditions)
            query = f"""
                SELECT * FROM `{self.current_table_name}`
                WHERE {where_clause};
            """

            self.cursor.execute(query, tuple(params))
            results = self.cursor.fetchall()

            if not results:
                self.table_widget.setRowCount(0)
                self.status_bar.setText(
                    f"⚠ No matches for '{search_text.strip()}' in {', '.join(selected_columns)}"
                )
            else:
                populate_table(self.table_widget, self.current_table_name, results, self.update_status_and_database)
                self.status_bar.setText(
                    f"🔍 {len(results)} result(s) for '{search_text.strip()}' in {', '.join(selected_columns)} at {now}"
                )

        except mariadb.Error as e:
            QMessageBox.critical(self, "Database Error", f"❌ Database Error: {e}")
            self.status_bar.setText("❌ Search failed.")

#---------------------------------------------------------------------------------

    #============================================
    #           Table Editing (CRUD)
    #============================================

    def update_database(self, item):  # MAIN
        self.table_widget.blockSignals(True)

        try:
            row = item.row()
            column = item.column()
            new_value = item.text().strip() or None

            pk_column = fetch_primary_key_column(self.cursor, self.current_table_name)
            if not pk_column:
                print("❌ ERROR: No primary key found.")
                self._update_status("❌ No primary key found.")
                return

            pk_index = next(
                (i for i in range(self.table_widget.columnCount())
                if self.table_widget.horizontalHeaderItem(i).text() == pk_column),
                None
            )
            if pk_index is None:
                print(f"❌ ERROR: ID column '{pk_column}' not found in UI.")
                self._update_status(f"❌ ID column '{pk_column}' not found.")
                return

            pk_item = self.table_widget.item(row, pk_index)
            if not pk_item:
                print(f"❌ ERROR: No ID item found in row {row}.")
                self._update_status(f"❌ No ID item found in row {row}.")
                return

            old_pk = pk_item.data(Qt.UserRole) or pk_item.text().strip()
            db_old_pk = check_primary_key_exists(self.cursor, self.current_table_name, pk_column, old_pk)

            if db_old_pk is None:
                print(f"❌ ERROR: Old ID {old_pk} not found in DB.")
                self._update_status(f"❌ ID {old_pk} not found in database.")
                return

            if new_value == str(db_old_pk):
                self._update_status("ℹ️ Value unchanged.")
                return

            now = datetime.now().strftime("%H:%M:%S")

            if column == pk_index:
                # Updating PK
                if check_duplicate_primary_key(self.cursor, self.current_table_name, pk_column, new_value):
                    print(f"❌ PK {new_value} already exists.")
                    self._update_status(f"❌ Duplicate PK: {new_value}")
                    pk_item.setText(str(db_old_pk))  # revert
                    return

                update_primary_key(self.cursor, self.conn, self.current_table_name, pk_column, db_old_pk, new_value)
                pk_item.setData(Qt.UserRole, new_value)
                pk_item.setText(str(new_value))
                print(f"✅ ID updated from {db_old_pk} → {new_value}")
                self._update_status(f"🔑 ID updated from {db_old_pk} to {new_value}")

            else:
                col_name = self.table_widget.horizontalHeaderItem(column).text()
                update_column(self.cursor, self.conn, self.current_table_name, col_name, new_value, pk_column, db_old_pk)
                self._update_status(f"✅ Updated '{col_name}' to '{new_value}' for ID {db_old_pk}")


            update_auto_increment_if_needed(self.cursor, self.conn, self.current_table_name, pk_column)

        except Exception as e:
            print(f"❌ ERROR updating database: {e}")
            if column == pk_index:
                self.table_widget.item(row, pk_index).setText(str(db_old_pk))
            self._update_status("❌ Error occurred while updating.")

        finally:
            self.table_widget.blockSignals(False)
    def update_status_and_database(self, row_idx, new_status):  # MAIN
        try:
            primary_key_item = self.table_widget.item(row_idx, 0)
            if not primary_key_item:
                print(f"❌ ERROR: No primary key item found in row {row_idx}.")
                self._update_status(f"❌ No primary key item in row {row_idx}")
                return

            pk_value = primary_key_item.data(Qt.UserRole) or primary_key_item.text().strip()

            pk_column = fetch_primary_key_column(self.cursor, self.current_table_name)
            if not pk_column:
                print(f"❌ ERROR: No primary key column found for {self.current_table_name}")
                self._update_status(f"❌ No PK column for '{self.current_table_name}'")
                return

            success = update_status(
                cursor=self.cursor,
                conn=self.conn,
                table_name=self.current_table_name,
                pk_column=pk_column,
                pk_value=pk_value,
                new_status=new_status,

            )

            if success:
                print(f"✅ Status updated to '{new_status}' for {pk_column} = {pk_value}")
                self._update_status(f"✅ Status updated to '{new_status}' for {pk_value}")
                if new_status == "Completed":
                    end_date = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S")
                    print(end_date)
                    end_date_col = 13
                    self.table_widget.setItem(row_idx, end_date_col, QTableWidgetItem(end_date))
                    self._update_status(f"✅ Status updated to '{new_status}' for {pk_value}")
                    
                #self.refresh_table(suppress_status=True)
            else:
                print(f"❌ Failed to update status.")
                self._update_status(f"❌ Failed to update status for ID {pk_value}")

        except Exception as e:
            print(f"❌ ERROR in update_status_and_database: {e}")
            self._update_status(f"❌ Error: {str(e)}")

    def add_record_controller(self):#MAIN
        self.cursor.execute(f"DESCRIBE {self.current_table_name}")
        column_details = {col[0]: col[1] for col in self.cursor.fetchall()}

        add_record_dialog(
            table_name=self.current_table_name,
            columns=self.columns,
            column_types=column_details,
            db_insert_func=lambda t, c, v: insert_record(self.cursor, self.conn, t, c, v),
            refresh_callback=self.refresh_table,
            parent=self.dialog  # or main window
        )
    def handle_delete_record(self, table_name, table_widget, primary_key_column): #MAIN
        selected_items = table_widget.selectedItems()

        if not selected_items:
            show_info(table_widget, "⚠ No rows selected.", title="Warning")
            return

        selected_rows = list(set(item.row() for item in selected_items))
        selected_rows.sort()  # optional: keeps order consistent

        primary_keys = [
            table_widget.item(row, 0).text() for row in selected_rows
            if table_widget.item(row, 0)
        ]

        if not primary_keys:
            show_info(table_widget, "⚠ Could not extract record IDs.", title="Warning")
            return

        if len(primary_keys) == 1:
            record_id = primary_keys[0]
            if not confirm_deletion(table_widget, record_id):
                return
        else:
            if not confirm_deletion_bulk(table_widget, len(primary_keys)):
                return

        try:
            from DB.data_access import delete_multiple_records
            success, error = delete_multiple_records(
                self.conn, table_name, primary_key_column, primary_keys
            )

            if success:
                self.refresh_table(suppress_status=True)
                show_info(table_widget, f"🗑 Deleted {len(primary_keys)} record(s).", title="Delete Success")
                self._update_status(f"🗑 Deleted {len(primary_keys)} record(s) ID: {', '.join(primary_keys)}")
            else:
                show_info(table_widget, f"❌ Failed to delete: {error}", title="Delete Failed")
        except Exception as e:
            handle_db_error(e, f"Failed to delete record(s) from {table_name}")
            show_info(table_widget, f"❌ Error: {e}", title="Error") 
    def handle_print_record(self, table_name, table_widget, primary_key_column, cursor=None):
        selected_items = table_widget.selectedItems()
        cursor = self.cursor  # Use the cursor from the class instance if not passed

        if not selected_items:
            show_info(table_widget, "⚠ No rows selected.", title="Warning")
            return

        selected_rows = list(set(item.row() for item in selected_items))
        selected_rows.sort()  # Optional: keeps order consistent

        # Get the job_id from the selected row (assuming column 0 holds the job_id)
        job_id = table_widget.item(selected_rows[0], 0).text()  # Extract job_id from column 0

        # Get customer contact info using the job_id
        customer_contact = get_customer_contact(cursor, job_id)
        if customer_contact:
            customer_first_name, customer_sur_name, customer_phone, customer_email, customer_post_code, customer_door_number = customer_contact
        else:
            customer_first_name, customer_sur_name, customer_phone, customer_email = "", "", "", ""

        # Get the start_datetime from column 12 (or provide a default value if not available)
        start_datetime = (
            table_widget.item(selected_rows[0], 12).text()
            if table_widget.item(selected_rows[0], 12)
            else "N/A"
        )
        
        device_brand = (
            table_widget.item(selected_rows[0], 3).text()
            if table_widget.item(selected_rows[0], 4)
            else "N/A"
        )

        # Get the device_type from column 4 (or provide a default value if not available)
        device_type = (
            table_widget.item(selected_rows[0], 4).text()
            if table_widget.item(selected_rows[0], 4)
            else "N/A"
        )

        # Get the device_model from column 5 (or provide a default value if not available)
        device_model = (
            table_widget.item(selected_rows[0], 5).text()
            if table_widget.item(selected_rows[0], 5)
            else "N/A"
        )


        # Get extras from column 6
        extras = (
            table_widget.item(selected_rows[0], 6).text()
            if table_widget.item(selected_rows[0], 6)
            else "N/A"
        )

        # Get issue from column 7
        issue = (
            table_widget.item(selected_rows[0], 7).text()
            if table_widget.item(selected_rows[0], 7)
            else "N/A"
        )

        # Get data_save from column 8
        data_save = (
            "Yes" if table_widget.item(selected_rows[0], 8) and table_widget.item(selected_rows[0], 8).text() == "1" else "No"
        )

        # Get password from colummn 9
        password = (
            table_widget.item(selected_rows[0], 9).text()
            if table_widget.item(selected_rows[0], 9)
            else "N/A"
        )

        # Replace placeholders in the imported template with actual data
        content = JOB_REPORT_TEMPLATE.format(

            #Customer details
            job_id=job_id,
            customer_first_name=customer_first_name,
            customer_sur_name=customer_sur_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            customer_door_number = customer_door_number,
            customer_post_code=customer_post_code,
            #house_number=house_number,
            #post_code=post_code
            
            #Devicee details
            start_datetime=start_datetime,
            device_brand=device_brand,
            device_type=device_type,
            device_model=device_model,
            extras=extras,
            issue=issue,
            password=password,
            data_save=data_save  # Provide the missing placeholder value
        )

        # Prepare the document content using QTextDocument
        document = QTextDocument()
        document.setHtml(content)

        # Create a printer object and set its properties
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        printer.setOrientation(QPrinter.Portrait)
        printer.setOutputFormat(QPrinter.NativeFormat)

        # Directly print to the default printer without showing the print dialog
        document.print_(printer)

        self._update_status(f"🖨️ Printed job report for JobID: {job_id}")
   



#---------------------------------------------------------------------------------

    #============================================
    #           Utility /Internal Use
    #============================================

    def _update_status(self, message: str): #MAIN
        if hasattr(self, "status_bar"):
            now = datetime.now().strftime("%H:%M:%S")
            self.status_bar.setText(f"{now} : {message}.")
    def fetch_data(self, table_name, limit=50, offset=0): #MAIN
        return fetch_data(self.cursor, table_name, limit, offset)

#---------------------------------------------------------------------------------

    #============================================
    #           Event Handling
    #============================================

    def keyPressEvent(self, event): #MAIN
        keyPressEvent(self, event)  # Calls the one from ui.py
    def eventFilter(self, source, event): #MAIN
            return event_filter(self, source, event)

#---------------------------------------------------------------------------------  

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)

        # ✅ Global StyleSheet
        app.setStyleSheet("""
            QMessageBox { background-color: #2A2A2A; }
            QLabel { color: black; font-size: 14px; }
            QPushButton { background-color: #3A9EF5; color: white; padding: 10px; border-radius: 5px; }
        """)

        # ✅ Show splash screen once, at startup
        splashscreen = SplashScreen()
        splashscreen.show()
        app.processEvents()

        loading_thread = InitializationThread()
        loading_thread.progress.connect(splashscreen.update_progress)

        def start_main_app():
            splashscreen.close()
            app.processEvents()
            window = DatabaseApp()
            window.show()

        loading_thread.finished.connect(start_main_app)
        loading_thread.start()

        sys.exit(app.exec_())

    except Exception as e:
        error_message = f"Unexpected error: {e}\n{traceback.format_exc()}"
        log_error(error_message)

    
