from email.quoprimime import body_check
import json
import hmac
import base64
import requests
import pandas as pd
from hashlib import sha1
from datetime import datetime
import streamlit as st


def gmt_date():
  '''
  Generates date string, i.e. 
  "Tue, 24 May 2022 18:52:29 GMT"
  '''
  return datetime.utcnow().strftime("%a, %d %b %Y %X GMT")


def checksum_string(endpoint, date, content_type='application/json', content_md5=''):
  '''
  Generates a string with the following format:
  'content_type,content_md5,endpoint,date'

  Only the endpoint is needed, the date is generated on call, and 
  content_type & conten_md5 are default values.

  :param1 endpoint: str - endpoint to be called.
  :param2 content_type: str - default is application/json.
  :param3 content_md: str - default is empty str.
  '''
  return f'{content_type},{content_md5},{endpoint},{date}'


def generate_checksum(checksum_str, secret_key):
  checksum_bytes = bytes(checksum_str.encode('utf-8'))
  secret_bytes = bytes(secret_key.encode('utf-8'))
  hash = hmac.new(secret_bytes, checksum_bytes, sha1).digest()
  return base64.b64encode(hash).decode("utf-8")


#Headers
accept = 'application/vnd.regalii.v3.2+json'
content_type = 'application/json'
content_md5 = ''
date = gmt_date()

API_KEY = st.secrets['API_KEY']
SECRET_KEY = st.secrets['SECRET_KEY']

def api_x_request(method,endpoint,payload=None,search_for=None):
  base_url = 'https://apix.staging.arcusapi.com'
  url = f'{base_url}{endpoint}'

  checksum_str = checksum_string(endpoint=endpoint,date=date)
  auth_checksum = generate_checksum(checksum_str,SECRET_KEY)

  headers = {
      'Accept':        accept,
      'Content-Type':  content_type,
      'Content-MD5':   content_md5,
      'Date':          date,
      'Authorization': f'APIAuth {API_KEY}:{auth_checksum}'
  }

  if method == 'GET':

    payload_pay = {
    "q":{"name_cont":search_for}
    }

    payload_pay = json.dumps(payload_pay)
    
    res = requests.get(url,headers=headers,data=payload_pay)

  if method == 'POST':
    res = requests.get(url,headers=headers,data=payload)

  return res.json()  

def get_billers():
    url = f'/biller_directory'
    return api_x_request('GET', url)

@st.cache
def convert_df(df):
  # IMPORTANT: Cache the conversion to prevent computation on every rerun
  return df.to_csv().encode('utf-8')

# MAIN APP

st.image("https://arcus-website-s3-assets.s3.amazonaws.com/content/2022/03/02/ccaeArcus-MC_logo.svg",width=300)
st.text("")
st.text("")

st.sidebar.header('Biller Finder')
st.sidebar.subheader('Billpay US')

search = st.sidebar.text_input('Seach for a Biller',help='Press "Enter" to apply changes')

classes = ['Homeowners Association',
 'Rental Properties',
 'Other',
 'Personal Banking (checking, savings, etc.)',
 'Bank Card',
 'Retail',
 'Electric / Gas / Power / Water',
 'Healthcare Services',
 'Insurance',
 'Club / Membership',
 'School / Car / Bank Loan & Finance',
 'Financial Services']

selected_classes = st.sidebar.multiselect('Select biller class:',options=classes,default=classes,help='You can select multiple or only one biller class.')

if not search:
  st.warning('Use the text box to look for specific billers')

#if click:

billers = api_x_request('GET','/biller_directory',search_for=search)
billers = billers['rpps_billers']

for biller in billers:
  name = biller['name']
  if biller["biller_class"] in selected_classes:
    st.write(f'### {name}')
    st.caption(f'ID: {biller["id"]}')
    col1,col2 = st.columns(2)
    with col1:
      st.write(f'Class: {biller["biller_class"]}')
    with col2:
      st.write(f'Type: {biller["biller_type"]}')
    mask_df = pd.DataFrame(biller['masks'])
    with st.expander('See available mask formats'):
      mask_df
      st.download_button(
        label=f"Download {name} mask data ",
        data=convert_df(mask_df),
        file_name=f'{name}_mask_data.csv',
        mime='text/csv')
    '---'

st.sidebar.info('''
Read the documentation: 
[API Docs](https://docs.arcusfi.com/api-x/3.2/)
''')