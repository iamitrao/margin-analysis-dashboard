import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Set page config
st.set_page_config(page_title="Nassau Candy Analytics", page_icon="🍬", layout="wide")

# Load and clean data
@st.cache_data
def load_data():
    df = pd.read_csv("Nassau Candy Distributor.csv")
    
    # Factory Mapping
    factories_data = [
        {"Factory": "Lot's O' Nuts", "Latitude": 32.881893, "Longitude": -111.768036, "Product Name": "Wonka Bar - Nutty Crunch Surprise"},
        {"Factory": "Lot's O' Nuts", "Latitude": 32.881893, "Longitude": -111.768036, "Product Name": "Wonka Bar - Fudge Mallows"},
        {"Factory": "Lot's O' Nuts", "Latitude": 32.881893, "Longitude": -111.768036, "Product Name": "Wonka Bar -Scrumdiddlyumptious"},
        {"Factory": "Wicked Choccy's", "Latitude": 32.076176, "Longitude": -81.088371, "Product Name": "Wonka Bar - Milk Chocolate"},
        {"Factory": "Wicked Choccy's", "Latitude": 32.076176, "Longitude": -81.088371, "Product Name": "Wonka Bar - Triple Dazzle Caramel"},
        {"Factory": "Sugar Shack", "Latitude": 48.11914, "Longitude": -96.18115, "Product Name": "Laffy Taffy"},
        {"Factory": "Sugar Shack", "Latitude": 48.11914, "Longitude": -96.18115, "Product Name": "SweeTARTS"},
        {"Factory": "Sugar Shack", "Latitude": 48.11914, "Longitude": -96.18115, "Product Name": "Nerds"},
        {"Factory": "Sugar Shack", "Latitude": 48.11914, "Longitude": -96.18115, "Product Name": "Fun Dip"},
        {"Factory": "Sugar Shack", "Latitude": 48.11914, "Longitude": -96.18115, "Product Name": "Fizzy Lifting Drinks"},
        {"Factory": "Secret Factory", "Latitude": 41.446333, "Longitude": -90.565487, "Product Name": "Everlasting Gobstopper"},
        {"Factory": "Secret Factory", "Latitude": 41.446333, "Longitude": -90.565487, "Product Name": "Lickable Wallpaper"},
        {"Factory": "Secret Factory", "Latitude": 41.446333, "Longitude": -90.565487, "Product Name": "Wonka Gum"},
        {"Factory": "The Other Factory", "Latitude": 35.1175, "Longitude": -89.971107, "Product Name": "Hair Toffee"},
        {"Factory": "The Other Factory", "Latitude": 35.1175, "Longitude": -89.971107, "Product Name": "Kazookles"}
    ]
    factories_df = pd.DataFrame(factories_data)
    df = pd.merge(df, factories_df, on='Product Name', how='left')

    # Clean data
    df = df[df['Sales'] > 0]
    df = df[df['Cost'] > 0]
    
    # Calculate key metrics
    df['Gross Profit'] = df['Sales'] - df['Cost']
    df['Gross Margin'] = np.where(df['Sales'] > 0, df['Gross Profit'] / df['Sales'], 0)
    df['Profit per Unit'] = np.where(df['Units'] > 0, df['Gross Profit'] / df['Units'], 0)
    
    total_sales = df['Sales'].sum()
    total_profit = df['Gross Profit'].sum()
    df['Revenue Contribution'] = df['Sales'] / total_sales
    df['Profit Contribution'] = df['Gross Profit'] / total_profit
    
    # Parse Dates & Logistics 
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d-%m-%Y', errors='coerce')
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], format='%d-%m-%Y', errors='coerce')
    
    df.loc[df['Order Date'].isna(), 'Order Date'] = pd.to_datetime(df.loc[df['Order Date'].isna(), 'Order Date'], infer_datetime_format=True, errors='coerce')
    df.loc[df['Ship Date'].isna(), 'Ship Date'] = pd.to_datetime(df.loc[df['Ship Date'].isna(), 'Ship Date'], infer_datetime_format=True, errors='coerce')

    df['Lead Time (Days)'] = (df['Ship Date'] - df['Order Date']).dt.days
    
    # Pre-calc margin volatility (grouped by product and month)
    df['Order Month'] = df['Order Date'].dt.to_period('M')
    
    return df

