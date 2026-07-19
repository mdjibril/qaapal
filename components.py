import streamlit as st

@st.fragment
def render_nos_selection(nos_data, prefix, persistent_set_key, result_list_key, select_key_prefix):
    """
    Consolidated standard criteria selection fragment.
    Enables checkbox filtering per-unit in a tab-like selectbox experience,
    avoiding thread-blocking component count overhead.
    """
    if persistent_set_key not in st.session_state:
        st.session_state[persistent_set_key] = set()

    def pc_callback(pc_val):
        # Toggle PC state in the persistent set
        if st.session_state[f"{prefix}chk_{pc_val}"]:
            st.session_state[persistent_set_key].add(pc_val)
        else:
            st.session_state[persistent_set_key].discard(pc_val)

    def sync_unit_pcs(u_key, u_data, unit_code):
        master_val = st.session_state[f"{prefix}unit_all_{u_key}"]
        for lo_key, pcs in u_data.items():
            lo_id = lo_key.split(':')[0].replace("LO", "").strip()
            for pc in pcs:
                pc_val = f"{unit_code} - {lo_id} - {pc}"
                st.session_state[f"{prefix}chk_{pc_val}"] = master_val
                if master_val:
                    st.session_state[persistent_set_key].add(pc_val)
                else:
                    st.session_state[persistent_set_key].discard(pc_val)

    def clear_all_pcs_callback():
        st.session_state[persistent_set_key].clear()
        # Reset all checkbox states dynamically
        for key in st.session_state.keys():
            if key.startswith(f"{prefix}chk_") or key.startswith(f"{prefix}unit_all_"):
                st.session_state[key] = False

    unit_titles = list(nos_data.keys())
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_unit_key = st.selectbox(
            "Select a Unit to view criteria", 
            unit_titles, 
            key=f"{select_key_prefix}_unit_selectbox"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button(
            "🗑️ Clear All Selections", 
            on_click=clear_all_pcs_callback, 
            key=f"{select_key_prefix}_clear_pcs_btn"
        )

    if selected_unit_key:
        unit_code = selected_unit_key.split(':')[0]
        
        st.checkbox(
            f"✅ Select All Performance Criteria for {unit_code}", 
            key=f"{prefix}unit_all_{selected_unit_key}",
            on_change=sync_unit_pcs,
            args=(selected_unit_key, nos_data[selected_unit_key], unit_code)
        )
        
        for lo_key, pcs in nos_data[selected_unit_key].items():
            lo_id = lo_key.split(':')[0].replace("LO", "").strip()
            with st.expander(lo_key, expanded=True):
                for pc in pcs:
                    pc_val = f"{unit_code} - {lo_id} - {pc}"
                    chk_key = f"{prefix}chk_{pc_val}"
                    if chk_key not in st.session_state:
                        st.session_state[chk_key] = pc_val in st.session_state[persistent_set_key]
                        
                    st.checkbox(
                        pc, 
                        key=chk_key,
                        on_change=pc_callback,
                        args=(pc_val,)
                    )
    
    st.session_state[result_list_key] = list(st.session_state[persistent_set_key])
