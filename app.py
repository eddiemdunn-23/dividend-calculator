import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import io

# Set up page styling and configurations
st.set_page_config(page_title="Dividend Target & Savings Planner", layout="wide")

st.markdown("""
    <style>
    .main-header { font-size: 32px; font-weight: bold; color: #1E3A8A; margin-bottom: 20px; }
    .sub-header { font-size: 20px; font-weight: semi-bold; color: #0F766E; margin-top: 15px; }
    .metric-box { padding: 15px; background-color: #F3F4F6; border-radius: 8px; border-left: 5px solid #2563EB; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🎯 Client Dividend & Wealth Roadmap Calculator</div>', unsafe_allow_html=True)
st.write("Help your clients discover their target capital, map out a monthly savings timeline, and visualize the compounding power of DRIP.")

# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
st.sidebar.header("📋 Client Inputs")

# Section 1: Core Dividend Goals
st.sidebar.subheader("1. Income Target")
net_monthly_goal = st.sidebar.number_input("Desired Net Monthly Dividend ($)", min_value=10, value=2000, step=100)
avg_yield = st.sidebar.number_input("Expected Portfolio Yield (%)", min_value=0.1, max_value=20.0, value=4.5, step=0.1)
tax_rate = st.sidebar.number_input("Estimated Tax Rate (%)", min_value=0.0, max_value=90.0, value=15.0, step=0.5)

# Section 2: Savings & Horizon
st.sidebar.subheader("2. Savings & Horizon")
current_savings = st.sidebar.number_input("Starting Capital ($)", min_value=0, value=10000, step=1000)
monthly_deposit = st.sidebar.number_input("Monthly Contribution ($)", min_value=0, value=1000, step=100)
years_horizon = st.sidebar.slider("Simulation Horizon (Years)", min_value=1, max_value=40, value=20)

# Section 3: Advanced Growth & Frequency
st.sidebar.subheader("3. Advanced Options")
dividend_growth = st.sidebar.number_input("Annual Dividend Growth Rate (%)", min_value=0.0, max_value=15.0, value=3.0, step=0.1)
capital_appreciation = st.sidebar.number_input("Annual Stock Price Growth (%)", min_value=0.0, max_value=20.0, value=4.0, step=0.1)
enable_drip = st.sidebar.checkbox("Reinvest Dividends (DRIP)", value=True)
payout_freq = st.sidebar.selectbox("Stock Dividend Payout Frequency", ["Monthly", "Quarterly", "Semi-Annual"])

# Mapping payout intervals
freq_map = {"Monthly": 1, "Quarterly": 3, "Semi-Annual": 6}
months_per_payout = freq_map[payout_freq]

# -----------------------------------------------------------------------------
# CALCULATIONS CORE
# -----------------------------------------------------------------------------
yield_dec = avg_yield / 100.0
tax_dec = tax_rate / 100.0

gross_monthly_goal = net_monthly_goal / (1.0 - tax_dec)
gross_annual_goal = gross_monthly_goal * 12
required_capital = gross_annual_goal / yield_dec

# Time-to-Target (Linear Roadmap)
monthly_growth_rate = (capital_appreciation / 100.0) / 12
months_to_target = 0
temp_cap = current_savings
achieved_natively = False

if monthly_deposit > 0 or monthly_growth_rate > 0:
    for m in range(1, 601):
        temp_cap = temp_cap * (1 + monthly_growth_rate) + monthly_deposit
        if temp_cap >= required_capital:
            months_to_target = m
            achieved_natively = True
            break

# Dynamic Loop Simulation
sim_months = years_horizon * 12
balance_history = []
dividend_history = []
total_contributions = []

current_balance = current_savings
cumulative_contributed = current_savings
annual_running_dividend = 0.0

for month in range(1, sim_months + 1):
    current_year = month // 12
    # Adjust yield for inflation/dividend growth annually
    dynamic_yield = avg_yield * ((1 + (dividend_growth / 100)) ** current_year)
    
    # Process payout if it falls on the frequency cycle month
    net_div_received = 0.0
    if month % months_per_payout == 0:
        payout_percentage = (dynamic_yield / 100) / (12 / months_per_payout)
        gross_div = current_balance * payout_percentage
        net_div_received = gross_div * (1.0 - tax_dec)
        
        if enable_drip:
            current_balance += net_div_received
            
    # Record tracking metric for annual baseline run-rate
    annual_running_dividend = current_balance * (dynamic_yield / 100) * (1.0 - tax_dec)

    # Monthly price changes & asset growth
    current_balance = current_balance * (1 + ((capital_appreciation / 100) / 12))
    
    # Monthly contribution updates
    current_balance += monthly_deposit
    cumulative_contributed += monthly_deposit
    
    # Synchronize data arrays at the close of every year
    if month % 12 == 0:
        balance_history.append(current_balance)
        dividend_history.append(annual_running_dividend)
        total_contributions.append(cumulative_contributed)

# Dataframe generation
plot_df = pd.DataFrame({
    "Year": list(range(1, len(balance_history) + 1)),
    "Portfolio Value ($)": balance_history,
    "Annual Net Dividend ($)": dividend_history,
    "Principal Invested ($)": total_contributions
}).set_index("Year")

# -----------------------------------------------------------------------------
# DISPLAY INTERFACE
# -----------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="sub-header">🏁 Required Capital</div>', unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><h3>${required_capital:,.2f}</h3>Required to generate ${net_monthly_goal:,.2f}/mo net.</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="sub-header">⏳ Standard Roadmap</div>', unsafe_allow_html=True)
    if achieved_natively:
        years_req = months_to_target // 12
        months_rem = months_to_target % 12
        st.markdown(f"<div class='metric-box'><h3>{years_req} Yrs, {months_rem} Mos</h3>Time to build target capital from savings alone.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='metric-box'><h3>50+ Years</h3>Increase savings or yield to hit target faster.</div>", unsafe_allow_html=True)

with col3:
    st.markdown('<div class="sub-header">📈 Simulated Portfolio</div>', unsafe_allow_html=True)
    final_net_monthly = (dividend_history[-1] / 12) if dividend_history else 0
    st.markdown(f"<div class='metric-box'><h3>${final_net_monthly:,.2f}/mo</h3>Net dividend income reached at Year {years_horizon}.</div>", unsafe_allow_html=True)

st.markdown("---")

st.subheader("🔮 Growth Projection & Compound Interest Visualizer")
tab1, tab2 = st.tabs(["💰 Portfolio Value vs. Contributions", "💵 Dividend Income Growth Trajectory"])

with tab1:
    st.line_chart(plot_df[["Portfolio Value ($)", "Principal Invested ($)"]])
with tab2:
    st.bar_chart(plot_df["Annual Net Dividend ($)"])

st.subheader("📊 Annual Simulation Metrics Ledger")
st.dataframe(
    plot_df.style.format({
        "Portfolio Value ($)": "${:,.2f}",
        "Annual Net Dividend ($)": "${:,.2f}",
        "Principal Invested ($)": "${:,.2f}"
    }),
    use_container_width=True
)

# -----------------------------------------------------------------------------
# PDF REPORT EXPORTER IMPLEMENTATION
# -----------------------------------------------------------------------------
def generate_pdf(df, req_cap, net_goal, final_div):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Client Dividend Wealth Roadmap Report", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(100, 10, f"Target Capital Needed: ${req_cap:,.2f}", ln=True)
    pdf.cell(100, 10, f"Target Monthly Income Goal: ${net_goal:,.2f}", ln=True)
    pdf.cell(100, 10, f"Projected Monthly Dividend at Horizon: ${final_div:,.2f}", ln=True)
    pdf.ln(10)
    
    # Simple Table Headings
    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 8, "Year", border=1)
    pdf.cell(55, 8, "Portfolio Value", border=1)
    pdf.cell(55, 8, "Annual Net Dividend", border=1)
    pdf.cell(50, 8, "Principal Invested", border=1)
    pdf.ln()
    
    # Table Content
    pdf.set_font("Arial", "", 10)
    for index, row in df.iterrows():
        pdf.cell(30, 8, str(index), border=1)
        pdf.cell(55, 8, f"${row['Portfolio Value ($)']:,.2f}", border=1)
        pdf.cell(55, 8, f"${row['Annual Net Dividend ($)']:,.2f}", border=1)
        pdf.cell(50, 8, f"${row['Principal Invested ($)']:,.2f}", border=1)
        pdf.ln()
        
    return pdf.output()

# Export button handler
pdf_data = generate_pdf(plot_df, required_capital, net_monthly_goal, final_net_monthly)
st.sidebar.download_button(
    label="📥 Download Client PDF Report",
    data=bytes(pdf_data),
    file_name="dividend_roadmap_report.pdf",
    mime="application/pdf"
)