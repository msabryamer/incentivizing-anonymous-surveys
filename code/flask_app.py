from flask import Flask, request, render_template_string
import pandas as pd
import os

app = Flask(__name__)

# Paths - Using absolute paths relative to this file for PythonAnywhere compatibility
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERIFY_CSV_PATH = os.path.join(BASE_DIR, 'data', 'verify_list.csv')
COLLECTED_CSV_PATH = os.path.join(BASE_DIR, 'data', 'collected_emails.csv')

def is_valid_email(email):
    """Simple verification: check for '@', '.', and that '.' comes after '@'."""
    if '@' in email and '.' in email:
        return email.rindex('.') > email.index('@')
    return False

def load_verify_list():
    try:
        verify_list = pd.read_csv(VERIFY_CSV_PATH)
        return [str(val).strip().lower() for val in verify_list.iloc[:, 0].values]
    except FileNotFoundError:
        return None

def load_collected_emails(has_verify_list=False):
    if os.path.exists(COLLECTED_CSV_PATH):
        return pd.read_csv(COLLECTED_CSV_PATH)
    else:
        if has_verify_list:
            return pd.DataFrame(columns=['email', 'username', 'verified', 'referrer'])
        else:
            return pd.DataFrame(columns=['email', 'referrer'])

def save_collected_emails(df):
    df.to_csv(COLLECTED_CSV_PATH, index=False)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Incentivizing Anonymous Surveys</title>
    <style>
        /* Modern Premium CSS inspired by our Streamlit design */
        body {
            font-family: 'Inter', 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            color: #2c3e50;
        }
        .container {
            background-color: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.1);
            max-width: 400px;
            width: 100%;
            text-align: center;
        }
        h1 {
            font-size: 24px;
            margin-bottom: 10px;
            font-weight: 700;
        }
        p.subtitle {
            font-size: 16px;
            color: #7f8c8d;
            margin-bottom: 30px;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            margin-bottom: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-sizing: border-box;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            border-color: #3498db;
            box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
        }
        button {
            width: 100%;
            padding: 12px;
            background-color: #2c3e50;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover {
            background-color: #34495e;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .alert {
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 8px;
            font-size: 14px;
            text-align: left;
        }
        .alert-error {
            background-color: #fdecea;
            color: #e74c3c;
            border: 1px solid #fad2cf;
        }
        .alert-warning {
            background-color: #fef5e7;
            color: #f39c12;
            border: 1px solid #fdebd0;
        }
        .alert-success {
            background-color: #eafaf1;
            color: #27ae60;
            border: 1px solid #d5f5e3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎁 Survey Reward Entry</h1>
        <p class="subtitle">Thank you for participating! Enter your email below to claim your reward or enter the raffle.</p>
        
        {% if message %}
            <div class="alert alert-{{ message_type }}">{{ message }}</div>
        {% endif %}

        {% if message_type != 'success' %}
        <form method="POST" action="/">
            {% if ask_username %}
            <input type="text" name="username" placeholder="e.g., your_username" required>
            {% endif %}
            <input type="text" name="email" placeholder="e.g., user@example.com" required>
            <button type="submit">Submit Entry</button>
        </form>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None
    message_type = None
    ask_username = os.path.exists(VERIFY_CSV_PATH)

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip().lower() if ask_username else None
        referrer = request.referrer or ""
        
        if not email:
            message = "⚠️ Please enter an email address."
            message_type = "warning"
        elif not is_valid_email(email):
            message = "❌ Invalid email format. Please check your spelling and try again."
            message_type = "error"
        elif ask_username and not username:
            message = "⚠️ Please enter a username."
            message_type = "warning"
        else:
            verify_list = load_verify_list()
            collected_emails = load_collected_emails(has_verify_list=ask_username)
            
            # Check if already submitted email
            if not collected_emails.empty and email in collected_emails['email'].str.lower().values:
                message = "⚠️ This email has already been submitted."
                message_type = "warning"
                
                # Still shuffle and save to decouple submission timing
                if len(collected_emails) > 1:
                    collected_emails = collected_emails.sample(frac=1).reset_index(drop=True)
                save_collected_emails(collected_emails)
            else:
                if ask_username:
                    # Drop old row if username matches
                    if not collected_emails.empty and 'username' in collected_emails.columns:
                        if username in collected_emails['username'].str.lower().values:
                            collected_emails = collected_emails[collected_emails['username'].str.lower() != username]
                            
                    is_verified = 1 if (verify_list is not None and username in verify_list) else 0
                    new_row = pd.DataFrame({'email': [email], 'username': [username], 'verified': [is_verified], 'referrer': [referrer]})
                else:
                    new_row = pd.DataFrame({'email': [email], 'referrer': [referrer]})
                    
                collected_emails = pd.concat([collected_emails, new_row], ignore_index=True)
                
                # SHUFFLE the DataFrame to decouple submission time/order from the email
                if len(collected_emails) > 1:
                    collected_emails = collected_emails.sample(frac=1).reset_index(drop=True)
                
                # Save
                save_collected_emails(collected_emails)
                
                message = "🎉 Success! Your entry has been recorded."
                message_type = "success"

    return render_template_string(HTML_TEMPLATE, message=message, message_type=message_type, ask_username=ask_username)

if __name__ == '__main__':
    app.run(debug=True)
