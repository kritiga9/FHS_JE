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


# https://blog.streamlit.io/streamlit-authenticator-part-1-adding-an-authentication-component-to-your-app/

@st.cache_data
def read_df(table_id, filter_col_name=None, filter_col_value=None, index_col=None, date_col=None, dtype=None):
    keboola_client.tables.export_to_file(table_id, '.')
    table_name = table_id.split(".")[-1]
    #st.write(filter_col_value)
    df = pd.read_csv(table_name, index_col=index_col, parse_dates=date_col, dtype=dtype, keep_default_na=False, na_values=[''])
    if filter_col_name:
        return df.loc[df[filter_col_name]==filter_col_value]
    else:
        return df

def determine_step(username):
    status_df = read_df(STATUS_TAB_ID, "entity_name", username)    
    authorization = status_df.loc[status_df["entity_name"]==username, "config_has_data"].values[0]
    report_tracking = (status_df.loc[status_df["entity_name"]==username, "report_tracking"].values[0])
    if authorization==1 or report_tracking=='None':
        step = 2
    else:
        step = 1
    return step    
    
#@st.cache_data
def parse_credentials():
    """
    The method takes credentials from streamlit secret and converts
    these into a dictionary compatible with streamlit authenticator

    Returns
    -------
    config_dict - dictionary containing information about credentials formatted
    for stauth
    
    NOTE
    ----
    advanced features of stauth are not currently implemented beyond the simplest
    use. For instance, no preauthorized users or passwords expiry

    """
    config_dict = {}
        
    keys_to_exclude = ["kbc_token_master", "kbc_url", "token"]
    filtered_secrets = {key: st.secrets[key] for key in st.secrets if key not in keys_to_exclude}
    # Convert the input dictionary into the desired format
    config_dict = {
        "credentials": {
            "usernames": {
                username: {
                    
                        "name": username,
                        "password": password
                    
                }
                for username, password in filtered_secrets.items()
            }
        }
    }

    config_dict["cookie"] = {'expiry_days':0,
                                'key':"random_signature_key",
                                'name':"random_cookie_name"}

    config_dict["preauthorized"] = {'emails':["melsby@gmail.com"]}
    
    return config_dict