df = load_data()

# --- SIDEBAR INTERACTIVE FILTERS ---
st.sidebar.header("Filter Data")

# 1. Date Range Selector
min_date = df['Order Date'].min().date() if not pd.isna(df['Order Date'].min()) else pd.Timestamp('2020-01-01').date()
max_date = df['Order Date'].max().date() if not pd.isna(df['Order Date'].max()) else pd.Timestamp('2030-01-01').date()

date_range = st.sidebar.date_input(
    "📅 Date Range Selector",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# 2. Division Filter
divisions = df['Division'].dropna().unique().tolist()
selected_divisions = st.sidebar.multiselect(
    "🏢 Division Filter",
    options=divisions,
    default=divisions
)

# 3. Margin Threshold Slider
min_margin = float(df['Gross Margin'].min() * 100)
max_margin = float(df['Gross Margin'].max() * 100)
margin_threshold = st.sidebar.slider(
    "📊 Minimum Margin Threshold (%)",
    min_value=max_margin if pd.isna(min_margin) else min_margin,
    max_value=min_margin if pd.isna(max_margin) else max_margin,
    value=min_margin if pd.isna(min_margin) else min_margin,
    step=1.0
)

# 4. Product Search
search_term = st.sidebar.text_input("🔍 Product Search", "")

# --- APPLY FILTERS ---
filtered_df = df.copy()

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[(filtered_df['Order Date'].dt.date >= start_date) & (filtered_df['Order Date'].dt.date <= end_date)]

if selected_divisions:
    filtered_df = filtered_df[filtered_df['Division'].isin(selected_divisions)]

filtered_df = filtered_df[filtered_df['Gross Margin'] * 100 >= margin_threshold]

if search_term:
    filtered_df = filtered_df[filtered_df['Product Name'].str.contains(search_term, case=False, na=False)]


# --- TOP LEVEL SUMMARY ---
st.title("🍬 Nassau Candy Financial Dashboard")
st.markdown("Strategic oversight for product profitability and division performance.")

col1, col2, col3, col4 = st.columns(4)
total_sales = filtered_df['Sales'].sum()
total_profit = filtered_df['Gross Profit'].sum()
avg_margin = (total_profit / total_sales) if total_sales > 0 else 0
avg_lead_time = filtered_df['Lead Time (Days)'].mean()

col1.metric("Total Sales", f"${total_sales:,.2f}")
col2.metric("Total Gross Profit", f"${total_profit:,.2f}")
col3.metric("Average Gross Margin", f"{avg_margin:.1%}")
col4.metric("Avg Delivery Lead Time", f"{avg_lead_time:.1f} days")

st.write("---")

# --- DASHBOARD TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 Product Profitability", 
    "🏢 Division Performance", 
    "⚖️ Cost vs Margin", 
    "🎯 Profit Concentration",
    "🚚 Logistics & Factories" # NEW TAB
])

