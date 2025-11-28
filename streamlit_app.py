import streamlit as st
import pandas as pd

st.write("Aqui está - our first attempt at using data to create a table:")
st.table(pd.DataFrame({
    'first column': [5, 1, 2, 3, 4],
    'second column': [0, 10, 20, 30, 40]
}))