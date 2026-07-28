import streamlit as pd
import pandas as pd
import numpy as np
import streamlit as st
from fpdf import FPDF
import base64

# Configure page styling
st.set_page_config(page_title="Professional Dividend Calculator & Planner", layout="wide")

st.markdown("""
    <style>
    .main-header { font-size: 32px; font-weight: bold; color: #1E3A8A; margin-bottom: 20px; }
    .sub-header { font-size: 20px; font-weight: semi-bold; color: #0F766E; margin-top: 15px; }
    .metric-box { padding: 15px; background-color: #F3F4F6; border-radius: 8px; border-left: 5px solid #2563EB; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🎯 Elite Client Dividend Planner & Report Generator</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
st.sidebar.header("📋 Client Input Panel")

# Section 1: Core Dividend Goals
st.sidebar.subheader("1. Core Income Target")
net_monthly_goal = st.sidebar.number_input("Desired Net Monthly Dividend ($)", min_value=10, value=2000, step=100)
avg_yield = st.sidebar.number_input("Portfolio Yield (%)", min_value=0.1, max_value=20.0, value=4.5, step=0.1)
tax_rate = st.sidebar.number_input("Estimated Dividend Tax Rate (%)", min_value=0.0, max_value=90.0, value=15.0, step=0.5)

# Section 2: Payout Frequency Simulation
st.sidebar.subheader("2. Payout Frequency Mix")
st.sidebar.caption("Distribute portfolio weight across payout types (Must total 100%)")
w_monthly = st.sidebar.slider("Monthly Payout Stocks (%)", 0, 100, 20)
w_quarterly = st.sidebar.slider("Quarterly Payout Stocks (%)", 0, 100, 70)
w_semiannual = st.sidebar.slider("Semi-Annual Payout Stocks (%)", 0, 100, 10)

# Validate weight allocation
total_weight = w_monthly + w_quarterly + w_semiannual
if total_weight != 100:
    st.sidebar.error(f"⚠️ Allocation Total is {total_weight}%. It must equal 100%.")

# Section 3: Savings & Horizon
st.sidebar.subheader("3. Accumulation Roadmap")
current_savings = st.sidebar.number_input("Starting Capital ($)", min_value=0, value=10000, step=1000)
monthly_deposit = st.sidebar.number_input("Monthly Contribution ($)", min_value=0, value=1000, step=100)
years_horizon = st.sidebar.slider("Timeline Horizon (Years)", min_value=1, max_value=40, value=20)

# Section 4: Advanced Growth Variables
st.sidebar.subheader("4. Growth & DRIP Dynamics")
dividend_growth = st.sidebar.number_input("Annual Dividend Growth Rate (%)", min_value=0.0, max_value=15.0, value=3.0, step=0.1)
capital_appreciation = st.sidebar.number_input("Annual Stock Price Growth (%)", min_value=0.0, max_value=20.0, value=4.0, step=0.1)
enable_drip = st.sidebar.checkbox("Reinvest Dividends (DRIP)", value=True)

# -----------------------------------------------------------------------------
# CALCULATION CORE & ROADMAP
# -----------------------------------------------------------------------------
yield_dec = avg_yield / 100.0
tax_dec = tax_rate / 100.0

gross_monthly_goal = net_monthly_goal / (1.0 - tax_dec)
gross_annual_goal = gross_monthly_goal * 12
required_capital = gross_annual_goal / yield_dec

# Base Savings Timeline Calculations
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

# -----------------------------------------------------------------------------
# DYNAMIC MONTHLY SIMULATION ENGINE (DRIP & Frequencies)
# -----------------------------------------------------------------------------
sim_months = years_horizon * 12
balance_history = []
dividend_history = []
total_contributions = []

current_balance = current_savings
cumulative_contributed = current_savings

for month in range(1, sim_months + 1):
    # 1. Calculate this month's dynamic annualized yield rate
    current_year = month // 12
    monthly_yield = (avg_yield * ((1 + (dividend_growth / 100)) ** current_year)) / 12 / 100
    
    # 2. Calculate net dividends earned this month
    gross_div = current_balance * monthly_yield
    net_div = gross_div * (1.0 - tax_dec)
    
    # 3. Apply fractional stock price growth
    current_balance = current_balance * (1 + ((capital_appreciation / 100) / 12))
    
    # 4. Handle DRIP reinvestment check
    if enable_drip:
        current_balance += net_div
        
    # 5. Process standard recurring deposits
    current_balance += monthly_deposit
    cumulative_contributed += monthly_deposit
    
    # 6. CAPTURE DATA AT THE END OF EVERY YEAR (SYNCHRONIZED STEP)
    if month % 12 == 0:
        balance_history.append(current_balance)
        dividend_history.append(net_div * 12)
        total_contributions.append(cumulative_contributed)

# Build dynamic DataFrame for plotting (All arrays are now exactly 'years_horizon' long)
plot_df = pd.DataFrame({
    "Year": list(range(1, len(balance_history) + 1)),
    "Portfolio Value ($)": balance_history,
    "Annual Net Dividend ($)": dividend_history,
    "Principal Invested ($)": total_contributions
}).set_index("Year")

# Isolate standard final operational data year matrix for seasonal overview
last_year_months = range((sim_months - 11), sim_months + 1)
calendar_months_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
last_year_payouts = [monthly_cash_flows[m] for m in last_year_months]
calendar_df = pd.DataFrame({"Month": calendar_months_labels, "Net Income ($)": last_year_payouts}).set_index("Month")

# -----------------------------------------------------------------------------
# DISPLAY INTERFACE
# -----------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="sub-header">🏁 Target Core Capital</div>', unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><h3>${required_capital:,.2f}</h3>Needed for static ${net_monthly_goal:,.2f}/mo baseline.</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="sub-header">⏳ Savings Runway Timeline</div>', unsafe_allow_html=True)
    if achieved_natively:
        st.markdown(f"<div class='metric-box'><h3>{months_to_target // 12} Yrs, {months_to_target % 12} Mos</h3>Duration without factoring DRIP variables.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='metric-box'><h3>50+ Years Needed</h3>Adjust variables to condense timeframe.</div>", unsafe_allow_html=True)

with col3:
    st.markdown('<div class="sub-header">📊 Dynamic Horizon Income</div>', unsafe_allow_html=True)
    simulated_monthly_avg = dividend_history[-1] / 12 if dividend_history else 0
    st.markdown(f"<div class='metric-box'><h3>${simulated_monthly_avg:,.2f}/mo</h3>Actual simulated Net average at Year {years_horizon}.</div>", unsafe_allow_html=True)

st.markdown("---")

# Visual Data Sections
st.subheader("🔮 Portfolio & Cash Flow Horizon Visualizer")
tab1, tab2, tab3 = st.tabs(["💰 Wealth Compounding", "💵 Annualized Income Distributions", "📅 Expected Client Monthly Cash Flow Grid"])

with tab1:
    st.line_chart(plot_df[["Portfolio Value ($)", "Principal Invested ($)"]])
with tab2:
    st.bar_chart(plot_df["Annual Net Dividend ($)"])
with tab3:
    st.write(f"### Estimated Cash Flow Fluctuation Profile (Year {years_horizon})")
    st.caption("Notice how income changes based on quarterly and semi-annual payout cycles instead of perfect linear averages.")
    st.bar_chart(calendar_df["Net Income ($)"])

# -----------------------------------------------------------------------------
# EXPORT PDF REPORT LOGIC
# -----------------------------------------------------------------------------
class DividendReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(31, 58, 138)
        self.cell(0, 10, "STRATEGIC DIVIDEND & WEALTH ROADMAP REPORT", border=0, ln=1, align="L")
        self.set_draw_color(31, 58, 138)
        self.line(10, 18, 200, 18)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(156, 163, 175)
        self.cell(0, 10, f"Page {self.page_no()} | Confidential Wealth Advisory Documentation", border=0, align="C")

def generate_pdf_report():
    pdf = DividendReport()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)
    
    # Title Block
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(17, 24, 39)
    pdf.cell(0, 12, "Custom Wealth Accumulation Profile", ln=1)
    pdf.ln(2)
    
    # Financial Targets Overview Table
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 118, 110)
    pdf.cell(0, 10, "1. Core Portfolio Capital Benchmarks", ln=1)
    
    pdf.set_font("Helvetica", "", 10)
