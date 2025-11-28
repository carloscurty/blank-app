import streamlit as st

st.title("🎈 My new app")
st.write(
    "🎈 My new Streamlit app"
)

import pandas as pd
df = pd.DataFrame({
  'first column': [1, 2, 3, 4],
  'second column': [10, 20, 30, 40]
})

df