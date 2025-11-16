# streamlit_app.py

import streamlit as st
import pandas as pd
from analysis import get_dummy_prop_data, analyze_slip_risk, get_trend_indicator
import time

# --- 0. Configuration and State Management ---

st.set_page_config(layout="wide", page_title="Peezy AI Prop Builder")

# Use st.session_state for global state (like ZUSTAND in React Native)
if 'slip' not in st.session_state:
    st.session_state.slip = []

# --- 1. Helper Functions for Slip Management ---

def add_to_slip(prop_data, selection):
    if len(st.session_state.slip) >= 6:
        st.warning("Maximum of 6 picks allowed in the slip.")
        return

    prop_id = prop_data['id']
    if any(item['id'] == prop_id for item in st.session_state.slip):
        st.warning("This prop is already in your slip.")
        return

    st.session_state.slip.append({
        'id': prop_id,
        'playerName': prop_data['name'],
        'propMarket': prop_data['market'],
        'line': prop_data['line'],
        'selection': selection,
        'trend_score': prop_data['trend_score'],
        'game_id': prop_data['game_id'],
    })

def remove_from_slip(prop_id):
    st.session_state.slip = [
        item for item in st.session_state.slip if item['id'] != prop_id
    ]

# --- 2. Player Prop Display Component ---

def display_player_prop(prop):
    """Displays a single player prop card with L/F analysis."""
    trend, color = get_trend_indicator(prop['trend_score'])

    col1, col2 = st.columns([0.7, 0.3])
    
    with col1:
        st.markdown(f"**{prop['playerName']}** ({prop['market']})")
        st.markdown(f"Line: **{prop['line']}**")
        
    with col2:
        st.markdown(f'<div style="background-color: {color}; color: white; padding: 5px; border-radius: 5px; text-align: center;">{trend}</div>', unsafe_allow_html=True)
        # Placeholder for odds data (Requirement 4)
        # st.caption(f"Odds: O -110 / U +100") 

    # Selection buttons
    c_over, c_under, c_empty = st.columns(3)
    with c_over:
        st.button(f"OVER {prop['line']}", key=f"O_{prop['id']}", 
                  on_click=add_to_slip, args=(prop, 'OVER'), 
                  use_container_width=True)
    with c_under:
        st.button(f"UNDER {prop['line']}", key=f"U_{prop['id']}", 
                  on_click=add_to_slip, args=(prop, 'UNDER'), 
                  use_container_width=True)
    st.divider()

# --- 3. Main App Layout ---

st.title("🏀 Peezy AI Prop Builder")

# Use Streamlit's sidebar for navigation (tabs)
page = st.sidebar.radio("Navigation", ["Players (Search)", "Build Slip (Analyzer)", "Profile (Login)"])

# --- PLAYERS SCREEN ---
if page == "Players (Search)":
    st.header("Search & Select Player Props")
    
    # Filtering and Search (Requirement 3)
    c1, c2 = st.columns([0.7, 0.3])
    search_term = c1.text_input("Search Player", key="search")
    sport_filter = c2.selectbox("Sport", ["NBA", "NFL", "MLB"], key="sport")
    
    # Simulate API Fetch (Requirement 4)
    with st.spinner(f"Fetching live lines for {sport_filter}..."):
        time.sleep(1) # Simulate network delay
        all_props = get_dummy_prop_data()
    
    # Apply search filter
    filtered_props = [
        p for p in all_props if search_term.lower() in p['name'].lower()
    ]

    if filtered_props:
        for prop in filtered_props:
            display_player_prop(prop)
    else:
        st.info("No available props found or filtered.")

# --- BUILD SLIP SCREEN ---
elif page == "Build Slip (Analyzer)":
    st.header("Pick-6 Slip Analyzer")

    if not st.session_state.slip:
        st.info("Your Pick-6 slip is empty. Go to the Players tab to add picks.")
    else:
        # --- Display Current Slip ---
        st.subheader(f"Current Picks ({len(st.session_state.slip)}/6)")
        for i, pick in enumerate(st.session_state.slip):
            c_p1, c_p2, c_p3 = st.columns([0.1, 0.7, 0.2])
            c_p1.markdown(f"**{i+1}.**")
            c_p2.markdown(f"**{pick['playerName']}** | {pick['propMarket']} **{pick['selection']}** {pick['line']}")
            c_p3.button("Remove", key=f"R_{pick['id']}", on_click=remove_from_slip, args=(pick['id'],), use_container_width=True)
        
        st.divider()

        # --- Analysis Section (Requirement 1) ---
        st.subheader("Slip Risk Analysis")
        risk_score, warning, trend_strength = analyze_slip_risk(st.session_state.slip)
        
        # Risk Score Indicator
        st.metric(
            label="Overall Risk Score (Lower is better)",
            value=f"{risk_score:.1f} / 10",
            delta=f"Avg Trend: {trend_strength:.1f}"
        )

        # Correlation Warning (Most important output)
        if warning:
            st.error(f"Correlation Warning: {warning}")
        else:
            st.success("No major correlation warnings detected.")

        st.info("This analysis does not guarantee results. Use for informational purposes only.")

# --- PROFILE SCREEN (Placeholder) ---
elif page == "Profile (Login)":
    st.header("User Profile & Settings")
    
    # Placeholder for Firebase Auth (Requirement 5)
    st.success("Logged in as: User@peezyai.com") 
    st.write("This section will manage your Watchlist and user settings.")
    st.button("Log Out")
    
    # Placeholder for Watchlist (Requirement 2)
    st.subheader("Watchlist & Alerts")
    st.info("No alerts or saved props currently in your watchlist.")

# --- Footer Pick-6 Card (Simulated) ---
st.sidebar.markdown("---")
st.sidebar.markdown(f"**🔥 Current Slip:** **{len(st.session_state.slip)}/6 Picks**")