import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.settings import STATUS_TAB_ID, MAPPING_CLASSES_TAB_ID,MAPPING_TAB_ID, DEBUG
from src.helpers import parse_credentials
from src.helpers import read_df
from src.helpers import determine_step
from src.helpers import show_welcome_page, show_qb_authentication_page, show_journal_entry_page, show_invoice_selection_page, show_daily_sales_export_page, show_distribution_invoices_page
from src.streamlit_widgets import WorkflowProgress, submit_form, render_clickable_link
from src.streamlit_widgets import render_selectboxes
from src.helpers import Authenticate
from PIL import Image


config_dict = parse_credentials()

authenticator = Authenticate(
    config_dict['credentials'],
    config_dict['cookie']['name'],
    config_dict['cookie']['key'],
    config_dict['cookie']['expiry_days'],
    config_dict['preauthorized']
) 

with st.sidebar:
    #image = Image.open("/data/in/files/995108192_fhs_logo.png")
    #st.image(image, caption='')

    st.markdown('## **QUICKBOOKS AUTOMATION SETUP**')
    name, authentication_status, username = authenticator.login('Login', 'main')
  
if authentication_status:

    with st.sidebar:
        st.write(f'Welcome *{name}*')
        x = authenticator.logout('Logout', 'main')
        if st.session_state['logout'] == True:
            st.cache_data.clear()
            st.session_state['logout'] = False    

    # Initialize the current page as a session state variable
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Welcome"

    # Sidebar navigation
    st.sidebar.title("Navigation")
    if st.sidebar.button("Main Page", key="sidebar_welcome_button"):
        st.session_state.current_page = "Welcome"
    if st.sidebar.button("QB authentication", key="sidebar_auth_button"):
        st.session_state.current_page = "QB authentication"
    if st.sidebar.button("QB Journal Entry", key="sidebar_journal_button"):
        st.session_state.current_page = "Journal_Entry"
    if st.sidebar.button("QB Invoices", key="sidebar_invoices_button"):
        st.session_state.current_page = "InvoiceSelection"

    # Main page routing
    if st.session_state.current_page == "Welcome":
        show_welcome_page()
    elif st.session_state.current_page == "QB authentication":
        show_qb_authentication_page()
    elif st.session_state.current_page == "Journal_Entry":
        show_journal_entry_page()
    elif st.session_state.current_page == "InvoiceSelection":
        show_invoice_selection_page()
    elif st.session_state.current_page == "Daily Sales Export":
        show_daily_sales_export_page()
    elif st.session_state.current_page == "Distribution Invoices":
        show_distribution_invoices_page()


elif authentication_status == False:
    with st.sidebar:
        st.error('Username/password is incorrect')
elif authentication_status == None:
    with st.sidebar:
        st.warning('Please enter your username and password')

# stop the code flow if the authentication is not successful
if not authentication_status:
    st.stop()