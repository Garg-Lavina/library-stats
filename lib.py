import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

# Basic configuration
st.set_page_config(
    page_title="Library Stats",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Library Statistics Dashboard")

# Data loading with caching
@st.cache_data
def load_data(file_name='library_data.csv'):
    df = pd.read_csv(file_name)
    date_cols = ['issue_date', 'due_date', 'return_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("Filters")
filtered_df = df.copy()

# Date filter
if 'issue_date' in df.columns:
    min_date = df['issue_date'].min().date()
    max_date = df['issue_date'].max().date()
    date_range = st.sidebar.slider(
        "Date range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date)
    )
    filtered_df = filtered_df[
        (filtered_df['issue_date'].dt.date >= date_range[0]) & 
        (filtered_df['issue_date'].dt.date <= date_range[1])
    ]

# Dynamic filters for available columns
filter_options = {
    'genre': "Book Genres",
    'borrower_type': "Borrower Types",
    'student_batch': "Student Batches",
    'student_major': "Student Majors",
    'borrower_age_group': "Age Groups"
}

for col, label in filter_options.items():
    if col in df.columns:
        options = df[col].unique()
        selected = st.sidebar.multiselect(
            label,
            options=options,
            default=options
        )
        if selected:
            filtered_df = filtered_df[filtered_df[col].isin(selected)]

# Key metrics
st.header("Key Metrics")
cols = st.columns(4)
metrics = [
    ("Total Books Issued", len(filtered_df)),
    ("Unique Borrowers", filtered_df['borrower_id'].nunique()),
    ("Books Not Returned", filtered_df['return_date'].isna().sum()),
    ("Late Returns", filtered_df['overdue_status'].str.contains('Late|Overdue', na=False).sum())
]

for (label, value), col in zip(metrics, cols):
    col.metric(label, value)

# Visualization functions
def plot_time_series(data, x_col, y_col, title, x_label, y_label):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(data[x_col], data[y_col], marker='o')
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    plt.xticks(rotation=45)
    plt.grid(True)
    st.pyplot(fig)

def plot_bar_horizontal(data, title, x_label, y_label, palette='viridis', top_n=10):
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(x=data.values, y=data.index, ax=ax, palette=palette)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    st.pyplot(fig)

def plot_pie(data, title, colors='pastel'):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(data, labels=data.index, autopct='%1.1f%%', startangle=90, colors=sns.color_palette(colors))
    ax.set_title(title)
    ax.axis('equal')
    st.pyplot(fig)

# Visualizations
if not filtered_df.empty:
    st.header("Data Visualizations")
    
    if 'issue_date' in filtered_df.columns:
        monthly_data = filtered_df.groupby(pd.Grouper(key='issue_date', freq='M')).size().reset_index(name='count')
        plot_time_series(monthly_data, 'issue_date', 'count', 
                        'Books Issued Each Month', 'Date', 'Number of Books')
    
    if 'book_title' in filtered_df.columns:
        popular_books = filtered_df['book_title'].value_counts().head(10)
        plot_bar_horizontal(popular_books, 'Top 10 Most Borrowed Books', 
                          'Times Borrowed', 'Book Title')
    
    if 'genre' in filtered_df.columns:
        genre_counts = filtered_df['genre'].value_counts()
        plot_pie(genre_counts, 'Book Genre Distribution')
    
    if 'borrower_type' in filtered_df.columns:
        borrower_counts = filtered_df['borrower_type'].value_counts()
        plot_bar_horizontal(borrower_counts, 'Books Issued by Borrower Type', 
                          'Number of Books', 'Borrower Type', 'deep')
    
    if 'days_on_loan' in filtered_df.columns and 'genre' in filtered_df.columns:
        avg_loan = filtered_df.groupby('genre')['days_on_loan'].mean().sort_values(ascending=False)
        plot_bar_horizontal(avg_loan, 'Average Loan Duration by Genre', 
                          'Average Days', 'Genre', 'cubehelix')

# Data export
st.header("Filtered Data")
st.dataframe(filtered_df)

@st.cache_data
def convert_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

if not filtered_df.empty:
    excel_data = convert_to_excel(filtered_df)
    st.download_button(
        "Download as Excel",
        data=excel_data,
        file_name="filtered_library_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )