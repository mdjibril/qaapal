from copy import deepcopy

import streamlit as st


def ensure_session_defaults(defaults):
    """Populate missing Streamlit session keys without overwriting existing state."""
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default() if callable(default) else deepcopy(default)

