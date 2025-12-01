import streamlit as st
import numpy as np
import pandas as pd
import time

#dataframe = pd.DataFrame(
#    np.random.randn(10, 20),
#    columns=('col %d' % i for i in range(20)))

#st.dataframe(dataframe.style.highlight_max(axis=0))

#------ Widgets
#x = st.slider('x')  # 👈 this is a widget
#st.write(x, 'squared is', x * x)

#------ Gráfico
#chart_data = pd.DataFrame(
#     np.random.randn(x, 3),
#     columns=['a', 'b', 'c'])

#st.line_chart(chart_data)


#------ Mapa
#------ Checkbox
#if st.checkbox('Exibir o mapa'):
#    map_data = pd.DataFrame(
#        np.random.randn(x*x, 2) / [50, 50] + [37.76, -122.4],
#        columns=['lat', 'lon'])

#    st.map(map_data)

#import streamlit as st
#st.text_input("Your name", key="name")

# You can access the value at any point with:
#st.session_state.name

#------ Caixa de seleção para as opções
#df = pd.DataFrame({
#    'first column': [1, 2, 30, 4],
#    'second column': [10, 20, 30, 40]
#    })

#option = st.selectbox(
#    'Which number do you like best?',
#     df['first column'])

#'You selected: ', option

#------LAYOUT
#
#
#
#
# 
#------

#------ Sidebar
st.sidebar.title("MENU")

import streamlit as st

# Define the pages
main_page = st.Page("main_page.py", title="Main Page", icon="🎈")
page_2 = st.Page("page_2.py", title="Page 2", icon="❄️")
page_3 = st.Page("page_3.py", title="Page 3", icon="🎉")

# Set up navigation
pg = st.navigation([main_page, page_2, page_3])

# Run the selected page
pg.run()