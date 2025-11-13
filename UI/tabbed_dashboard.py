from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget,
    QPushButton
)
from PyQt5.QtCore import Qt

from UI.ui import (
    create_scrollable_area,
    add_chart_to_layout,
    build_summary_label,
    show_error_label
)

from DB.data_access import (
    get_customer_acquisition,
    get_top_customers_by_jobs,
    get_most_frequent_device_brands,
    get_device_type_trends,
    get_job_status_distribution,
    get_avg_job_duration_by_technician,
    get_top_device_issues,
    get_technician_workload,
    get_avg_job_completion_time,
    get_walkin_volume,
    get_walkin_service_types,
    get_jobs_per_day_by_week,
    get_avg_jobs_per_day_by_week,
    get_job_start_times_in_minutes,
    get_database_summary_counts
)

from UI.charts import (
    pie_chart, bar_chart, line_chart, single_value_bar,
    multi_line_weekday_plot, average_intake_bar, start_time_distribution, bar_chart1
)


class TabbedDashboard(QDialog):
    def __init__(self, parent=None, cursor=None):
        super().__init__(parent)
        self.setStyleSheet("""
    * {
        font-family: 'Segoe UI', sans-serif;
    }
""")

        self.setWindowTitle("📊 Business Dashboard")
        self.setGeometry(200, 200, 1400, 900)
        self.setWindowState(Qt.WindowFullScreen)

        self.cursor = cursor
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.tabs.addTab(self.build_summary_tab(), "Summary")
        self.tabs.addTab(self.build_customers_tab(), "Customers")
        self.tabs.addTab(self.build_devices_tab(), "Devices")
        self.tabs.addTab(self.build_technicians_tab(), "Technicians")
        self.tabs.addTab(self.build_timing_tab(), "Timing")
        self.tabs.addTab(self.build_walkins_tab(), "Walk-Ins")

        layout.addWidget(self.tabs)

        # ➕ Add Exit Button
        exit_button = QPushButton("❌ Exit Dashboard")
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        exit_button.clicked.connect(self.close)

        # Add the button to layout
        layout.addWidget(exit_button, alignment=Qt.AlignRight)
        self.setLayout(layout)

    def build_tab(self, chart_blocks):
        scroll_area, layout = create_scrollable_area()

        try:
            for chart_title, data_func, plot_func in chart_blocks:
                data = data_func(self.cursor)
                if data:
                    fig = plot_func(data)
                    if fig:
                        add_chart_to_layout(fig, layout, chart_title)
        except Exception as e:
            layout.addWidget(show_error_label(str(e)))

        return scroll_area

    def build_summary_tab(self):
        scroll_area, layout = create_scrollable_area()
        try:
            customers, jobs, walkins = get_database_summary_counts(self.cursor)
            layout.addWidget(build_summary_label(customers, jobs, walkins))

            blocks = [
                ("Job Status Distribution", get_job_status_distribution,
                 lambda d: bar_chart(d, xlabel="Job Status", ylabel="Count")),
                 ("Customer Acquisition by Referral Source", get_customer_acquisition, pie_chart)
            ]
            for title, data_func, plot_func in blocks:
                data = data_func(self.cursor)
                if data:
                    fig = plot_func(data)
                    add_chart_to_layout(fig, layout, title)
        except Exception as e:
            layout.addWidget(show_error_label(str(e)))
        return scroll_area

    def build_customers_tab(self):
        return self.build_tab([
            
            ("Top Customers by Job Count", get_top_customers_by_jobs,
             lambda d: bar_chart(d, xlabel="Customer ID", ylabel="Job Count", rotate=True))
        ])

    def build_devices_tab(self):
        return self.build_tab([
            ("Most Frequent Device Brands", get_most_frequent_device_brands,
             lambda d: bar_chart(d, xlabel="Count", ylabel="Device Brand", horizontal=True, color="orange")),

            ("Most Common Device Types", get_device_type_trends,
             lambda d: bar_chart1(d, xlabel="Device Type", ylabel="Job Count", rotate=False, color="orange",
                              title=" ", title_pad=30)),

            ("Most Frequent Device Issues", get_top_device_issues,
             lambda d: bar_chart(d, xlabel="Count", ylabel="Issue", horizontal=True, color="blue"))
        ])

    def build_technicians_tab(self):
        return self.build_tab([
            ("Avg Job Duration by Technician", get_avg_job_duration_by_technician,
             lambda d: bar_chart(d, xlabel="Technician", ylabel="Avg Duration (Days)", rotate=True, color="purple")),

            ("Technician Workload", get_technician_workload,
             lambda d: bar_chart(d, xlabel="Technician", ylabel="Job Count", rotate=True, color="cyan")),

            ("Avg Job Completion Time", get_avg_job_completion_time,
             lambda d: single_value_bar("Avg Completion Time", d, ylabel="Avg Duration (Days)", color="red"))
        ])

    def build_timing_tab(self):
        return self.build_tab([
            ("Job Counts Per Day (Excl. Sunday) for Each Week", get_jobs_per_day_by_week, multi_line_weekday_plot),
            ("Avg Job Intake per Day of Week (Excl. Sunday)", get_avg_jobs_per_day_by_week, average_intake_bar),
            ("Overall Job Start Time Distribution", get_job_start_times_in_minutes, start_time_distribution),
            ("Walk-In Volume Over Time", get_walkin_volume,
                 lambda d: line_chart(d, xlabel="Date", ylabel="Walk-In Count", color="brown"))
        ])

    def build_walkins_tab(self):
        return self.build_tab([
            ("Most Common Walk-In Services", get_walkin_service_types,
             lambda d: bar_chart(d, xlabel="Count", ylabel="Service Type", horizontal=True, color="pink"))
        ])