class Authenticate:
    """
    This class will create login, logout, register user, reset password, forgot password, 
    forgot username, and modify user details widgets.
    """
    def __init__(self, credentials: dict, cookie_name: str, key: str, cookie_expiry_days: float=30.0, 
        preauthorized: list=None):
        """
        Create a new instance of "Authenticate".

        Parameters
        ----------
        credentials: dict
            The dictionary of usernames, names, passwords, and emails.
        cookie_name: str
            The name of the JWT cookie stored on the client's browser for passwordless reauthentication.
        key: str
            The key to be used for hashing the signature of the JWT cookie.
        cookie_expiry_days: float
            The number of days before the cookie expires on the client's browser.
        preauthorized: list
            The list of emails of unregistered users authorized to register.
        validator: Validator
            A Validator object that checks the validity of the username, name, and email fields.
        """
        self.credentials = credentials
        self.credentials['usernames'] = {key: value for key, value in credentials['usernames'].items()}
        self.cookie_name = cookie_name
        self.key = key
        self.cookie_expiry_days = cookie_expiry_days
        self.preauthorized = preauthorized
        self.cookie_manager = stx.CookieManager()
        #self.validator = validator if validator is not None else Validator()

        if 'name' not in st.session_state:
            st.session_state['name'] = None
        if 'authentication_status' not in st.session_state:
            st.session_state['authentication_status'] = None
        if 'username' not in st.session_state:
            st.session_state['username'] = None
        if 'logout' not in st.session_state:
            st.session_state['logout'] = None

    def _token_encode(self) -> str:
        """
        Encodes the contents of the reauthentication cookie.

        Returns
        -------
        str
            The JWT cookie for passwordless reauthentication.
        """
        return jwt.encode({'name':st.session_state['name'],
            'username':st.session_state['username'],
            'exp_date':self.exp_date}, self.key, algorithm='HS256')

    def _token_decode(self) -> str:
        """
        Decodes the contents of the reauthentication cookie.

        Returns
        -------
        str
            The decoded JWT cookie for passwordless reauthentication.
        """
        try:
            return jwt.decode(self.token, self.key, algorithms=['HS256'])
        except:
            return False

    def _set_exp_date(self) -> str:
        """
        Creates the reauthentication cookie's expiry date.

        Returns
        -------
        str
            The JWT cookie's expiry timestamp in Unix epoch.
        """
        return (datetime.utcnow() + timedelta(days=self.cookie_expiry_days)).timestamp()

    def _check_pw(self) -> bool:
        """
        Checks the validity of the entered password.

        Returns
        -------
        bool
            The validity of the entered password by comparing it to the hashed password on disk.
        """
        return st.session_state["username"] in st.secrets and hmac.compare_digest(
            st.session_state["password"],
            st.secrets[st.session_state["username"]],
        )

    def _check_cookie(self):
        """
        Checks the validity of the reauthentication cookie.
        """
        self.token = self.cookie_manager.get(self.cookie_name)
        if self.token is not None:
            self.token = self._token_decode()
            if self.token is not False:
                if not st.session_state['logout']:
                    if self.token['exp_date'] > datetime.utcnow().timestamp():
                        if 'name' and 'username' in self.token:
                            st.session_state['name'] = self.token['name']
                            st.session_state['username'] = self.token['username']
                            st.session_state['authentication_status'] = True
    
    def _check_credentials(self, inplace: bool=True) -> bool:
        """
        Checks the validity of the entered credentials.

        Parameters
        ----------
        inplace: bool
            Inplace setting, True: authentication status will be stored in session state, 
            False: authentication status will be returned as bool.
        Returns
        -------
        bool
            Validity of entered credentials.
        """
        if self.username in self.credentials['usernames']:
            try:
                if self._check_pw():
                    if inplace:
                        st.session_state['name'] = self.credentials['usernames'][self.username]['name']
                        self.exp_date = self._set_exp_date()
                        self.token = self._token_encode()
                        self.cookie_manager.set(self.cookie_name, self.token,
                            expires_at=datetime.now() + timedelta(days=self.cookie_expiry_days))
                        st.session_state['authentication_status'] = True
                    else:
                        return True
                else:
                    if inplace:
                        st.session_state['authentication_status'] = False
                    else:
                        return False
            except Exception as e:
                print(e)
        else:
            if inplace:
                st.session_state['authentication_status'] = False
            else:
                return False

    def login(self, form_name: str, location: str='main') -> tuple:
        """
        Creates a login widget.

        Parameters
        ----------
        form_name: str
            The rendered name of the login form.
        location: str
            The location of the login form i.e. main or sidebar.
        Returns
        -------
        str
            Name of the authenticated user.
        bool
            The status of authentication, None: no credentials entered, 
            False: incorrect credentials, True: correct credentials.
        str
            Username of the authenticated user.
        """
        if not st.session_state['authentication_status']:
            self._check_cookie()
            if not st.session_state['authentication_status']:
                login_form = st.form('Login')


                login_form.subheader(form_name)
                self.username = login_form.text_input('Username')
                st.session_state['username'] = self.username
                self.password = login_form.text_input('Password', type='password')
                st.session_state['password'] = self.password

                if login_form.form_submit_button('Login'):
                    self._check_credentials()
        return st.session_state['name'], st.session_state['authentication_status'], st.session_state['username']

    def logout(self, button_name: str, location: str='main', key: str=None):
        """
        Creates a logout button.

        Parameters
        ----------
        button_name: str
            The rendered name of the logout button.
        location: str
            The location of the logout button i.e. main or sidebar.
        """
        if location == 'main':
            if st.button(button_name, key):
                self.cookie_manager.delete(self.cookie_name)
                st.session_state['logout'] = True
                st.session_state['name'] = None
                st.session_state['username'] = None
                st.session_state['authentication_status'] = None

def data_issues():
    st.error("""Downloading data from Quickbooks is not yet ready. Our team is monitoring the progress. 
             For more information, please check your inbox and look for ticket Request #27324 """)

