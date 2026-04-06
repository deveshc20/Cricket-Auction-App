import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid

# Set the title and subtitle
st.title('Cricket Auction App V2')
st.subheader('Enhanced UI/UX with Streamlit and Plotly')

# Navigation Menu
menu = st.sidebar.radio('Navigation', ['Home', 'Visualizations', 'Metrics'])

# Loading State
with st.spinner('Loading...'):
    # Simulate data loading
    auction_data = pd.read_csv('auction_data.csv') # Placeholder for actual data

# Home Section
if menu == 'Home':
    st.write('Welcome to the enhanced Cricket Auction App!')

# Visualizations Section
elif menu == 'Visualizations':
    # Create a plotly chart
    fig = px.bar(auction_data, x='Player', y='BidAmount', title='Player Bids Overview')
    st.plotly_chart(fig)

# Metrics Section
elif menu == 'Metrics':
    total_bids = auction_data['BidAmount'].sum()
    st.metric(label='Total Bids Amount', value=f'${total_bids}')

# Interactive Table using AgGrid
st.subheader('Auction Details')
AgGrid(auction_data)