import streamlit as st
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import calendar
from datetime import datetime
import sqlite3

#-----setting------#

incomes = ['saving', 'Blog', 'incentives']

expenses = ['Rent', 'Utilities', 'Groceries', 'Fuel', 'Other Expenses', 'Pocket Money']

currency = ' INR'

page_title = "Savings and Expense Tracker"

page_icon = "📊"

layout = "centered"

# Create a connection to the SQLite database
conn = sqlite3.connect("savings_expenses.db")
c = conn.cursor()

# Create a table to store data if it doesn't exist already
c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY,
                period TEXT,
                saving INTEGER,
                blog INTEGER,
                incentives INTEGER,
                rent INTEGER,
                utilities INTEGER,
                groceries INTEGER,
                fuel INTEGER,
                other_expenses INTEGER,
                pocket_money INTEGER,
                comment TEXT
            )''')

# Commit the changes and close the connection
conn.commit()
conn.close()

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>#

st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)

st.title(page_title + "" + page_icon)

hide_st_style = """
<style>
    #MainMenu {visibility:hidden;}
    footer{visibility:hidden;}
    header{visibility:hidden;}
</style>
"""

st.markdown(hide_st_style, unsafe_allow_html=True)


#>>>>>>>>>>>>>>>> Drop values <<<<<<<<<<<<<<<<<#

years = [datetime.today().year, datetime.today().year + 1]
months = list(calendar.month_name[1:])

#>>>>>> Page Navigation <<<<<<<<<<<<<#

selected = option_menu(
    menu_title=None,
    options=["Your Data", "Data Visualization"],
    icons=["pencil-fill", "bar-chart-fill"],
    orientation="horizontal",
    
)

#>>>>>>>>> input & save period <<<<<<<<<<<#

if selected == "Your Data":
    st.header(f"Data Entry in {currency}")

    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        col1.selectbox("select Month:", months, key="month")
        col2.selectbox("select Year:", years, key='year')

        #>>>>>>>>> Divider <<<<<<<<<#

        with st.expander("Income"):
            for income in incomes:
                st.number_input(f'{income}:', min_value=0, format='%i', step=10, key=income)

        with st.expander("Expenses"):
            for expense in expenses:
                st.number_input(f'{expense}:', min_value=0, format='%i', step=10, key=expense)

        with st.expander("Comment"):
            comment = st.text_area("", placeholder="Enter a comment here")

        #>>>>>> submit button <<<<<<<<<<<#

        submitted = st.form_submit_button("save data")

        if submitted:
            period = str(st.session_state["year"]) + "_" + str(st.session_state["month"])
            incomes = {income: st.session_state[income] for income in incomes}
            expenses = {expense: st.session_state[expense] for expense in expenses}

            # Insert data into the database
            conn = sqlite3.connect("savings_expenses.db")
            c = conn.cursor()
            c.execute('''INSERT INTO expenses (period, saving, blog, incentives, rent, utilities,
                          groceries, fuel, other_expenses, pocket_money, comment)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (period, incomes['saving'], incomes['Blog'], incomes['incentives'],
                       expenses['Rent'], expenses['Utilities'], expenses['Groceries'],
                       expenses['Fuel'], expenses['Other Expenses'], expenses['Pocket Money'],
                       comment))

            # Commit the changes and close the connection
            conn.commit()
            conn.close()

            st.write(f'Savings: {incomes}')
            st.write(f'Expenses: {expenses}')
            st.success("Data saved")

if selected == "Data Visualization":
    # After the line: comment = "some Comments"
    # Add code to retrieve data from the database

    # Get period options from the database
    conn = sqlite3.connect("savings_expenses.db")
    c = conn.cursor()
    c.execute('''SELECT DISTINCT period FROM expenses''')
    periods = [row[0] for row in c.fetchall()]
    conn.close()

    st.header("Data Visualization")
    with st.form("saved_periods"):
        period = st.selectbox("Select Period:", periods)
        submitted = st.form_submit_button("Plot Period")

        if submitted:
            # Retrieve data from the database
            conn = sqlite3.connect("savings_expenses.db")
            c = conn.cursor()

            # Get data for the selected period
            c.execute('''SELECT saving, blog, incentives, rent, utilities, groceries, fuel,
                          other_expenses, pocket_money, comment
                          FROM expenses WHERE period=?''', (period,))
            result = c.fetchone()

            # Close the connection
            conn.close()

            # Check if data exists for the selected period
            if result:
                incomes = {'saving': result[0], 'Blog': result[1], 'incentives': result[2]}
                expenses = {'Rent': result[3], 'Utilities': result[4], 'Groceries': result[5],
                            'Fuel': result[6], 'Other Expenses': result[7], 'Pocket Money': result[8]}
                comment = result[9]
            else:
                st.error("Data not found for the selected period.")

            # Rest of your code for data visualization remains the same
            total_income = sum(incomes.values())
            total_expense = sum(expenses.values())

            remaining_budget = total_income - total_expense

            col1, col2, col3 = st.columns(3)

            col1.metric("Total Saving", f"{total_income}{currency}")
            col2.metric("Total Expense", f"{total_expense}{currency}")
            col3.metric("Balance on Hand", f"{remaining_budget}{currency}")
            st.text(f'comment: {comment}')

            # Create sankey chart
            label = list(incomes.keys()) + ["Total Saving"] + list(expenses.keys())
            source = list(range(len(incomes))) + [len(incomes)] * len(expenses)
            target = [len(incomes)] * len(incomes) + [label.index(expense) for expense in expenses.keys()]
            value = list(incomes.values()) + list(expenses.values())

            # Data to dict, dict to sankey
            link = dict(source=source, target=target, value=value)
            node = dict(label=label, pad=20, thickness=30, color="#E694FF")
            data = go.Sankey(link=link, node=node)

            # Plot it!
            fig = go.Figure(data)
            fig.update_layout(margin=dict(l=0, r=0, t=5, b=5))
            st.plotly_chart(fig, use_container_width=True)
