
# ui/job_notes_editor.py

from datetime import datetime
from functools import partial

from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy, QFrame, QDateEdit
)

from DB.data_access import (
    get_cost_columns, get_costs_by_job, insert_cost, delete_cost,
    get_payments, insert_payment, delete_payment,
    get_customer_contact, get_communications, insert_communication, delete_communication,
    get_orders, insert_order, delete_order,
    get_editable_columns, get_job_data, update_job_data
)

from UI.job_dialogs_style import JOB_DIALOG_STYLESHEET

class JobNotesEditor(QDialog): #UI
    def __init__(self, job_id, job_data, save_callback, cursor, conn, parent=None):
        super().__init__(parent)
        self.job_id = job_id
        self.notes, self.status, self.technician = [x or "" for x in job_data]
        self.save_callback = save_callback

        # ✅ Add these
        self.cursor = cursor
        self.conn = conn

        self.setWindowTitle(f"📝 Edit Notes for Job {job_id}")
        self.setGeometry(100, 100, 500, 600)
        self.setStyleSheet(JOB_DIALOG_STYLESHEET)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # ======= STATUS =======
        status_label = QLabel("📌 Status:")
        self.status_box = QComboBox()
        self.status_box.addItems(["Waiting for parts", "In Progress", "Completed", "Picked Up", "Cancelled"])
        self.status_box.setCurrentText(self.status)
        self.status_box.setStyleSheet("""
            QComboBox {
                background-color: #2A2A2A;
                color: white;
                padding: 6px;
                border: 1px solid #3A9EF5;
                border-radius: 5px;
            }
        """)
        layout.addWidget(status_label)
        layout.addWidget(self.status_box)

        # ======= TECHNICIAN =======
        tech_label = QLabel("👨‍🔧 Technician:")
        self.tech_input = QLineEdit(self.technician)
        self.tech_input.setStyleSheet("""
            QLineEdit {
                background-color: #2A2A2A;
                color: white;
                padding: 6px;
                border: 1px solid #3A9EF5;
                border-radius: 5px;
            }
        """)
        layout.addWidget(tech_label)
        layout.addWidget(self.tech_input)

        # ======= NOTES =======
        notes_label = QLabel("📝 Edit Notes:")
        self.notes_text = QTextEdit()
        self.notes_text.setPlainText(self.notes or "")
        self.notes_text.setStyleSheet("""
            QTextEdit {
                background-color: #2A2A2A;
                color: white;
                padding: 8px;
                border: 1px solid #3A9EF5;
                border-radius: 5px;
            }
        """)
        self.notes_text.setMinimumHeight(120)
        layout.addWidget(notes_label)
        layout.addWidget(self.notes_text)


        # ======= SAVE / CANCEL =======
        save_cancel_row = QHBoxLayout()
        save_cancel_row.setSpacing(10)

        save_btn = QPushButton("💾 Save Changes")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold; border-radius: 5px;")
        save_btn.clicked.connect(self.save_notes)
        save_cancel_row.addWidget(save_btn)

        close_btn = QPushButton("❌ Close")
        close_btn.setStyleSheet("background-color: #D9534F; color: white; padding: 8px; font-weight: bold; border-radius: 5px;")
        close_btn.clicked.connect(self.reject)
        save_cancel_row.addWidget(close_btn)

        layout.addLayout(save_cancel_row)

        # ======= SEPARATOR =======
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #444;")
        layout.addWidget(line)

        # ======= NAV BUTTONS =======
        nav_label = QLabel("🔍 View Related Info:")
        nav_label.setStyleSheet("color: #3A9EF5; font-weight: bold; margin-top: 10px;")
        layout.addWidget(nav_label)

        nav_button_row = QHBoxLayout()
        nav_button_row.setSpacing(8)

        buttons = [
            ("💰 Costs", CostsDialog),
            ("💳 Payments", PaymentsDialog),
            ("📞 Communications", CommunicationsDialog),
            ("📦 Orders", OrdersDialog),
            ("🛠 Job Details", JobDetailsDialog),
        ]

        for label, dialog_cls in buttons:
            btn = QPushButton(label)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3A3A3A;
                    color: white;
                    padding: 6px 12px;
                    border: 1px solid #3A9EF5;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #2A2A2A;
                }
            """)
            btn.clicked.connect(lambda _, cls=dialog_cls: self.open_dialog(cls, self.job_id))
            nav_button_row.addWidget(btn)

        layout.addLayout(nav_button_row)
        self.setLayout(layout)

    def save_notes(self):
        new_notes = self.notes_text.toPlainText()
        new_status = self.status_box.currentText().strip()
        new_technician = self.tech_input.text().strip()

        if (new_notes == self.notes and new_status == self.status and new_technician == self.technician):
            QMessageBox.information(self, "ℹ No Changes", "No changes were made.")
            return

        end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if new_status == "Completed" else None

        try:
            self.save_callback(self.job_id, new_notes, new_status, new_technician, end_date)
            QMessageBox.information(self, "✅ Success", f"Job {self.job_id} updated.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Could not save changes: {e}")

    def open_dialog(self, dialog_class, *args):
        dialog = dialog_class(*args, self.cursor, self.conn)
        dialog.exec_()

class CostsDialog(QDialog): #UI
    def __init__(self, job_id, cursor, conn, parent=None):
        super().__init__(parent)
        self.setStyleSheet(JOB_DIALOG_STYLESHEET)
        self.job_id = job_id
        self.cursor = cursor
        self.conn = conn

        self.setWindowTitle(f"💰 Costs for Job {job_id}")
        self.setGeometry(600, 100, 700, 500)

        self.columns = get_cost_columns(self.cursor)
        self.display_columns = [c for c in self.columns if c.lower() not in ['costid', 'jobid']]

        self.init_ui()
        self.load_costs()

    def init_ui(self):
        self.layout = QVBoxLayout()

        title = QLabel("💰 Job Costs")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3A9EF5;")
        title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.display_columns) + 2)
        self.table.setHorizontalHeaderLabels(self.display_columns + ["➕ Add to Orders", "🗑 Delete"])

        # ✅ Stretch last column (good!)
        self.table.horizontalHeader().setStretchLastSection(True)

        # ✅ Resize columns to fit content (optional depending on layout)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # ✅ Remove vertical header index to eliminate left-edge white space
        self.table.verticalHeader().setVisible(False)

        # ✅ Remove frame — this is often the reason for "white edge"
        self.table.setFrameStyle(QFrame.NoFrame)

        # ✅ Make background fully match your QDialog (dark theme)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #292A2D;
                color: white;
                gridline-color: #444;
                border: none;
            }
        """)

        # ✅ Add alternating row colors (optional polish)
        self.table.setAlternatingRowColors(True)

        # ✅ Add it to layout
        self.layout.addWidget(self.table)


        self.total_label = QLabel("💰 Total Cost: £0.00")
        self.total_label.setAlignment(Qt.AlignRight)
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #3A9EF5;")
        self.layout.addWidget(self.total_label)

        add_btn = QPushButton("➕ Add Cost")
        add_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        add_btn.clicked.connect(self.open_add_dialog)
        self.layout.addWidget(add_btn)

        self.setLayout(self.layout)

    def load_costs(self):
        self.table.clearContents()
        data = get_costs_by_job(self.cursor, self.job_id, self.columns)
        self.table.setRowCount(len(data))

        total = 0
        for row_idx, row_data in enumerate(data):
            cost_id = row_data[0]

            for col_idx, col_name in enumerate(self.display_columns):
                value = row_data[self.columns.index(col_name)]
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
                if col_name.lower() == "amount":
                    try:
                        total += float(value)
                    except:
                        pass

            # Add to Orders Button (placeholder)
            add_btn = QPushButton("➕ Add to Orders")
            part_description = row_data[self.columns.index("Description")]
            add_btn.clicked.connect(partial(self.open_add_to_orders, part_description))
            self.table.setCellWidget(row_idx, len(self.display_columns), add_btn)


            # Delete Button
            del_btn = QPushButton("🗑")
            del_btn.clicked.connect(partial(self.confirm_delete, cost_id))
            self.table.setCellWidget(row_idx, len(self.display_columns)+1, del_btn)

        self.total_label.setText(f"💰 Total Cost: £{total:.2f}")

    def confirm_delete(self, cost_id):
        confirm = QMessageBox.question(self, "Delete", "Delete this cost?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            delete_cost(self.cursor, cost_id)
            self.conn.commit()
            self.load_costs()

    def open_add_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("➕ Add Cost")
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        title = QLabel("Add a New Cost")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #3A9EF5;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        cost_type = QComboBox()
        cost_type.addItems(["Parts", "Labor", "Shipping", "Miscellaneous"])

        amount = QLineEdit()
        amount.setPlaceholderText("Amount in £")

        description = QTextEdit()
        description.setPlaceholderText("Description")
        description.setMinimumHeight(60)

        form_fields = [
            ("Cost Type:", cost_type),
            ("Amount (£):", amount),
            ("Description:", description),
        ]

        for label_text, widget in form_fields:
            label = QLabel(label_text)
            layout.addWidget(label)
            layout.addWidget(widget)

        submit_btn = QPushButton("✅ Add Cost")
        submit_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        layout.addWidget(submit_btn)

        dialog.setLayout(layout)

        def submit():
            try:
                amt = float(amount.text().strip())
                desc = description.toPlainText().strip()
                if not desc:
                    raise ValueError("Description required")
                insert_cost(self.cursor, self.job_id, cost_type.currentText(), amt, desc)
                self.conn.commit()
                dialog.close()
                self.load_costs()
            except Exception as e:
                QMessageBox.warning(dialog, "Error", str(e))

        submit_btn.clicked.connect(submit)
        dialog.exec_()

    def open_add_to_orders(self, part_description):
        dialog = AddToOrdersDialog(self.job_id, part_description, self.cursor, self.conn)
        dialog.exec_()

class AddToOrdersDialog(QDialog): #UI
    def __init__(self, job_id, part_description, cursor, conn, parent=None):
        super().__init__(parent)
        self.job_id = job_id
        self.part_description = part_description
        self.cursor = cursor
        self.conn = conn

        self.setWindowTitle("📦 Add Part to Orders")
        self.setMinimumWidth(350)

        # ✅ Dark theme styling
        self.setStyleSheet(JOB_DIALOG_STYLESHEET)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Title
        title = QLabel(f"Add to Orders: {self.part_description}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #3A9EF5;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Input field
        cost_label = QLabel("Enter Total Cost (£):")
        self.total_cost_entry = QLineEdit()
        self.total_cost_entry.setPlaceholderText("e.g., 30.00")

        layout.addWidget(cost_label)
        layout.addWidget(self.total_cost_entry)

        # Submit button
        submit_btn = QPushButton("✅ Add to Orders")
        submit_btn.clicked.connect(self.submit_order)
        layout.addWidget(submit_btn)

        self.setLayout(layout)

    def submit_order(self):
        total_cost = self.total_cost_entry.text().strip()

        if not total_cost:
            QMessageBox.warning(self, "⚠ Input Error", "Total cost must be entered.")
            return

        try:
            total_cost = float(total_cost)
            quantity = 1

            self.cursor.execute(
                "INSERT INTO orders (JobID, OrderDate, Description, Quantity, TotalCost) "
                "VALUES (%s, NOW(), %s, %s, %s)",
                (self.job_id, self.part_description, quantity, total_cost)
            )
            self.conn.commit()

            QMessageBox.information(self, "✅ Success", "Part added to orders successfully.")
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "⚠ Input Error", "Total cost must be a valid number.")

class PaymentsDialog(QDialog): #IMPROVE FURTHER UI
    def __init__(self, job_id, cursor, conn, parent=None):
        super().__init__(parent)
        self.job_id = job_id
        self.cursor = cursor
        self.conn = conn

        self.setWindowTitle(f"💳 Payments for Job {job_id}")
        self.setGeometry(600, 100, 600, 500)

        self.setStyleSheet(JOB_DIALOG_STYLESHEET)
        self.init_ui()
        self.load_payments()

    def init_ui(self):
        self.layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Payment ID", "Amount", "Payment Type", "Date", "🗑 Delete"])

        # === Stretch & Resize Columns ===
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # === Hide vertical index column (left edge) ===
        self.table.verticalHeader().setVisible(False)

        # === Remove borders (prevents white lines) ===
        self.table.setFrameStyle(QFrame.NoFrame)

        # === Visual Enhancements ===
        self.table.setAlternatingRowColors(True)

        # === Matching Style ===
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #292A2D;
                color: white;
                gridline-color: #444;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #3A9EF5;
                color: black;
            }
        """)

        # === Add to layout ===
        self.layout.addWidget(self.table)


        self.total_label = QLabel("💰 Total Payments: £0.00")
        self.total_label.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.total_label)

        add_btn = QPushButton("➕ Add Payment")
        add_btn.clicked.connect(self.open_add_payment_dialog)
        self.layout.addWidget(add_btn)

        self.setLayout(self.layout)

    def load_payments(self):
        self.table.clearContents()
        payments = get_payments(self.cursor, self.job_id)
        self.table.setRowCount(len(payments))

        total = 0
        for row_idx, (payment_id, amount, payment_type, payment_date) in enumerate(payments):
            total += float(amount)

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(payment_id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(f"£{amount:.2f}"))
            self.table.setItem(row_idx, 2, QTableWidgetItem(payment_type))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(payment_date)))

            del_btn = QPushButton("🗑")
            del_btn.clicked.connect(partial(self.confirm_delete, payment_id))
            self.table.setCellWidget(row_idx, 4, del_btn)

        self.total_label.setText(f"💰 Total Payments: £{total:.2f}")

    def confirm_delete(self, payment_id):
        confirm = QMessageBox.question(self, "Delete", "Delete this payment?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            delete_payment(self.cursor, payment_id)
            self.conn.commit()
            self.load_payments()

    def open_add_payment_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("➕ Add Payment")
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Amount
        amount_label = QLabel("Amount (£):")
        amount_entry = QLineEdit()
        amount_entry.setPlaceholderText("e.g., 100.00")

        # Payment type
        type_label = QLabel("Payment Type:")
        type_dropdown = QComboBox()
        type_dropdown.addItems(["Card", "Cash", "Bank Transfer"])

        # Date
        date_label = QLabel("Date:")
        date_entry = QDateEdit()
        date_entry.setDate(QDate.currentDate())
        date_entry.setCalendarPopup(True)

        layout.addWidget(amount_label)
        layout.addWidget(amount_entry)
        layout.addWidget(type_label)
        layout.addWidget(type_dropdown)
        layout.addWidget(date_label)
        layout.addWidget(date_entry)

        # Submit
        add_button = QPushButton("✅ Add Payment")
        def submit():
            try:
                amount = float(amount_entry.text().strip())
                payment_type = type_dropdown.currentText()
                payment_date = date_entry.date().toString("yyyy-MM-dd")

                insert_payment(self.cursor, self.job_id, amount, payment_type, payment_date)
                self.conn.commit()
                dialog.accept()
                self.load_payments()
            except ValueError:
                QMessageBox.warning(dialog, "⚠ Error", "Amount must be a number.")

        add_button.clicked.connect(submit)
        layout.addWidget(add_button)

        dialog.setLayout(layout)
        dialog.exec_()

class CommunicationsDialog(QDialog): #fix UI
    def __init__(self, job_id, cursor, conn, parent=None):
        super().__init__(parent)
        self.job_id = job_id
        self.cursor = cursor
        self.conn = conn
        self.setStyleSheet(JOB_DIALOG_STYLESHEET)
        self.setWindowTitle(f"📞 Communications for Job {job_id}")
        self.setGeometry(600, 100, 700, 500)

        self.init_ui()
        self.load_communications()

    def init_ui(self):
        self.layout = QVBoxLayout()

        # --- Customer Info ---
        contact = get_customer_contact(self.cursor, self.job_id)
        contact = contact or ("N/A", "N/A", "N/A", "N/A")
        fields = ["First Name", "Surname", "📞 Phone", "✉ Email"]

        self.customer_table = QTableWidget(4, 2)
        self.customer_table.setHorizontalHeaderLabels(["Field", "Value"])

        # === Set data ===
        for i, (field, value) in enumerate(zip(fields, contact)):
            self.customer_table.setItem(i, 0, QTableWidgetItem(field))
            self.customer_table.setItem(i, 1, QTableWidgetItem(value))

        # === Behavior ===
        self.customer_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.customer_table.setSelectionMode(QTableWidget.NoSelection)
        self.customer_table.setFocusPolicy(Qt.NoFocus)

        # === Headers ===
        self.customer_table.horizontalHeader().setStretchLastSection(True)
        self.customer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.customer_table.verticalHeader().setVisible(False)  # ✅ Removes left strip
        self.customer_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # === Style ===
        self.customer_table.setFrameStyle(QFrame.NoFrame)
        self.customer_table.setStyleSheet("""
            QTableWidget {
                background-color: #292A2D;
                color: white;
                gridline-color: #444;
                border: none;
            }
            QHeaderView::section {
                background-color: #3C4043;
                color: #E8EAED;
                font-weight: bold;
                padding: 6px;
            }
        """)

        # === Add to layout ===
        self.layout.addWidget(self.customer_table)


        # --- Communications Table ---
        self.comms_table = QTableWidget()
        self.comms_table.setColumnCount(5)
        self.comms_table.setHorizontalHeaderLabels(["ID", "Date", "Type", "Message", "🗑 Delete"])

        # === Column Sizing ===
        self.comms_table.horizontalHeader().setStretchLastSection(True)
        self.comms_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.comms_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # === Hide vertical index (left edge) ===
        self.comms_table.verticalHeader().setVisible(False)

        # === No frame ===
        self.comms_table.setFrameStyle(QFrame.NoFrame)

        # === Row visuals ===
        self.comms_table.setAlternatingRowColors(True)

        # === Style to match theme ===
        self.comms_table.setStyleSheet("""
            QTableWidget {
                background-color: #292A2D;
                color: white;
                gridline-color: #444;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #3A9EF5;
                color: black;
            }
            QHeaderView::section {
                background-color: #3C4043;
                color: #E8EAED;
                font-weight: bold;
                padding: 6px;
            }
        """)

        # === Add to layout ===
        self.layout.addWidget(self.comms_table)


        # --- Bottom Buttons ---
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Add Communication")
        add_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; border-radius: 5px;")
        add_btn.clicked.connect(self.open_add_dialog)
        btn_layout.addWidget(add_btn)

        close_btn = QPushButton("❌ Close")
        close_btn.setStyleSheet("background-color: #D9534F; color: white; padding: 8px; border-radius: 5px;")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        self.layout.addLayout(btn_layout)
        self.setLayout(self.layout)

    def load_communications(self):
        self.comms_table.clearContents()
        comms = get_communications(self.cursor, self.job_id)
        self.comms_table.setRowCount(len(comms))

        for row_idx, (comm_id, date_time, comm_type, message) in enumerate(comms):
            self.comms_table.setItem(row_idx, 0, QTableWidgetItem(str(comm_id)))
            self.comms_table.setItem(row_idx, 1, QTableWidgetItem(str(date_time)))
            self.comms_table.setItem(row_idx, 2, QTableWidgetItem(comm_type))
            self.comms_table.setItem(row_idx, 3, QTableWidgetItem(message))

            del_btn = QPushButton("🗑")
            del_btn.clicked.connect(partial(self.confirm_delete, comm_id))
            self.comms_table.setCellWidget(row_idx, 4, del_btn)

        self.comms_table.resizeRowsToContents()

    def confirm_delete(self, comm_id):
        confirm_box = QMessageBox(self)
        confirm_box.setWindowTitle("🗑 Confirm Deletion")
        confirm_box.setText("Are you sure you want to delete this communication?")
        confirm_box.setIcon(QMessageBox.Warning)

        confirm_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm_box.setDefaultButton(QMessageBox.No)

        # Optional: Custom stylesheet
        confirm_box.setStyleSheet("""
            QMessageBox {
                background-color: #2A2A2A;
                color: white;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3A3A3A;
                color: white;
                padding: 6px 12px;
                border: 1px solid #4FC3F7;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #444;
            }
            QLabel {
                color: #4FC3F7;
                font-weight: bold;
            }
        """)

        if confirm_box.exec_() == QMessageBox.Yes:
            delete_communication(self.cursor, comm_id)
            self.conn.commit()
            self.load_communications()

    def open_add_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("➕ Add Communication")
        layout = QVBoxLayout()

        type_dropdown = QComboBox()
        type_dropdown.addItems(["Email", "Call", "SMS", "In-Person", "Other"])
        layout.addWidget(QLabel("Communication Type:"))
        layout.addWidget(type_dropdown)

        message_entry = QTextEdit()
        message_entry.setPlaceholderText("Enter message")
        layout.addWidget(QLabel("Message:"))
        layout.addWidget(message_entry)

        submit_btn = QPushButton("✅ Add Communication")

        def submit():
            comm_type = type_dropdown.currentText().strip()
            message = message_entry.toPlainText().strip()
            if not comm_type or not message:
                QMessageBox.warning(dialog, "⚠ Input Error", "All fields must be filled.")
                return

            insert_communication(self.cursor, self.job_id, comm_type, message)
            self.conn.commit()
            dialog.accept()
            self.load_communications()

        submit_btn.clicked.connect(submit)
        layout.addWidget(submit_btn)

        dialog.setLayout(layout)
        dialog.exec_()

class OrdersDialog(QDialog): #PERFECT
    def __init__(self, job_id, cursor, conn, parent=None):
        super().__init__(parent)
        self.job_id = job_id
        self.cursor = cursor
        self.conn = conn

        self.setWindowTitle(f"📦 Orders for Job {job_id}")
        self.setMinimumSize(700, 520)

        self.setStyleSheet(JOB_DIALOG_STYLESHEET)
        self.init_ui()
        self.load_orders()

    def init_ui(self):
        self.layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Order ID", "Order Date", "Description", "Quantity", "Total Cost (£)", "🗑"
        ])

        # === Sizing ===
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # === Hide vertical row index (left edge strip) ===
        self.table.verticalHeader().setVisible(False)

        # === Flat border (eliminates white edge/frame) ===
        self.table.setFrameStyle(QFrame.NoFrame)

        # === Styling (matches your theme) ===
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #292A2D;
                color: white;
                gridline-color: #444;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #3A9EF5;
                color: black;
            }
        """)

        # === Add to layout ===
        self.layout.addWidget(self.table)


        add_btn = QPushButton("➕ Add Order")
        add_btn.clicked.connect(self.open_add_order_dialog)
        self.layout.addWidget(add_btn)

        self.setLayout(self.layout)

    def load_orders(self):
        self.table.clearContents()
        orders = get_orders(self.cursor, self.job_id)
        self.table.setRowCount(len(orders))

        for row_idx, (order_id, date, desc, qty, total) in enumerate(orders):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(order_id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(date)))
            self.table.setItem(row_idx, 2, QTableWidgetItem(desc))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(qty)))

            total_str = f"£{total:.2f}" if total is not None else "£0.00"
            self.table.setItem(row_idx, 4, QTableWidgetItem(total_str))

            del_btn = QPushButton("🗑")
            del_btn.setObjectName("deleteBtn")
            del_btn.clicked.connect(partial(self.confirm_delete, order_id))
            self.table.setCellWidget(row_idx, 5, del_btn)


    def confirm_delete(self, order_id):
        confirm = QMessageBox.question(self, "Delete", "Delete this order?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            delete_order(self.cursor, order_id)
            self.conn.commit()
            self.load_orders()

    def open_add_order_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("➕ Add Order")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout()

        desc_input = QLineEdit()
        desc_input.setPlaceholderText("e.g., Hard Drive, RAM Module")
        qty_input = QLineEdit()
        qty_input.setPlaceholderText("Quantity")
        cost_input = QLineEdit()
        cost_input.setPlaceholderText("Total Cost (£)")

        layout.addSpacing(10)
        layout.addWidget(QLabel("Part Description:"))
        layout.addWidget(desc_input)
        layout.addSpacing(6)

        layout.addWidget(QLabel("Quantity:"))
        layout.addWidget(qty_input)
        layout.addSpacing(6)

        layout.addWidget(QLabel("Total Cost:"))
        layout.addWidget(cost_input)
        layout.addSpacing(10)


        submit_btn = QPushButton("✅ Add Order")

        def submit():
            desc = desc_input.text().strip()
            qty = qty_input.text().strip()
            cost = cost_input.text().strip()

            if not desc or not qty or not cost:
                QMessageBox.warning(dialog, "⚠ Input Error", "All fields must be filled.")
                return

            try:
                qty = int(qty)
                cost = float(cost)
                insert_order(self.cursor, self.job_id, desc, qty, cost)
                self.conn.commit()
                dialog.accept()
                self.load_orders()
            except ValueError:
                QMessageBox.warning(dialog, "⚠ Input Error", "Quantity must be an integer and cost a valid number.")

        layout.addWidget(submit_btn)
        dialog.setLayout(layout)
        dialog.exec_()

class JobDetailsDialog(QDialog): #MINOR
    def __init__(self, job_id, cursor, conn, parent=None):
        super().__init__(parent)
        self.job_id = job_id
        self.cursor = cursor
        self.conn = conn

        self.setWindowTitle(f"🛠 Edit Job Details - Job {job_id}")
        self.setMinimumSize(700, 520)

        self.setStyleSheet(JOB_DIALOG_STYLESHEET)
        self.columns = get_editable_columns(self.cursor)
        self.original_data = get_job_data(self.cursor, self.job_id, self.columns)

        if not self.original_data:
            QMessageBox.critical(self, "❌ Error", "Job not found.")
            self.close()
            return

        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.input_fields = {}

        for idx, col in enumerate(self.columns):
            field_label = QLabel(f"{col}:")
            self.layout.addWidget(field_label)

            if col.lower() == "issue":
                field = QTextEdit()
                field.setMinimumHeight(80)
                field.setText(str(self.original_data[idx]))
            elif col.lower() == "datasave":
                field = QCheckBox()
                field.setChecked(bool(self.original_data[idx]))
            else:
                field = QLineEdit()
                field.setText(str(self.original_data[idx]))

            self.input_fields[col] = field
            self.layout.addWidget(field)

        # --- Save / Cancel Buttons ---
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Save Changes")
        save_btn.clicked.connect(self.save_changes)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)

        self.layout.addSpacing(10)
        self.layout.addLayout(btn_layout)
        self.setLayout(self.layout)

    def save_changes(self):
        new_data = []

        for col in self.columns:
            widget = self.input_fields[col]
            if isinstance(widget, QLineEdit):
                value = widget.text().strip()
            elif isinstance(widget, QTextEdit):
                value = widget.toPlainText().strip()
            elif isinstance(widget, QCheckBox):
                value = int(widget.isChecked())
            else:
                value = None
            new_data.append(value)

        if tuple(new_data) == self.original_data:
            QMessageBox.information(self, "ℹ No Changes", "No changes were made.")
            self.close()
            return

        try:
            update_job_data(self.cursor, self.job_id, self.columns, new_data)
            self.conn.commit()
            QMessageBox.information(self, "✅ Success", "Job details updated.")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Update failed: {e}")



