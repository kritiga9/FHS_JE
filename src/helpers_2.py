import hmac
import jwt
from src.settings import keboola_client, STATUS_TAB_ID
from src.settings import STREAMLIT_BUCKET_ID, CONFIG_ID
from src.settings import RESTAURANTS_TAB_ID , GROSS_SALES, DAILY_SALES
import requests
import json
import streamlit as st
import pandas as pd
import datetime
from datetime import datetime, timedelta
import numpy as np
import extra_streamlit_components as stx
from src.helpers import read_df
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

def show_daily_sales_export_page(name):
    # need to change this into an editable dataframe
    st.title(st.session_state.selected_location)
    st.subheader("Daily Sales Export")
    # Filter daily_totals DataFrame based on selected_location
    daily_totals = read_df(GROSS_SALES, filter_col_name="restaurant_full", filter_col_value=st.session_state.selected_location,dtype=str)
    daily_totals["gross_sales"] = daily_totals["gross_sales"].astype(float)
    daily_totals = daily_totals.sort_values("date", ascending=False).reset_index(drop=True)
    # Display column headers
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown("**Date**")
    col2.markdown("**Gross Sales**")
    col3.markdown("**Post to QuickBooks**")
    col4.markdown("**Skip**")
    
    # Define a CSS style to reduce the gap between lines
    hr_style = 'border: none; height: 1px; background-color: #ccc; margin: 5px 0;'

    
    # Assuming you have a dictionary to store skipped entries
    skipped_entries = {}

    # Create a placeholder to store skipped indices
    skipped_indices = []

    for index, row in daily_totals.iterrows():
        if index in skipped_indices:
            continue  # Skip displaying rows with skipped indices

        col1, col2, col3, col4 = st.columns(4)
        col1.write(row["date"])
        col2.write(f"${row['gross_sales']:.2f}")
        
        with col3:
            formatted_date = row["date"].replace("-", "")
            key = row["restaurant_id"] + "_" + formatted_date
            if st.button("Review & Post", key=f"Review&Post_{index}"):
                show_journal_entry(name, key)
                break
                
        with col4:
            # Using st.button's returned value to check if the button is clicked
            if st.button("Skip", key=f"Skip_{index}"):
                # Record timestamp and flag for skipped entry
                skipped_entries[key] = {"timestamp": datetime.now(), "skipped": True}
                # You may want to add a print statement or other logging here to indicate the skip
                skipped_indices.append(index)
                continue  # Skip displaying the rest of the row


    # After the loop, you can process the skipped_entries dictionary as needed
    # For example, print the skipped entries
    for key, value in skipped_entries.items():
        st.write(f"Skipped entry {key} at {value['timestamp']}")
        # Add a horizontal line to separate rows
        st.markdown(f'<hr style="{hr_style}">', unsafe_allow_html=True)
    

def show_journal_entry(name, key):
    df = read_df(DAILY_SALES, filter_col_name="id", filter_col_value=key)
    ACCOUNTS_TAB_ID = f'{CONFIG_ID}{name}.Account'
    accounts = read_df(ACCOUNTS_TAB_ID)['FullyQualifiedName'].tolist()
    #accounts = df["account"].unique().tolist()
    df = df[["account","Debit","Credit","Description"]]

    editable_df = st.data_editor(df,
                                num_rows="dynamic",
                                use_container_width=True,
                                column_config = {
                                    "account" : st.column_config.SelectboxColumn(
                                        "Account",
                                        help = "The category of expense",
                                        options = accounts,
                                        required = True
                                    )
                                },hide_index=True,
                                height = 35*len(df)+38
                                )

    # you can access the data by just editable_df
    credit_sum = df["Credit"].sum()
    debit_sum = df["Debit"].sum()
    difference = df["Debit"].sum() - df["Credit"].sum()
    col1,col2,col3,col4 = st.columns(4)

    with col1:
        st.write("")


    with col2:
        st.text_input('Difference',difference,disabled=True,key='diff')

    with col3:
        
        st.text_input('Credit Sum',credit_sum,disabled=True,key = 'credit_input')

    with col4:
        st.text_input('Debit Sum',debit_sum,disabled=True,key = 'debit_input')