def write_file_submit_authorization(status_df, 
                              company_id=None, 
                              financial_calendar=None, 
                              tracking_selection = None,
                              file_path=".dev_status.csv"):
    """
    

    Parameters
    ----------
    status_df : TYPE
        DESCRIPTION.
    company_id : TYPE
        DESCRIPTION.
    financial_calendar : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """  

    if not company_id:
        company_id = st.session_state.get("company_id", "").replace(" ","")
    
    if not financial_calendar:
        financial_calendar = st.session_state.get("custom_calendar", False)

    if not tracking_selection:
        tracking_selection = st.session_state.get('report_tracking',"")
    

    
    status_df["company_id"]=company_id
    status_df["custom_calendar"] = int(financial_calendar)
    status_df["authorization_timestamp"] = str(datetime.datetime.now())
    status_df["report_tracking"] = tracking_selection
    status_df.to_csv(file_path, index=False)
    
    return None
    #status_df[""]
         
def update_status_table(
        keboola_client=keboola_client,
        #keboola_key,
        table_id=STATUS_TAB_ID,
    #    bucket_id,
        file_path='.dev_status.csv',
        #primary_key='config_id',
        is_incremental=True, 
        delimiter=',',
        enclosure='"', 
        escaped_by='', 
        columns=['username'],
        without_headers=False
        ):
    
    #client = Client(keboola_URL, keboola_key)
    # check whether a table in the bucket exists. If so, retrieve its table_id
    
    res = keboola_client.tables.load(table_id=table_id,
                        file_path=file_path,
                        is_incremental=is_incremental, 
                        delimiter=delimiter,
                        enclosure=enclosure, 
                        escaped_by=escaped_by,
                        columns=columns,
                        without_headers=without_headers) 

    return res, f"table {table_id} has been updated."
    
    
def check_config_values():
    
    if (
            (st.session_state["company_id"]==st.session_state["company_id_old"]) or 
            (st.session_state["company_id_old"] in [None, ""])) and (
            (st.session_state["custom_calendar"]==st.session_state["custom_calendar_old"]) or
            (st.session_state["custom_calendar_old"]  in [None, ""])
        ) and (
            (st.session_state["report_tracking"]==st.session_state["report_tracking_old"]) or
            (st.session_state["report_tracking_old"]  in [None, ""])):
        return 1
    else:
        return 0
    
        
        
    # fill logic for custom calendar
def prepare_mapping_file(status_df, file_path='.mapping.csv'):
    
    username = status_df.entity_name.values[0]
    #class_{i}
    
    classes = sorted([ k for k in st.session_state.keys() if k.startswith('class_')])
    locations = sorted([ k for k in st.session_state.keys() if k.startswith('location_')])

   # old_classes = sorted([ k for k in st.session_state.keys() if k.startswith('old_class_')])
   # old_locations = sorted([ k for k in st.session_state.keys() if k.startswith('old_location_')])
    
    
    to_dict = []
    
    mapping_timestamp = str(datetime.datetime.now())
    for c, l in zip(classes, locations):
        inner_dict = {}
        inner_dict['entity_name'] = username
        inner_dict['class_dep'] = st.session_state[c]
        inner_dict['location'] = st.session_state[l]
        inner_dict['timestamp'] = mapping_timestamp
        to_dict.append(inner_dict)
        
    mapdf = pd.DataFrame(to_dict)
    mapdf.to_csv(file_path, index=False)
    return file_path

