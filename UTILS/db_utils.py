from PyQt5.QtWidgets import QInputDialog, QFileDialog, QMessageBox
import mariadb
from UTILS.error_utils import log_error, handle_db_error
from PyQt5.QtWidgets import QInputDialog, QMessageBox, QFileDialog
import os
from datetime import datetime
from DB.data_access import connect_to_database

from PyQt5.QtWidgets import QInputDialog, QMessageBox, QLineEdit
import os
from FILE_OPS.config import (load_settings)
import os
from datetime import datetime
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import mariadb

import mariadb
import re

from PyQt5.QtWidgets import QInputDialog, QLineEdit

from UI.job_dialogs_style import JOB_DIALOG_STYLESHEET

def get_styled_database_name(parent_widget=None):
    dialog = QInputDialog(parent_widget)
    dialog.setWindowTitle("Database Name")
    dialog.setLabelText("Enter the name of the new database:")
    dialog.setInputMode(QInputDialog.TextInput)
    dialog.setTextValue("")
    dialog.setStyleSheet(JOB_DIALOG_STYLESHEET)   # Apply your custom stylesheet
    dialog.resize(400, 100)  # Optional: Resize for better appearance

    ok = dialog.exec_()
    db_name = dialog.textValue().strip()

    return db_name, bool(ok and db_name)

def show_custom_messagebox(icon, title, text, parent=None):
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    msg_box.setIcon(icon)
    msg_box.setStyleSheet(JOB_DIALOG_STYLESHEET)
    msg_box.exec_()

def sql_escape(value):
    """Escapes values to treat all string data as text in the backup."""
    if value is None:
        return 'NULL'
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        # Escape special characters (single quotes, backslashes, newlines, etc.)
        escaped = str(value).replace("\\", "\\\\").replace("'", "''").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        return f"'{escaped}'"

def backup_database(cursor, backup_directory=None, interactive=True):
    if not backup_directory:
        if interactive:
            backup_directory = QFileDialog.getExistingDirectory(None, "Select Backup Directory")
            if not backup_directory:
                return
        else:
            print("❌ No backup directory specified. Backup cancelled.")
            return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_directory, f"database_backup_{timestamp}.sql")

    try:
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write("-- MariaDB SQL Backup\n")
            f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")

            cursor.execute("SHOW TABLES;")
            tables = [table[0] for table in cursor.fetchall()]

            for table in tables:
                # Write CREATE TABLE statement
                cursor.execute(f"SHOW CREATE TABLE `{table}`;")
                create_table_statement = cursor.fetchone()[1]
                f.write(f"{create_table_statement};\n\n")

                # Write INSERT statements for data
                cursor.execute(f"SELECT * FROM `{table}`;")
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

                for row in rows:
                    # Escape each value to treat all as plain text
                    escaped_values = ", ".join(sql_escape(val) for val in row)
                    column_list = ", ".join(f"`{col}`" for col in columns)
                    f.write(f"INSERT INTO `{table}` ({column_list}) VALUES ({escaped_values});\n")

                f.write("\n")

            f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
            
            if interactive:
                    show_custom_messagebox(QMessageBox.Information, "Success", f"✅ Database backup saved to:\n{backup_file}")
            else:
                print(f"✅ Backup saved to {backup_file}")

    except Exception as e:
        if interactive:
            show_custom_messagebox(QMessageBox.Critical, "Error", f"❌ Failed to back up database: {e}")
        else:
            print(f"❌ Failed to back up database: {e}")

