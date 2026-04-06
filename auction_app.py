import streamlit as st
from st_aggrid import AgGrid
import plotly.express as px
import pandas as pd

# Sample data for demonstration
data = {'Player': ['Player 1', 'Player 2', 'Player 3'], 'Budget': [100, 200, 150]}
df = pd.DataFrame(data)

# Streamlit option menu for navigation
selected_option = st.sidebar.selectbox('Select an option', ['Home', 'Auction', 'Statistics'])

if selected_option == 'Home':
    st.title('Welcome to Cricket Auction App')
    st.write('An enhanced auction experience with improved UI/UX!')

elif selected_option == 'Auction':
    st.title('Auction Room')
    st.write('Place your bids below:')
    st.button('Bid')

elif selected_option == 'Statistics':
    st.title('Budget Visualization')
    # Plotly chart for budget visualization
    fig = px.bar(df, x='Player', y='Budget', title='Budget Visualization')
    st.plotly_chart(fig)

# Interactive tables using streamlit-aggrid
st.subheader('Player Data')
AgGrid(df)

# Improved layouts
st.sidebar.header('User Options')
col1, col2 = st.columns(2)
with col1:
    st.metric(label='Total Budget', value='450')
with col2:
    st.metric(label='Bids Made', value='10')

# Loading state example
if st.button('Load Data'):
    with st.spinner('Loading data...'):
        # Simulating data load
        import time
        time.sleep(2)
        st.success('Data loaded successfully!')

# Modal-like dialogs for confirmations
if st.button('Confirm Bid'):
    st.warning('Are you sure you want to confirm your bid?')

# End of enhanced auction app