# ----------------- TAB 1: PRODUCT PROFITABILITY -----------------
with tab1:
    st.subheader("Product Profitability Overview")
    
    prod_agg = filtered_df.groupby('Product Name').agg({
        'Sales':'sum', 
        'Gross Profit':'sum',
        'Cost': 'sum'
    }).reset_index()
    prod_agg['Gross Margin'] = np.where(prod_agg['Sales'] > 0, prod_agg['Gross Profit'] / prod_agg['Sales'], 0)
    prod_agg['Revenue Contrib'] = prod_agg['Sales'] / total_sales
    prod_agg['Profit Contrib'] = prod_agg['Gross Profit'] / total_profit
    
    # KPI: Margin Volatility
    monthly_margins = filtered_df.groupby(['Product Name', 'Order Month'])['Gross Margin'].mean().reset_index()
    margin_vol = monthly_margins.groupby('Product Name')['Gross Margin'].std().fillna(0).reset_index()
    margin_vol.rename(columns={'Gross Margin': 'Margin Volatility (StdDev)'}, inplace=True)
    
    prod_agg = pd.merge(prod_agg, margin_vol, on='Product Name', how='left')
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top Performers by Profit**")
        top_profit = prod_agg.sort_values(by='Gross Profit', ascending=False).head(10)
        fig1 = px.bar(top_profit, y='Product Name', x='Gross Profit', orientation='h', title='Top 10 Products by Gross Profit', color='Gross Profit', color_continuous_scale='Greens')
        fig1.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.markdown("**Bottom Performers by Profit**")
        bottom_profit = prod_agg.sort_values(by='Gross Profit', ascending=True).head(10)
        fig2 = px.bar(bottom_profit, y='Product Name', x='Gross Profit', orientation='h', title='Bottom 10 Products by Gross Profit', color='Gross Profit', color_continuous_scale='Reds')
        st.plotly_chart(fig2, use_container_width=True)
        
    st.markdown("**Product Level Leaderboard (With Margin Volatility & Contribution Metrics)**")
    st.dataframe(prod_agg.sort_values('Gross Profit', ascending=False).style.format({
        'Sales': '${:,.2f}',
        'Gross Profit': '${:,.2f}',
        'Cost': '${:,.2f}',
        'Gross Margin': '{:.1%}',
        'Revenue Contrib': '{:.1%}',
        'Profit Contrib': '{:.1%}',
        'Margin Volatility (StdDev)': '{:.3f}'
    }), use_container_width=True)

# ----------------- TAB 2: DIVISION PERFORMANCE -----------------
with tab2:
    st.subheader("Division Performance Dashboard")
    div_agg = filtered_df.groupby('Division').agg({
        'Sales':'sum', 
        'Gross Profit':'sum'
    }).reset_index()
    div_agg['Gross Margin'] = np.where(div_agg['Sales'] > 0, div_agg['Gross Profit'] / div_agg['Sales'], 0)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Revenue vs Profit by Division**")
        fig_div = go.Figure(data=[
            go.Bar(name='Sales', x=div_agg['Division'], y=div_agg['Sales'], marker_color='rgb(55, 83, 109)'),
            go.Bar(name='Gross Profit', x=div_agg['Division'], y=div_agg['Gross Profit'], marker_color='rgb(26, 118, 255)')
        ])
        fig_div.update_layout(barmode='group', title="Revenue vs Gross Profit")
        st.plotly_chart(fig_div, use_container_width=True)
    
    with c2:
        st.markdown("**Margin Distribution by Division**")
        fig_box = px.box(filtered_df, x="Division", y="Gross Margin", color="Division", title="Distribution of Margins per Transaction")
        fig_box.layout.yaxis.tickformat = ',.0%'
        st.plotly_chart(fig_box, use_container_width=True)

