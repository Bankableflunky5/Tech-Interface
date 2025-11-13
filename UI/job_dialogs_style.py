# job_ui_styles.py

JOB_DIALOG_STYLESHEET = """
QDialog {
    background-color: #1E1E1E;
    color: #EAEAEA;
    font-family: 'Segoe UI', 'Open Sans', 'Roboto', sans-serif;
    font-size: 14px;
}

QLabel {
    color: #4FC3F7;
    font-weight: bold;
    font-size: 14px;
    margin-bottom: 4px;
}

QLineEdit, QTextEdit, QComboBox, QDateEdit {
    background-color: #2A2A2A;
    color: white;
    border: 1px solid #4FC3F7;
    padding: 6px;
    border-radius: 6px;
}

QTextEdit {
    padding: 8px;
}

QPushButton {
    background-color: #3A3A3A;
    color: #EAEAEA;
    border: 1px solid #4FC3F7;
    padding: 8px 14px;
    border-radius: 6px;
}

QPushButton:hover {
    background-color: #4FC3F7;
    color: #1E1E1E;
}

QPushButton:disabled {
    background-color: #555;
    color: #888;
    border: 1px solid #444;
}

QPushButton#saveBtn {
    background-color: #4CAF50;
    color: white;
}

QPushButton#closeBtn {
    background-color: #D9534F;
    color: white;
}

QPushButton#deleteBtn {
    background-color: #D9534F;
}

QPushButton#deleteBtn:hover {
    background-color: #C9302C;
}

QTableWidget {
    background-color: #292A2D;
    color: white;
    gridline-color: #444;
    alternate-background-color: #222;
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

QCheckBox {
    color: #EAEAEA;
    font-weight: normal;
    padding-top: 4px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #2A2A2A;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #4FC3F7;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    background: none;
    height: 0px;
}
"""
