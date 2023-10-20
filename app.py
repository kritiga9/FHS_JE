import streamlit as st
import random
import pandas as pd
from datetime import datetime, timedelta

def show_welcome_page():
    st.title("Welcome")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("QB authentication"):
            st.session_state.page = "QB authentication"
            st.experimental_rerun()
    with col2:
        if st.button("QB Journal Entry"):
            st.session_state.page = "Selection"
            st.experimental_rerun()
    with col3:
        if st.button("QB Invoices"):
            st.session_state.page = "InvoiceSelection"
            st.experimental_rerun()

def show_qb_authentication_page():
    st.title("QB Authentication Page")

def show_selection_page():
    st.title("Select a Location")
    locations = ["ACWORTH", "WAVERLY", "WESLEY CHAPEL", "WONDERLAND SOUTH", "BURLINGTON"]
    for location in locations:
        if st.button(location):
            st.session_state.selected_location = location
            st.session_state.page = "Daily Sales Export"
            st.experimental_rerun()

def show_invoice_selection_page():
    st.title("Select a Location for Invoice")
    locations = ["ACWORTH", "WAVERLY", "WESLEY CHAPEL", "WONDERLAND SOUTH", "BURLINGTON"]
    for location in locations:
        if st.button(location):
            st.session_state.selected_location = location
            st.session_state.page = "Distribution Invoices"
            st.experimental_rerun()

def show_daily_sales_export_page():
    st.title(st.session_state.selected_location)
    st.subheader("Daily Sales Export")
    
    # Generating dummy data
    dates = [(datetime.now() - timedelta(days=i)).strftime('%d/%b/%Y') for i in range(30)]
    sales = [f"${random.uniform(1000.0, 100000.0):,.2f}" for _ in range(30)]
    data = {"Date": dates, "Gross Sales": sales}
    
    df = pd.DataFrame(data)
    
    # Display column headers
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown("**Date**")
    col2.markdown("**Gross Sales**")
    col3.markdown("**Post to QuickBooks**")
    col4.markdown("**Skip**")
    
    for index, row in df.iterrows():
        col1, col2, col3, col4 = st.columns(4)
        col1.write(row["Date"])
        col2.write(row["Gross Sales"])
        with col3:
            st.button("Review & Post", key=f"Review&Post_{index}")
        with col4:
            st.button("Skip", key=f"Skip_{index}")

def show_distribution_invoices_page():
    st.title(st.session_state.selected_location)
    st.subheader("Distribution Invoices")
    
    # Generating dummy data
    dates = [(datetime.now() - timedelta(days=i)).strftime('%d/%b/%Y') for i in range(30)]
    invoice_numbers = [str(random.randint(1000000, 9999999)) for _ in range(30)]
    invoice_totals = [f"${random.uniform(1000.0, 100000.0):,.2f}" for _ in range(30)]
    data = {"Invoice Date": dates, "Invoice number": invoice_numbers, "Invoice total": invoice_totals}
    
    df = pd.DataFrame(data)
    
    # Display column headers
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.markdown("**Invoice Date**")
    col2.markdown("**Invoice Number**")
    col3.markdown("**Invoice Total**")
    col4.markdown("**Post to QuickBooks**")
    col5.markdown("**Skip**")
    
    for index, row in df.iterrows():
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.write(row["Invoice Date"])
        col2.write(row["Invoice number"])
        col3.write(row["Invoice total"])
        with col4:
            st.button("Review & Post", key=f"Review&Post_Invoice_{index}")
        with col5:
            st.button("Skip", key=f"Skip_Invoice_{index}")

def main():
    # Page routing
    if "page" not in st.session_state:
        st.session_state.page = "Welcome"

    if st.session_state.page == "Welcome":
        show_welcome_page()
    elif st.session_state.page == "QB authentication":
        show_qb_authentication_page()
    elif st.session_state.page == "Selection":
        show_selection_page()
    elif st.session_state.page == "InvoiceSelection":
        show_invoice_selection_page()
    elif st.session_state.page == "Daily Sales Export":
        show_daily_sales_export_page()
    elif st.session_state.page == "Distribution Invoices":
        show_distribution_invoices_page()

if __name__ == "__main__":
    main()