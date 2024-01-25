import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from src.settings import STATUS_TAB_ID, MAPPING_CLASSES_TAB_ID,MAPPING_TAB_ID, DEBUG, RESTAURANTS_TAB_ID, DAILY_SALES
from src.helpers import parse_credentials
from src.helpers import read_df
from src.helpers import determine_step
from src.helpers_2 import show_welcome_page, show_qb_authentication_page,  show_daily_sales_export_page, show_distribution_invoices_page ,show_journal_entry_page, show_invoice_selection_page, show_journal_entry
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
        
    restaurants_filtered = read_df(RESTAURANTS_TAB_ID, filter_col_name="entity_name", filter_col_value=name)
    
    status_df = read_df(STATUS_TAB_ID, filter_col_name="entity_name", filter_col_value=name, dtype={'config_id':str})
    config_id = status_df["config_id"].iloc[0]
    
    ### TIME testing - placeholders for other time testing
    #here i take entity name as is 
    # First approach
    # start_time = time.time()
    # # Your first block of code
    # ACCOUNTS_TAB_ID = f'in.c-kds-team-ex-quickbooks-online-fhs-quickbooks-{name}.Account'
    # accounts = read_df(ACCOUNTS_TAB_ID)['FullyQualifiedName']
    # end_time = time.time()
    # time_taken_first = end_time - start_time
    # st.write(f"Time taken by the first approach: {time_taken_first} seconds")
    # st.write(accounts)

    ##TIME TESTING END
        
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
        # Show JE dates without choosing location if entity doesn't have classes/depts
        if status_df["report_tracking"].iloc[0] == "None":
            # If report_tracking is "None", automatically set the selected location
            if 'selected_location' not in st.session_state or st.session_state.selected_location not in restaurants_filtered['Restaurant'].values:
                st.session_state.selected_location = restaurants_filtered['Restaurant'].iloc[0]
            show_daily_sales_export_page(name)
        else:
            # Show the page for choosing a location
            show_journal_entry_page(restaurants_filtered)
    elif st.session_state.current_page == "InvoiceSelection":
        show_invoice_selection_page(restaurants_filtered)
    elif st.session_state.current_page == "Daily Sales Export":
        show_daily_sales_export_page(name)
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