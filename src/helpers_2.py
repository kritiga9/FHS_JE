import hmac
import jwt
from src.settings import keboola_client, STATUS_TAB_ID
from src.settings import STREAMLIT_BUCKET_ID
from src.settings import RESTAURANTS_TAB_ID
import requests
import json
import streamlit as st
import pandas as pd
import datetime
from datetime import datetime, timedelta
import numpy as np
import extra_streamlit_components as stx
import random #delete this after we get real data

###Functions for Phase2 of the App (showing naigation and pages)

def show_journal_entry_page(restaurants_filtered):
    st.title("Select a Location for Journal Entry")
    locations = restaurants_filtered
    
    for index, row in restaurants_filtered.iterrows():
        restaurant_name = row['Restaurant']  # Get the restaurant name from the 'Restaurant' column
        if st.button(restaurant_name):
            st.session_state.selected_location = restaurant_name
            st.session_state.current_page = "Daily Sales Export"
            st.experimental_rerun()


def show_invoice_selection_page(restaurants_filtered):
    st.title("Select a Location for Invoice")
    locations = restaurants_filtered
    for location in locations:
        if st.button(location):
            st.session_state.selected_location = location
            st.session_state.current_page = "Distribution Invoices"
            st.experimental_rerun()
                
daily_totals = pd.read_csv("daily_totals.csv")
def show_welcome_page():
        st.title("Welcome")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("QB authentication"):
                st.session_state.current_page = "QB authentication"
                st.experimental_rerun()
        with col2:
            if st.button("QB Journal Entry"):
                st.session_state.current_page = "Journal_Entry"
                st.experimental_rerun()
        with col3:
            if st.button("QB Invoices"):
                st.session_state.current_page = "InvoiceSelection"
                st.experimental_rerun()

def show_qb_authentication_page():
    st.title("QB Authentication Page")

def show_daily_sales_export_page():
    st.title(st.session_state.selected_location)
    st.subheader("Daily Sales Export")
    
    # Filter daily_totals DataFrame based on selected_location
    filtered_daily_totals = daily_totals[daily_totals['Location'] == st.session_state.selected_location]
    
    
    # Display column headers
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown("**Date**")
    col2.markdown("**Gross Sales**")
    col3.markdown("**Post to QuickBooks**")
    col4.markdown("**Skip**")
    
    # Define a CSS style to reduce the gap between lines
    hr_style = 'border: none; height: 1px; background-color: #ccc; margin: 5px 0;'

    
    for index, row in filtered_daily_totals.iterrows():
        col1, col2, col3, col4 = st.columns(4)
        col1.write(row["Date"])
        col2.write(f"${row['Gross_sales']:.2f}")
        with col3:
            st.button("Review & Post", key=f"Review&Post_{index}")
        with col4:
            st.button("Skip", key=f"Skip_{index}")
        
        # Add a horizontal line to separate rows
        st.markdown(f'<hr style="{hr_style}">', unsafe_allow_html=True)
    

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