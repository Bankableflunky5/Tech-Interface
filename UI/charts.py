import matplotlib.pyplot as plt


# 🎨 Centralized Color Palette
CHART_COLORS = {
    "primary": "#3A9EF5",
    "secondary": "#F39C12",
    "accent": "#9B59B6",
    "neutral": "#2C3E50",
    "light_bg": "#ecf0f1",
    "error": "#e74c3c"
}


def pie_chart(data):
    labels, values = zip(*data)
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    return fig

def bar_chart(data, xlabel="", ylabel="", rotate=False, horizontal=False, color="blue"):
    labels, values = zip(*data)
    fig, ax = plt.subplots()
    if horizontal:
        ax.barh(labels, values, color=color)
        ax.set_ylabel(ylabel)
        ax.set_xlabel(xlabel)
    else:
        ax.bar(labels, values, color=color)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
    if rotate:
        ax.tick_params(axis='x', rotation=45)
    return fig

def bar_chart1(data, xlabel="", ylabel="", rotate=False, horizontal=False, color="blue", title=None, title_pad=20):
    labels, values = zip(*data)
    wrapped_labels = ['\n'.join(label.split()) for label in labels]

    fig, ax = plt.subplots()
    if horizontal:
        ax.barh(wrapped_labels, values, color=color)
        ax.set_ylabel(ylabel)
        ax.set_xlabel(xlabel)
    else:
        ax.bar(wrapped_labels, values, color=color)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis='x', labelrotation=45 if rotate else 0)

    if title:
        ax.set_title(title, pad=title_pad)

    plt.tight_layout()
    return fig

def single_value_bar(label, value, ylabel="", color="blue"):
    fig, ax = plt.subplots()
    ax.bar([label], [value], color=color)
    ax.set_ylabel(ylabel)
    return fig

def line_chart(data, xlabel="", ylabel="", color="blue"):
    x, y = zip(*data)
    fig, ax = plt.subplots()
    ax.plot(x, y, marker="o", color=color)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis='x', rotation=45)
    return fig

def multi_line_weekday_plot(results):
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    weekly_job_counts = {}
    for week, day, count in results:
        if week not in weekly_job_counts:
            weekly_job_counts[week] = [0] * 6
        weekly_job_counts[week][day - 2] = count
    fig, ax = plt.subplots(figsize=(10, 6))
    for week, counts in weekly_job_counts.items():
        ax.plot(days_of_week, counts, marker="o", label=f"Week {week}")
    ax.set_xlabel("Day of the Week")
    ax.set_ylabel("Job Count")
    ax.legend(title="Weeks")
    return fig

def average_intake_bar(results):
    day_map = {2: "Monday", 3: "Tuesday", 4: "Wednesday", 5: "Thursday", 6: "Friday", 7: "Saturday"}
    days, counts = zip(*results)
    days = [day_map[d] for d in days]
    fig, ax = plt.subplots()
    ax.bar(days, counts, color="blue")
    ax.set_xlabel("Day of the Week")
    ax.set_ylabel("Average Job Count")
    ax.tick_params(axis='x', rotation=45)
    return fig

def start_time_distribution(minutes):
    if not minutes:
        return None
    fig, ax = plt.subplots(figsize=(10, 6))
    counts, bins, _ = ax.hist(minutes, bins=24, color='orange', edgecolor='black')
    ax.set_xlabel('Time of Day (minutes from midnight)')
    ax.set_ylabel('Number of Jobs')
    ax.set_title('Overall Job Start Time Distribution')
    ax.set_xticks(range(0, 1440, 60))
    ax.set_xticklabels([f'{h:02}:00' for h in range(24)])
    avg = sum(minutes) / len(minutes)
    hr, mn = int(avg // 60), int(avg % 60)
    ax.axvline(avg, color='red', linestyle='--', label=f'Avg: {hr:02}:{mn:02}')
    max_idx = counts.argmax()
    ax.text((bins[max_idx] + bins[max_idx+1]) / 2, counts[max_idx] + 1,
            f'Busiest: {int(bins[max_idx]//60):02}:{int(bins[max_idx]%60):02} - {int(bins[max_idx+1]//60):02}:{int(bins[max_idx+1]%60):02}',
            ha='center', color='blue', fontweight='bold')
    ax.text(avg, counts.max() * 0.85, f'Avg Time: {hr:02}:{mn:02}', color='red', ha='center', fontweight='bold')
    ax.legend()
    return fig
