import streamlit as st

if "audio_key" not in st.session_state:
    st.session_state.audio_key = 0

st.write("key is", st.session_state.audio_key)

audio = st.audio_input("Record", key=f"audio_{st.session_state.audio_key}")

if audio:
    if st.button("Process"):
        st.write("Processing audio size", len(audio.read()))
        # DO NOT increment key here yet to test
        st.session_state.audio_key += 1
        st.rerun()