# ----------------- TAB 3: COST VS MARGIN DIAGNOSTICS -----------------
with tab3:
    st.subheader("Cost vs Margin Diagnostics")
    
    scatter_data = filtered_df.groupby('Product Name').agg({
        'Sales': 'sum',
        'Cost': 'sum',
        'Gross Profit': 'sum',
        'Units': 'sum'
    }).reset_index()
    scatter_data['Gross Margin'] = np.where(scatter_data['Sales'] > 0, scatter_data['Gross Profit'] / scatter_data['Sales'], 0)
    scatter_data['Risk Flag'] = np.where(scatter_data['Gross Margin'] < 0.40, 'High Risk (<40% Margin)', 'Healthy')
    
    fig_scatter = px.scatter(
        scatter_data, 
        x="Cost", 
        y="Sales", 
        color="Risk Flag",
        size=(scatter_data["Sales"]+1), 
        hover_name="Product Name",
        hover_data={"Margin": (scatter_data['Gross Margin']*100).apply(lambda x: f"{x:.1f}%")},
        title="Cost-Efficiency Profile: Cost vs Sales Volume"
    )
    fig_scatter.add_shape(
        type="line", line=dict(dash='dash'),
        x0=0, y0=0, x1=scatter_data['Cost'].max(), y1=scatter_data['Cost'].max()
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# ----------------- TAB 4: PROFIT CONCENTRATION -----------------
with tab4:
    st.subheader("Concentration Analysis (80/20 Pareto)")
    
    col_type = st.radio("Select Pareto Measure", ["Gross Profit", "Sales (Revenue)"], horizontal=True)
    metric = "Gross Profit" if col_type == "Gross Profit" else "Sales"
    
    pareto_df = filtered_df.groupby('Product Name').agg({metric:'sum'}).reset_index()
    pareto_df = pareto_df[pareto_df[metric] > 0]
    pareto_df = pareto_df.sort_values(metric, ascending=False)
    
    pareto_df['Cumulative Value'] = pareto_df[metric].cumsum()
    pareto_df['Cumulative %'] = pareto_df['Cumulative Value'] / pareto_df[metric].sum()
    
    fig_pareto = go.Figure()
    fig_pareto.add_trace(go.Bar(
        x=pareto_df['Product Name'],
        y=pareto_df[metric],
        name=metric,
        marker_color='rgb(55, 83, 109)'
    ))
    fig_pareto.add_trace(go.Scatter(
        x=pareto_df['Product Name'],
        y=pareto_df['Cumulative %'],
        name='Cumulative %',
        yaxis='y2',
        mode='lines+markers',
        marker_color='red'
    ))
    fig_pareto.update_layout(
        title=f"Pareto Summary: Concentration of Product {metric}",
        yaxis=dict(title=f"{metric} ($)"),
        yaxis2=dict(title="Cumulative %", overlaying='y', side='right', tickformat=',.0%', range=[0, 1.05]),
        xaxis=dict(tickangle=-45)
    )
    st.plotly_chart(fig_pareto, use_container_width=True)
    
    eighty_percent_idx = pareto_df[pareto_df['Cumulative %'] <= 0.8]
    products_for_80 = len(eighty_percent_idx) if not eighty_percent_idx.empty else 1
    total_products = len(pareto_df)
    st.info(f"**Dependency Indicator:** {products_for_80} product(s) ({products_for_80/total_products:.1%}) generate approximately 80% of your {metric}.")

# ----------------- TAB 5: LOGISTICS & FACTORIES -----------------
with tab5:
    st.subheader("Logistics & Regional Congestion Dashboard")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Factory Dependency Risk**")
        factory_agg = filtered_df.groupby('Factory').agg({'Gross Profit':'sum', 'Sales':'sum'}).reset_index()
        fig_pie = px.pie(factory_agg, values='Gross Profit', names='Factory', title="Gross Profit Generated per Factory")
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with c2:
        st.markdown("**State Congestion: Average Delivery Delays**")
        state_delay = filtered_df.groupby('State/Province').agg(
            Avg_Delay=('Lead Time (Days)', 'mean'),
            Order_Count=('Row ID', 'count')
        ).reset_index().sort_values('Avg_Delay', ascending=False).head(15)
        
        fig_state = px.bar(state_delay, x='State/Province', y='Avg_Delay', color='Order_Count', 
                           title="Top 15 Most Congestion-Prone States", 
                           color_continuous_scale='Blues')
        st.plotly_chart(fig_state, use_container_width=True)
        
    st.markdown("**Cost vs Lead Time (Risk Mapping)**")
    risk_mapping = filtered_df.groupby('Product Name').agg(
        Avg_Lead_Time=('Lead Time (Days)', 'mean'),
        Gross_Margin=('Gross Margin', 'mean'),
        Factory=('Factory', 'first')
    ).reset_index()
    fig_risk = px.scatter(risk_mapping, x='Avg_Lead_Time', y='Gross_Margin', color='Factory', 
                          hover_name='Product Name', title='Logistical Risk Matrix: Lead Time vs Margin')
    fig_risk.layout.yaxis.tickformat = ',.0%'
    st.plotly_chart(fig_risk, use_container_width=True)
