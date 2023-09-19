import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
from google.oauth2 import service_account
import base64
import datetime

def check_password():
    """Returns `True` if the user had a correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
            st.session_state["username"] in st.secrets["passwords"]
            and st.session_state["password"]
            == st.secrets["passwords"][st.session_state["username"]]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store username + password
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():
    # Define your Google Sheets credentials JSON file (replace with your own)
    credentials_path = 'collection20-aa5f3fb7835e.json'
    
    # Authenticate with Google Sheets using the credentials
    credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=['https://spreadsheets.google.com/feeds'])
    
    # Authenticate with Google Sheets using gspread
    gc = gspread.authorize(credentials)
    
    # Your Google Sheets URL
    url = "https://docs.google.com/spreadsheets/d/1i5HsneT9vpPREVo-ED_HwLLkPpsSjKVY0vuilehDXxg/edit#gid=0"
    
    # Open the Google Sheets spreadsheet
    worksheet = gc.open_by_url(url).worksheet("assign")
    
    # Add a sidebar
    st.sidebar.image('corplogo.PNG', use_column_width=True)
    st.sidebar.markdown("Navigation Pane")
    
    # Main Streamlit app code
    def main(): 
        # Create a sidebar to switch between views
        view = st.sidebar.radio("Select", ["Dashboard", "New Record", "Records"])
    
        if view == "Dashboard":
            st.subheader("PREMIUM COLLECTION UPDATE APPLICATION")
    
            # Read data from the Google Sheets worksheet
            data = worksheet.get_all_values()
    
           # Prepare data for Plotly
            headers = data[0]
            data = data[1:]
            df = pd.DataFrame(data, columns=headers)  # Convert data to a DataFrame
            x_data = df['Person Allocated']
            y_data = df['Outstanding Amount']

            # Assuming your DataFrame is named 'df'
            df['Delete'] = [''] * len(df)

            # Convert the "Amount Collected" column to numeric
            df['Amount Collected'] = pd.to_numeric(df['Amount Collected'])

            highest_collector = df['Person Allocated'].mode().values[0]
            frequent_category_count = df[df['Person Allocated'] == highest_collector].shape[0]

            most_collected = df.groupby('Person Allocated')['Amount Collected'].sum().reset_index()

            # Sort by the sum of 'Amount Collected' in descending order
            result = most_collected.sort_values(by='Amount Collected', ascending=False)

            # Get the person with the highest sum
            highest_person = result.head(1)

            name = highest_person['Person Allocated'].values[0]
            highest_collected_amount = highest_person['Amount Collected'].values[0]

            # Format highest_collected_amount as an integer with a thousands separator
            formatted_highest_collected_amount = "Ksh. {:,.0f}".format(highest_collected_amount)

            current_date = datetime.datetime.now()
            start_of_week = current_date - datetime.timedelta(days=current_date.weekday())
            end_of_week = start_of_week + datetime.timedelta(days=6)
            
            week = df[(pd.to_datetime(df['Date']).dt.date >= start_of_week.date()) & (pd.to_datetime(df['Date']).dt.date <= end_of_week.date())]
            weekly_amount = week["Amount Collected"].sum()

            st.markdown(
                f'<div style= "display: flex; flex-direction: row;">'  # Container with flex layout
                f'<div style="background-color: #f19584; padding: 10px; border-radius: 10px; width: 250px; margin-right: 20px;">'
                f'<strong style="color: black;">CONTACTED MOST DEBTORS</strong> <br>'
                f"{highest_collector}<br>"
                f"{frequent_category_count} accounts<br>"
                f'</div>'
                f'<div style="background-color: #E7BDFF; padding: 10px; border-radius: 10px; width: 250px; margin-right: 20px;">'
                f'<strong style="color: black;">HIGHEST COLLECTOR</strong> <br>'
                f"{name}<br>"
                f"{formatted_highest_collected_amount}<br>"
                f'</div>'
                f'<div style="background-color: #EFE9AB; padding: 10px; border-radius: 10px; width: 250px; margin-right: 20px;">'
                f'<strong style="color: black;">THIS WEEK COLLECTION</strong> <br>'  
                f"<br>"
                f"{weekly_amount}<br>"
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # Create a Plotly bar graph
            fig = px.bar(x=x_data, y=y_data, labels={'x': 'Person Allocated', 'y': 'Outstanding Amount'})
            fig.update_layout(title={'text': 'OUTSTANDING AMOUNTS PER PERSON ALLOCATED', 'x': 0.5, 'xanchor': 'center'}) 

            # Display the Plotly bar graph in Streamlit
            st.markdown("")
            st.plotly_chart(fig)

        elif view == "New Record":
            # Add the dashboard elements here
            st.subheader("NEW ITEM")

            # Create form fields for user input
            date = st.date_input("Date")
            intermediary = st.text_input("Intermediary")
            persons = st.selectbox("Persons Allocated:",["Samuel Kangi", "David Masui", "Chrispus Boro", "Collins Chetekei", "Dennis Amdany"])
            outstanding = st.number_input("Outstanding Amount")
            collected = st.number_input("Amount Collected")
            actions = st.text_area("Actions")
            review = st.selectbox("Reviewed by:",["Samuel Kangi", "David Masui"])

            # Check if the user has entered data and submitted the form
            if st.button("Submit"):
                date_str = date.strftime("%Y-%m-%d")

                # Create a new row of data to add to the Google Sheets spreadsheet
                new_data = [date_str, intermediary, persons, outstanding, collected, actions, review]

                # Append the new row of data to the worksheet
                worksheet.append_row(new_data)     

        elif view == "Records":
            # Show the saved DataFrame here
            data = worksheet.get_all_values()
            headers = data[0]
            data = data[1:]
            df = pd.DataFrame(data, columns=headers)  # Convert data to a DataFrame
            st.subheader("RECORDS")

            # Get the unique reviewer names from the DataFrame
            unique_reviewers = df['Reviewed by'].unique()

            # Create a dropdown to select a reviewer with "All" option
            selected_reviewer = st.selectbox("Filter by Reviewer:", ["All"] + list(unique_reviewers))

            if selected_reviewer != "All":
                # Filter the DataFrame based on the selected reviewer
                filtered_df = df[df['Reviewed by'] == selected_reviewer]
            else:
                # If "All" is selected, show the entire DataFrame
                filtered_df = df

            edited_df = st.data_editor(filtered_df)

            # Add a button to update Google Sheets with the changes
            if st.button("Update Google Sheets"):
                worksheet.clear()  # Clear the existing data in the worksheet
                worksheet.update([edited_df.columns.tolist()] + edited_df.values.tolist())

            # Add a button to download the filtered data as a CSV
            if st.button("Download CSV"):
                csv_data = edited_df.to_csv(index=False, encoding='utf-8')
                b64 = base64.b64encode(csv_data.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="collection_report.csv">Download CSV</a>'
                st.markdown(href, unsafe_allow_html=True)              

    if __name__ == "__main__":
        main()

