import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import bcrypt
import sqlite3
import json


# Initialize database
def init_db():
    conn = sqlite3.connect('shop_management.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                (id INTEGER PRIMARY KEY, shop_name TEXT, date TEXT,
                 sales REAL, cash_out REAL, expenses TEXT, bank_deposit REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cheques 
                (id INTEGER PRIMARY KEY, date TEXT, shop_name TEXT,
                 amount REAL, payee TEXT, status TEXT)''')
    conn.commit()
    conn.close()

# Helper functions
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

def add_transaction(shop_name, date, sales, cash_out, expenses, bank_deposit):
    conn = sqlite3.connect('shop_management.db')
    c = conn.cursor()
    c.execute('''INSERT INTO transactions (shop_name, date, sales, cash_out, expenses, bank_deposit)
                VALUES (?, ?, ?, ?, ?, ?)''',
              (shop_name, date.strftime('%Y-%m-%d'), sales, cash_out, json.dumps(expenses), bank_deposit))
    conn.commit()
    conn.close()

def add_cheque(date, shop_name, amount, payee):
    conn = sqlite3.connect('shop_management.db')
    c = conn.cursor()
    c.execute('''INSERT INTO cheques (date, shop_name, amount, payee, status)
                VALUES (?, ?, ?, ?, ?)''',
              (date.strftime('%Y-%m-%d'), shop_name, amount, payee, 'Pending'))
    conn.commit()
    conn.close()

def get_transactions():
    conn = sqlite3.connect('shop_management.db')
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    return df

def get_cheques():
    conn = sqlite3.connect('shop_management.db')
    df = pd.read_sql_query("SELECT * FROM cheques", conn) 
    conn.close()
    return df

def calculate_bank_balance():
    conn = sqlite3.connect('shop_management.db')
    c = conn.cursor()
    c.execute("SELECT SUM(bank_deposit) FROM transactions")
    total_deposits = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM cheques WHERE status='Pending'")
    total_cheques = c.fetchone()[0] or 0
    conn.close()
    return total_deposits - total_cheques

# Initialize the database
init_db()

# Main app
def main():
    st.title('Business Management System')
    
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if st.session_state.user:
        st.sidebar.title(f"Welcome, {st.session_state.user}")
        st.sidebar.button("Logout", on_click=logout)
        
        # Display bank balance
        bank_balance = calculate_bank_balance()
        st.sidebar.metric("Bank Balance", f"LKR{bank_balance:.2f}")
        # Add 'Prediction' to the navigation menu


        # Navigation
        page = st.sidebar.selectbox('Navigate', ['Daily Sales', 'Bank Transactions', 'Sales Visualization', 'Prediction'])
        
        if page == 'Daily Sales':
            daily_sales_page()
        elif page == 'Bank Transactions':
            bank_transactions_page()
        elif page == 'Sales Visualization':
            sales_visualization_page()
        elif page == 'Prediction':
            prediction_page()
    else:
        auth_page()

def auth_page():
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.header("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            conn = sqlite3.connect('shop_management.db')
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE username = ?", (username,))
            result = c.fetchone()
            conn.close()
            if result and check_password(password, result[0]):
                st.session_state.user = username
                st.success("Logged in successfully!")
                
            else:
                st.error("Invalid username or password")
    
    with tab2:
        st.header("Sign Up")
        new_username = st.text_input("New Username", key="signup_username")
        new_password = st.text_input("New Password", type="password", key="signup_password")
        if st.button("Sign Up"):
            conn = sqlite3.connect('shop_management.db')
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ?", (new_username,))
            if c.fetchone():
                st.error("Username already exists")
            else:
                hashed_password = hash_password(new_password)
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (new_username, hashed_password))
                conn.commit()
                conn.close()
                st.success("Account created successfully! Please log in.")

def logout():
    st.session_state.user = None
   

def daily_sales_page():
    st.header("Daily Sales Entry")
    
    with st.form("sales_form"):
        shop_name = st.selectbox("Shop Name", ["Gampaha", "Nittambuwa"])
        date = st.date_input("Date", datetime.now().date())
        sales = st.number_input("Sales", min_value=0.0, step=0.01)
        cash_out = st.number_input("Cash Out", min_value=0.0, step=0.01)
        
        st.subheader("Expenses")
        expenses = {}
        for expense in ['Salary', 'Rent', 'Light Bill', 'Phone Bill', 'Water Bill', 'Petty Cash', 'Home', 'Other Expenses']:
            expenses[expense.lower().replace(' ', '_')] = st.number_input(expense, min_value=0.0, step=0.01)
        
        description = st.text_area("Description")
        expenses['description'] = description
        
        bank_deposit = st.number_input("Bank Deposit (Current Account)", min_value=0.0, step=0.01)
        
        submitted = st.form_submit_button("Submit")
        if submitted:
            add_transaction(shop_name, date, sales, cash_out, expenses, bank_deposit)
            st.success("Transaction added successfully!")

def bank_transactions_page():
    st.header("Bank Transactions")
    
    tab1, tab2 = st.tabs(["Bank Deposits", "Pass Cheque"])
    
    with tab1:
        st.subheader("Bank Deposits")
        df_deposits = get_transactions()
        if not df_deposits.empty:
            df_deposits = df_deposits[['date', 'shop_name', 'bank_deposit']]
            df_deposits = df_deposits[df_deposits['bank_deposit'] > 0]
            st.dataframe(df_deposits)
        else:
            st.info("No bank deposits recorded yet.")
    
    with tab2:
        st.subheader("Pass Cheque")
        with st.form("cheque_form"):
            date = st.date_input("Date", datetime.now().date())
            shop_name = st.selectbox("Shop Name", ["Gampaha", "Nittambuwa"])
            amount = st.number_input("Amount", min_value=0.01, step=0.01)
            payee = st.text_input("Payee")
            submitted = st.form_submit_button("Pass Cheque")
            if submitted:
                add_cheque(date, shop_name, amount, payee)
                st.success("Cheque passed successfully!")
        
        st.subheader("Cheque History")
        df_cheques = get_cheques()
        if not df_cheques.empty:
            st.dataframe(df_cheques)
        else:
            st.info("No cheques recorded yet.")

def sales_visualization_page():
    st.header("Sales Visualization")
    
    df = get_transactions()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df['expenses'] = df['expenses'].apply(json.loads)
        
        # Shop filter
        selected_shop = st.selectbox("Select Shop", ["All", "Gampaha", "Nittambuwa"])
        if selected_shop != "All":
            df = df[df['shop_name'] == selected_shop]
        
        # Monthly sales
        monthly_sales = df.groupby(df['date'].dt.to_period('M'))['sales'].sum().reset_index()
        monthly_sales['date'] = monthly_sales['date'].dt.to_timestamp()
        fig_monthly = px.bar(monthly_sales, x='date', y='sales', title='Monthly Sales')
        st.plotly_chart(fig_monthly)
        
        # Calculate net profit
        df['total_expenses'] = df['expenses'].apply(lambda x: sum(v for k, v in x.items() if k != 'description'))
        df['net_profit'] = df['sales'] - df['cash_out'] - df['total_expenses']
        monthly_profit = df.groupby(df['date'].dt.to_period('M'))['net_profit'].sum().reset_index()
        monthly_profit['date'] = monthly_profit['date'].dt.to_timestamp()
        fig_profit = px.line(monthly_profit, x='date', y='net_profit', title='Monthly Net Profit')
        st.plotly_chart(fig_profit)
        
        # Sales by shop
        shop_sales = df.groupby('shop_name')['sales'].sum().reset_index()
        fig_shop = px.pie(shop_sales, values='sales', names='shop_name', title='Sales by Shop')
        st.plotly_chart(fig_shop)
    else:
        st.info("No sales data available for visualization.")

def prediction_page():
    st.header("Sales Prediction")
    
    


    # Load prediction data
    predicted_stock = pd.read_csv('next_month_stock_predictions.csv')

    # Streamlit app
    st.title("Stock Quantity Prediction Application")

    st.sidebar.header("Filter Options")

    # Shop name selection
    shop_names = predicted_stock['ShopName'].unique()
    selected_shop = st.sidebar.selectbox("Select Shop Name", shop_names)

    # Filter by shop
    filtered_data = predicted_stock[predicted_stock['ShopName'] == selected_shop]

    # Item selection
    items = filtered_data['Item'].unique()
    selected_item = st.sidebar.selectbox("Select Item", items)

    # Filter by item
    item_data = filtered_data[filtered_data['Item'] == selected_item]

    # Display the prediction
    if not item_data.empty:
        predicted_quantity = item_data.iloc[0]['Predicted_Quantity']
        st.write(f"### Predicted Quantity for {selected_item} in {selected_shop}: {predicted_quantity}")
    else:
        st.write("No data available for the selected filters.")

    # Display the full dataset
    st.write("### Full Prediction Data")
    st.dataframe(predicted_stock)



if __name__ == "__main__":
    main()