def create_or_update_table(table_name,
        keboola_client=keboola_client,
        bucket_id=STREAMLIT_BUCKET_ID,
        file_path='.mapping.csv',
        primary_key='xxx', # define primary key
        is_incremental=True, 
        delimiter=',',
        enclosure='"', 
        escaped_by='', 
        columns=["entity_name", "class_dep"],
        without_headers=False):
    """
    The function creates or incrementally updates the mapping table. 
    Mapping table should be keyed by hash(config_id+class)

    Parameters
    ----------
    table_name : TYPE
        DESCRIPTION.
    keboola_client : TYPE, optional
        DESCRIPTION. The default is keboola_client.
    bucket_id : TYPE, optional
        DESCRIPTION. The default is 'out.c-create_configs'.
    file_path : TYPE, optional
        DESCRIPTION. The default is '.mapping.csv'.
    primary_key : TYPE, optional
        DESCRIPTION. The default is 'xxx'.
    # define primary key        is_incremental : TYPE, optional
        DESCRIPTION. The default is False.
    delimiter : TYPE, optional
        DESCRIPTION. The default is ','.
    enclosure : TYPE, optional
        DESCRIPTION. The default is '"'.
    escaped_by : TYPE, optional
        DESCRIPTION. The default is ''.
    columns : TYPE, optional
        DESCRIPTION. The default is None.
    without_headers : TYPE, optional
        DESCRIPTION. The default is False.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    
    # check whether a table in the bucket exists. If so, retrieve its table_id
    try:
        try:
            tables = keboola_client.tables.list()

        except Exception as e:
            return str(e)
        # there will be 0 or 1 hit
        table_def = list(filter(lambda x: x['bucket']['id']==bucket_id and x['name']==table_name, tables))
        if table_def:
            table_id = table_def[0]['id']
            # table already exists --> load
            try:
                _= keboola_client.tables.load(table_id=table_id,
                                    file_path=file_path,
                                    is_incremental=is_incremental, 
                                    delimiter=delimiter,
                                    enclosure=enclosure, 
                                    escaped_by=escaped_by,
                                    columns=columns,
                                    without_headers=without_headers) 
                return True, f"{table_name} table has been updated."
            except Exception as e:
                return False, str(e)    
        else:
            # table does not exist --> create
            try:
                return True, keboola_client.tables.create(name=table_name,
                                    bucket_id=bucket_id,
                                    file_path=file_path,
                                    primary_key=columns) + " table has been successfully created!!"
            except Exception as e:
                return False, str(e)   
    except Exception as e:
        return False, str(e)     

def trigger_flow(api_token, config_id, component_name):
    headers = {
        'accept': 'application/json',
        'X-KBC-RunId': '',  # Set the appropriate run ID if available
        'X-StorageApi-Token': api_token,
        'Content-Type': 'application/json'
    }
    payload = json.dumps({
        "component": component_name,
        "mode": "run",
        "config": config_id
    })

    url = "https://queue.keboola.com/jobs"
    try:
        # Check if a job is already running for the config_id
        if is_job_running(api_token, config_id):
            print("A job is already running for the current config_id. Skipping job creation.")
            return None

        # Create a new job
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 201:
            job_data = response.json()
            run_id = job_data.get("id")
            print("Flow for mapping is triggered")
            return response.json()
        else:
            print(f"Error - Response code: {response.status_code}, JSON: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error - {e}")

def is_job_running(api_token, config_id):
    headers = {
        'accept': 'application/json',
        'X-StorageApi-Token': api_token,
    }
    url = f"https://queue.keboola.com/jobs"
    try:
        response = requests.get(url, headers=headers, params={"config": config_id, "status": "running"})
        if response.status_code == 200:
            job_data = response.json()
            return len(job_data) > 0
        else:
            print(f"Error - Response code: {response.status_code}, JSON: {response.json()}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error - {e}")
        return False
    
###Functions for Phase2 of the App (showing naigation and pages)

#restaurants_filtered = read_df(RESTAURANTS_TAB_ID, filter_col_name="entity_name", filter_col_value=name)

        #Restaurants should be filtered based on the list of entities 
        #And entities should be filtered based on the Username
        #As we don't have a list yet, I took FHS_CORP entity
    #restaurants_filtered = restaurant_aux[restaurant_aux['entity_name'] == 'FHS_CORP']['Restaurant'].unique().tolist()

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

# def show_journal_entry_page():
#     st.title("Select a Location for Journal Entry")
#     locations = restaurants_filtered
#     for location in locations:
#         if st.button(location):
#             st.session_state.selected_location = location
#             st.session_state.current_page = "Daily Sales Export"
#             st.experimental_rerun()
    

# def show_invoice_selection_page():
#     st.title("Select a Location for Invoice")
#     locations = restaurants_filtered
#     for location in locations:
#         if st.button(location):
#             st.session_state.selected_location = location
#             st.session_state.current_page = "Distribution Invoices"
#             st.experimental_rerun()

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