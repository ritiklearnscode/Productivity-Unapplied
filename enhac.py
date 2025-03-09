import streamlit as st
import pandas as pd
import datetime
import sqlite3

# Initialize Database
def init_db():
    conn = sqlite3.connect("productivity.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    account_id TEXT,
                    task_type TEXT,
                    count INTEGER,
                    time_per_task REAL,
                    total_time REAL
                )''')
    conn.commit()
    conn.close()

# Fetch data for dashboard with optional filters
def fetch_tasks(start_date=None, end_date=None, account_id=None):
    conn = sqlite3.connect("productivity.db")
    query = '''SELECT date, account_id, task_type, 
                      SUM(count) as total_count, 
                      SUM(total_time) as total_time 
               FROM tasks'''
    params = []
    
    conditions = []
    if start_date:
        conditions.append("date >= ?")
        params.append(start_date.strftime("%Y-%m-%d"))
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date.strftime("%Y-%m-%d"))
    if account_id:
        conditions.append("account_id = ?")
        params.append(account_id)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " GROUP BY date, account_id, task_type ORDER BY date"
    
    df = pd.read_sql(query, conn, params=params if params else None)
    conn.close()
    return df

# Initialize database
init_db()

# Streamlit page configuration
st.set_page_config(
    page_title="Productivity Tracker",
    layout="wide",
    page_icon="🚀"
)

# Custom CSS for refined UI/UX
st.markdown("""
    <style>
    /* Overall body settings for a dark theme */
    .main {
        background-color: #1f1f1f;
        color: #e5e5e5;
    }

    /* App Title */
    .css-1v0mbdj h1 {
        color: #fff;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    /* Input widgets (text, number, date) */
    .stTextInput, .stNumberInput, .stDateInput {
        background-color: #2b2b2b !important;
        border-radius: 8px;
        border: 1px solid #444 !important;
        color: #e5e5e5 !important;
        margin-bottom: 0.5rem !important;
    }
    .stTextInput>label, .stNumberInput>label, .stDateInput>label {
        font-weight: 500;
        margin-bottom: 0.3rem;
        color: #ccc;
    }
    .stNumberInput>div>div>input, .stTextInput>div>input, .stDateInput>div>input {
        color: #e5e5e5 !important;
    }

    /* Buttons */
    .stButton button {
        background-color: #f55b5b !important;
        color: #fff !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: background-color 0.3s ease !important;
    }
    .stButton button:hover {
        background-color: #ff4141 !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        font-size: 1rem;
        color: #e5e5e5;
        font-weight: 600;
    }

    /* Section headers */
    h2, h3, h4 {
        color: #f0f0f0;
        font-weight: 600;
    }

    /* Metric boxes */
    .metric-box {
        padding: 20px; 
        background-color: #2b2b2b; 
        border-radius: 10px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        margin-bottom: 10px;
        text-align: center;
        transition: transform 0.2s;
    }
    .metric-box:hover {
        transform: translateY(-2px);
    }
    .metric-box h3 {
        margin: 0;
        color: #ddd;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    .metric-box h1 {
        margin: 0;
        color: #fff;
        font-size: 2.2rem;
        font-weight: 700;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #242424 !important;
    }
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4 {
        color: #fff;
    }

    /* Dataframe styling */
    .stDataFrame, .stTable {
        background-color: #2b2b2b;
        border: 1px solid #444;
        border-radius: 8px;
    }

    /* Force chart backgrounds to dark */
    .element-container {
        background-color: transparent !important;
    }
    .stChartFrame>div {
        background: #2b2b2b !important;
        border-radius: 8px;
        padding: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Main App Title
st.title("🚀 Productivity Tracker")

# --- Log New Tasks Section ---
with st.expander("📥 Log New Tasks", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Select Date", datetime.date.today())
    with col2:
        account_id = st.text_input("Account ID", help="Required field").strip()

    st.markdown("---")
    st.subheader("Task Details")
    
    # Add new entry for "No Activity/Future Review/Account Review" with 0 AHT
    task_types = {
        "Calls": 10.67, 
        "Emails": 3, 
        "Applications": 5,
        "EP Cases": 5, 
        "TT Cases": 5, 
        "Push Refund TT": 5,
        "No Activity/Future Review/Account Review": 0
    }

    entries = []
    cols = st.columns(3)
    # Dynamically create number inputs for each task type
    for i, (task, time_per_task) in enumerate(task_types.items()):
        with cols[i % 3]:
            count = st.number_input(
                f"{task} Count",
                min_value=0,
                step=1,
                key=task,
                help=f"Time per task: {time_per_task} minutes"
            )
            if count > 0:
                total_time = count * time_per_task  # 0 for No Activity tasks
                entries.append((
                    date.isoformat(),
                    account_id,
                    task,
                    count,
                    time_per_task,
                    total_time
                ))

    if st.button("💾 Save Tasks"):
        if not account_id:
            st.error("🔴 Please enter an Account ID")
        elif not entries:
            st.error("🔴 Please add at least one task")
        else:
            conn = sqlite3.connect("productivity.db")
            try:
                conn.executemany('''INSERT INTO tasks 
                                (date, account_id, task_type, count, time_per_task, total_time)
                                VALUES (?, ?, ?, ?, ?, ?)''',
                                entries)
                conn.commit()
                st.success(f"✅ Successfully logged {len(entries)} tasks!")
            except sqlite3.Error as e:
                st.error(f"🔴 Database error: {str(e)}")
            finally:
                conn.close()

# --- Performance Dashboard Section ---
st.markdown("---")
st.header("📊 Performance Dashboard")

# Filters
with st.expander("🔍 Filter Data", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=7))
    with col2:
        end_date = st.date_input("End Date", datetime.date.today())
    with col3:
        account_filter = st.text_input("Filter by Account ID")

# Fetch filtered data
df = fetch_tasks(
    start_date=start_date,
    end_date=end_date,
    account_id=account_filter if account_filter else None
)

if not df.empty:
    # Calculate today's summary (based on the selected date in Log section)
    conn = sqlite3.connect("productivity.db")
    today_tasks = pd.read_sql("SELECT * FROM tasks WHERE date = ?", conn, params=(date.isoformat(),))
    conn.close()
    if not today_tasks.empty:
        total_time_today = today_tasks['total_time'].sum()
        productivity_today = round(total_time_today / 480 * 100, 1)
        unique_accounts_today = today_tasks['account_id'].nunique()
    else:
        total_time_today = 0
        productivity_today = 0
        unique_accounts_today = 0

    # Key Metrics
    st.subheader("📈 Key Metrics")
    kcol1, kcol2 = st.columns(2)
    with kcol1:
        st.markdown(f'''
            <div class="metric-box">
                <h3>Accounts (Today)</h3>
                <h1>{unique_accounts_today}</h1>
            </div>
        ''', unsafe_allow_html=True)
    with kcol2:
        st.markdown(f'''
            <div class="metric-box">
                <h3>Productivity % (Today)</h3>
                <h1>{productivity_today}%</h1>
            </div>
        ''', unsafe_allow_html=True)

    # Visualizations
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📆 Daily Productivity")
        daily_df = df.groupby('date')['total_time'].sum().reset_index()
        daily_df['date'] = pd.to_datetime(daily_df['date'])
        daily_df['productivity'] = (daily_df['total_time'] / 480) * 100
        
        if not daily_df.empty:
            st.line_chart(daily_df.set_index('date')[["productivity"]], height=300)
        else:
            st.info("No data available for chart.")

    with col2:
        st.subheader("📋 Task Distribution")
        task_df = df.groupby('task_type')['total_count'].sum().reset_index()
        if not task_df.empty:
            st.bar_chart(task_df.set_index('task_type'), height=300)
        else:
            st.info("No task distribution data to display.")

    # Detailed View
    st.markdown("---")
    st.subheader("🔍 Detailed Records")
    detailed_df = df[['date', 'account_id', 'task_type', 'total_count', 'total_time']].copy()
    detailed_df['date'] = pd.to_datetime(detailed_df['date']).dt.date
    detailed_df['total_time'] = detailed_df['total_time'].apply(lambda x: f"{x/60:.1f} hrs")
    st.dataframe(
        detailed_df.rename(columns={
            'date': 'Date',
            'account_id': 'Account',
            'task_type': 'Task Type',
            'total_count': 'Count',
            'total_time': 'Time Spent'
        }),
        height=400,
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("📭 No data available for the selected filters")

# --- Sidebar Summary ---
st.sidebar.header("📅 Daily Summary")
st.sidebar.markdown(f"**Selected Date:** {date.strftime('%b %d, %Y')}")

# Compute productivity for the selected date for sidebar display
conn = sqlite3.connect("productivity.db")
sidebar_tasks = pd.read_sql(
    "SELECT SUM(total_time) as total_time FROM tasks WHERE date = ?",
    conn,
    params=(date.isoformat(),)
)
conn.close()

if not sidebar_tasks.empty and sidebar_tasks['total_time'][0] is not None:
    productivity_sidebar = round(sidebar_tasks['total_time'][0] / 480 * 100, 1)
else:
    productivity_sidebar = 0

st.sidebar.metric("Productivity % Today", f"{productivity_sidebar}%")

conn = sqlite3.connect("productivity.db")
daily_tasks = pd.read_sql(
    """SELECT task_type, SUM(count) as total_count 
       FROM tasks 
       WHERE date = ?
       GROUP BY task_type""", 
    conn,
    params=(date.isoformat(),)
)
conn.close()

# Create complete task list
all_tasks = pd.DataFrame({'task_type': list(task_types.keys())})
daily_counts = all_tasks.merge(daily_tasks, on='task_type', how='left').fillna(0)

# Display task counts in sidebar
st.sidebar.subheader("Today's Tasks")
for task in task_types.keys():
    count = int(daily_counts[daily_counts['task_type'] == task]['total_count'].values[0])
    st.sidebar.metric(f"{task}", count, help=f"Time per task: {task_types[task]} mins")