def change_db_password(_, conn):
    """Prompts for old & new DB password and updates it securely using fresh config from load_settings()."""

    # ⬇️ Load fresh settings
    settings = load_settings()

    host = settings.get("host", "localhost").strip()
    database_name = settings.get("database", "").strip()
    ssl_path = settings["ssl"]["cert_path"].strip()
    ssl_enabled = settings["ssl"]["enabled"]

    if not database_name:
        QMessageBox.critical(None, "Error", "Database configuration is missing or invalid!")
        return

    # Step 1: Ask for passwords
    old_password, ok = QInputDialog.getText(None, "Change Password", "Enter your current DB password:", QLineEdit.Password)
    if not ok or not old_password:
        QMessageBox.warning(None, "Warning", "Current password cannot be empty.")
        return

    new_password, ok = QInputDialog.getText(None, "Change Password", "Enter new password:", QLineEdit.Password)
    if not ok or not new_password:
        QMessageBox.warning(None, "Warning", "New password cannot be empty.")
        return

    confirm_password, ok = QInputDialog.getText(None, "Change Password", "Confirm new password:", QLineEdit.Password)
    if not ok or not confirm_password:
        QMessageBox.warning(None, "Warning", "Please confirm the new password.")
        return

    if new_password != confirm_password:
        QMessageBox.critical(None, "Error", "New passwords do not match. Please try again.")
        return

    if not conn:
        QMessageBox.critical(None, "Error", "Database connection is not established!")
        return

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT USER();")
        db_user = cursor.fetchone()[0]

        if '@' not in db_user:
            raise ValueError(f"Unexpected USER() format: '{db_user}'")

        db_username, db_host = db_user.split('@')
        print(f"🔐 Verifying credentials for {db_username}@{db_host}")
        print(f"📁 SSL enabled: {ssl_enabled}")
        print(f"📁 SSL path: {ssl_path}")

        if ssl_enabled and (not ssl_path or not os.path.isdir(ssl_path)):
            QMessageBox.critical(None, "SSL Error", f"Invalid or missing SSL directory:\n{ssl_path}")
            return

        # Reconnect with old password to verify
        try:
            temp_conn, temp_cursor = connect_to_database(
                username=db_username,
                password=old_password,
                host=host,
                database=database_name,
                ssl_enabled=ssl_enabled,
                ssl_path=ssl_path
            )
            temp_conn.close()
            print("✅ Password verification succeeded.")

        except Exception as err:
            print(f"❌ Connection failed with old password: {err}")
            QMessageBox.critical(None, "Error", f"Old password is incorrect.\n\n{err}")
            return

        # ✅ Correct: use parsed user + host, NOT db_user
        print(f"📝 Updating password for '{db_username}'@'{db_host}'")
        cursor.execute(f"SET PASSWORD = PASSWORD('{new_password}');")

        conn.commit()

        cursor.execute("FLUSH PRIVILEGES;")
        conn.commit()

        QMessageBox.information(None, "Success", "✅ Database password changed successfully!")

    except Exception as e:
        print(f"❌ Error during password update: {e}")
        QMessageBox.critical(None, "Error", f"Failed to change password: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()

def restore_database(conn, cursor, parent_widget=None):
    db_name, ok = get_styled_database_name(parent_widget)
    if not ok or not db_name:
        # Use QMessageBox with custom styles
        msg_box = QMessageBox(parent_widget)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Input Error")
        msg_box.setText("Database name cannot be empty.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setStyleSheet(JOB_DIALOG_STYLESHEET)  # Apply the stylesheet to the message box, not the button
        msg_box.exec_()
        return

    # Ask the user to select a backup file
    backup_file, _ = QFileDialog.getOpenFileName(
        parent_widget,
        "Select Backup File",
        "",
        "SQL Files (*.sql);;All Files (*)"
    )
    if not backup_file:
        # Use QMessageBox with custom styles
        msg_box = QMessageBox(parent_widget)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Input Error")
        msg_box.setText("No backup file selected.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setStyleSheet(JOB_DIALOG_STYLESHEET)  # Apply the stylesheet
        msg_box.exec_()
        return

    try:
        if not conn:
            raise Exception("No valid database connection found.")

        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name};")
        QMessageBox.information(parent_widget, "Success", f"Database '{db_name}' created successfully.")

        cursor.execute(f"USE {db_name};")

        # Open the backup file and execute its content
        with open(backup_file, "r") as file:
            sql_commands = file.read()

        # Execute each command in the SQL file
        for command in sql_commands.split(";"):
            command = command.strip()
            if command:
                try:
                    print(f"Executing: {command}")
                    cursor.execute(command)
                except mariadb.Error as e:
                    log_error(f"Failed to execute command: {command}. Error: {e}")
                    continue  # Skip the failed command

        conn.commit()
        # Use QMessageBox with custom styles for success
        msg_box = QMessageBox(parent_widget)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Success")
        msg_box.setText(f"Database restored successfully to '{db_name}'.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setStyleSheet(JOB_DIALOG_STYLESHEET)  # Apply the stylesheet
        msg_box.exec_()

    except mariadb.Error as e:
        handle_db_error(e, context=f"Failed to restore database '{db_name}'")
    except Exception as e:
        log_error(f"An unexpected error occurred: {e}")
        # Use QMessageBox with custom styles for error
        msg_box = QMessageBox(parent_widget)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(f"❌ Failed to restore database: {e}")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setStyleSheet(JOB_DIALOG_STYLESHEET)  # Apply the stylesheet
        msg_box.exec_()


