import streamlit as st
import numpy as np
import pandas as pd

#dataframe = pd.DataFrame(
#    np.random.randn(10, 20),
#    columns=('col %d' % i for i in range(20)))

#st.dataframe(dataframe.style.highlight_max(axis=0))

#------ Widgets

x = st.slider('x')  # 👈 this is a widget
st.write(x, 'squared is', x * x)

#------ Gráfico
chart_data = pd.DataFrame(
     np.random.randn(x, 3),
     columns=['a', 'b', 'c'])

st.line_chart(chart_data)


#------ Mapa

map_data = pd.DataFrame(
    np.random.randn(x*x, 2) / [50, 50] + [37.76, -122.4],
    columns=['lat', 'lon'])

st.map(map_data)

import streamlit as st
st.text_input("Your name", key="name")

# You can access the value at any point with:
st.session_state.name
