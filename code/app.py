import streamlit as st
import pandas as pd
import os

# Page Configuration
st.set_page_config(page_title="Incentivizing Anonymous Surveys", page_icon="🎁", layout="centered")

# Custom CSS for Premium Design
st.markdown("""
<style>
    /* Button styling */
    .stButton>button {
        background-color: #2c3e50;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        transition: 0.3s;
        width: 100%;
        font-weight: 600;
        font-size: 16px;
    }
    .stButton>button:hover {
        background-color: #34495e;
        box-shadow: 0 4px 12px 0 rgba(0,0,0,0.15);
        transform: translateY(-2px);
        color: white;
    }
    
    /* Header typography - forcing color to adapt well to light/dark themes */
    h1 {
        text-align: center;
        font-family: 'Inter', 'Helvetica Neue', sans-serif;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .subtitle-text {
        text-align: center;
        font-size: 18px;
        margin-bottom: 25px;
        opacity: 0.8;
    }
</style>
""", unsafe_allow_html=True)

# Define paths relative to the project root (assuming Streamlit is run from the root directory)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ELIGIBLE_CSV_PATH = os.path.join(BASE_DIR, 'data', 'email_list.csv')
COLLECTED_CSV_PATH = os.path.join(BASE_DIR, 'data', 'collected_emails.csv')

def is_valid_email(email):
    """Simple verification: check for '@', '.', and that '.' comes after '@'."""
    if '@' in email and '.' in email:
        return email.rindex('.') > email.index('@')
    return False

# Helper Functions
@st.cache_data
def load_eligible_emails():
    try:
        email_list = pd.read_csv(ELIGIBLE_CSV_PATH)
        # Clean and lower case emails from the first column
        return [str(email).strip().lower() for email in email_list.iloc[:, 0].values]
    except FileNotFoundError:
        st.error(f"Error: Could not find eligible email list at `data/email_list.csv`.")
        return []

def load_collected_emails():
    if os.path.exists(COLLECTED_CSV_PATH):
        return pd.read_csv(COLLECTED_CSV_PATH)
    else:
        return pd.DataFrame(columns=['email', 'verified'])

def save_collected_emails(df):
    df.to_csv(COLLECTED_CSV_PATH, index=False)

# UI Layout
st.markdown("<h1>Survey Reward Entry</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle-text'>Thank you for participating! Enter your email below to claim your reward or enter the raffle.</p>", unsafe_allow_html=True)

eligible_emails = load_eligible_emails()

with st.form("reward_entry_form", clear_on_submit=True):
    email_input = st.text_input("University Email Address", placeholder="e.g., student@uchicago.edu")
    submitted = st.form_submit_button("Submit Entry")

if submitted:
    email = email_input.strip().lower()
    
    if not email:
        st.warning("⚠️ Please enter an email address.")
    elif not is_valid_email(email):
        st.error("❌ Invalid email format. Please check your spelling and try again.")
    else:
        collected_emails = load_collected_emails()
        
        # Check if already submitted
        if not collected_emails.empty and email in collected_emails['email'].str.lower().values:
            st.warning("⚠️ This email has already been submitted.")
            # Still shuffle and save to decouple submission timing
            if len(collected_emails) > 1:
                collected_emails = collected_emails.sample(frac=1).reset_index(drop=True)
            save_collected_emails(collected_emails)
        else:
            # Check eligibility (verified=1 if in list, else 0)
            is_verified = 1 if email in eligible_emails else 0
            
            # Add new email
            new_row = pd.DataFrame({'email': [email], 'verified': [is_verified]})
            collected_emails = pd.concat([collected_emails, new_row], ignore_index=True)
            
            # SHUFFLE the DataFrame to decouple submission time/order from the email
            if len(collected_emails) > 1:
                collected_emails = collected_emails.sample(frac=1).reset_index(drop=True)
            
            # Save
            save_collected_emails(collected_emails)
            
            st.success("🎉 Success! Your email has been recorded.")
            st.balloons()
