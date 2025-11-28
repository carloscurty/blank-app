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
    np.random.randn(1000, 2) / [x, 50] + [37.76, -122.4],
    columns=['lat', 'lon'])

st.map(map_data)

