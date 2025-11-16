import streamlit as st
import pandas as pd
import time
# Firebase and Firestore Imports
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials, firestore, auth
from analysis import get_dummy_prop_data, analyze_slip_risk, get_trend_indicator

# --- 0. Configuration and Initialization ---

st.set_page_config(layout="wide", page_title="Peezy AI Prop Builder")

# Function to initialize the Firebase Admin SDK (Auth & Firestore)
@st.cache_resource
def initialize_firebase():
    try:
        if not firebase_admin._apps:
            # Initialize with the private key file for Admin SDK
            cred = credentials.Certificate("firebase-key.json")
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        return db
    except Exception as e:
        # NOTE: This error means 'firebase-key.json' is missing or invalid.
        st.error(f"Firebase Initialization Error. Check firebase-key.json: {e}")
        return None

db = initialize_firebase()

# Global state for user status and data
if 'user' not in st.session_state:
    st.session_state.user = None
if 'slip' not in st.session_state:
    st.session_state.slip = []
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

# --- 1. Watchlist and Slip Functions ---

def load_watchlist(user_id):
    """Fetches the user's watchlist from Firestore."""
    if not db or not user_id: return []
    try:
        doc_ref = db.collection("watchlists").document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("props", [])
        return []
    except Exception as e:
        st.warning(f"Error loading watchlist: {e}")
        return []

def save_watchlist(user_id, props):
    """Saves the updated watchlist back to Firestore."""
    if not db or not user_id: return
    try:
        doc_ref = db.collection("watchlists").document(user_id)
        doc_ref.set({"props": props})
    except Exception as e:
        st.error(f"Error saving watchlist: {e}")

def toggle_watchlist(prop_data):
    """Adds or removes a prop from the watchlist."""
    if not st.session_state.user:
        st.warning("Please log in to manage your watchlist.")
        return
        
    prop_id = prop_data['id']
    if prop_id in [p['id'] for p in st.session_state.watchlist]:
        st.session_state.watchlist = [p for p in st.session_state.watchlist if p['id'] != prop_id]
        st.sidebar.success(f"Removed {prop_data['playerName']} from Watchlist!")
    else:
        st.session_state.watchlist.append({
            'id': prop_data['id'],
            'playerName': prop_data['name'], # Use 'name' from prop_data here
            'market': prop_data['market'],
            'line': prop_data['line'],
        })
        st.sidebar.success(f"Added {prop_data['playerName']} to Watchlist!")
    
    # Save change back to Firebase
    save_watchlist(st.session_state.user['uid'], st.session_state.watchlist)
    time.sleep(0.1) # small delay for UI update

def add_to_slip(prop_data, selection):
    if len(st.session_state.slip) >= 6:
        st.warning("Maximum of 6 picks allowed in the slip.")
        return
    if not st.session_state.user:
        st.warning("Please log in to create a slip.")
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

# --- 2. Authentication Functions ---

def handle_login(email, password):
    """Attempts to sign in a user (simplified for Admin SDK environment)."""
    if not db: return st.error("Database connection failed.")
    try:
        user = auth.get_user_by_email(email)
        # NOTE: Admin SDK cannot verify password. We assume success if user exists.
        st.session_state.user = {'email': user.email, 'uid': user.uid}
        st.session_state.watchlist = load_watchlist(user.uid)
        st.success(f"Welcome back, {user.email}!")
        time.sleep(1)
        st.experimental_rerun()
        
    except firebase_admin.exceptions.FirebaseError as e:
        st.error(f"Login Failed. Check email/password. (Admin API Error: {e})")

def handle_signup(email, password):
    """Attempts to create a new user."""
    if not db: return st.error("Database connection failed.")
    if len(password) < 6: return st.error("Password must be at least 6 characters.")
        
    try:
        user = auth.create_user(email=email, password=password)
        st.session_state.user = {'email': user.email, 'uid': user.uid}
        st.session_state.watchlist = [] # New user starts with empty watchlist
        st.success(f"Account created for {user.email}! Logging you in...")
        time.sleep(1)
        st.experimental_rerun()
    except firebase_admin.exceptions.FirebaseError as e:
        st.error(f"Signup Failed: {e}")

def handle_logout():
    st.session_state.user = None
    st.session_state.watchlist = []
    st.session_state.slip = []
    st.success("Logged out successfully.")
    time.sleep(1)
    st.experimental_rerun()

# --- 3. Player Prop Display Component ---

def display_player_prop(prop):
    """Displays a single player prop card with L/F analysis and Watchlist button."""
    trend, color = get_trend_indicator(prop['trend_score'])
    
    is_watched = False
    if st.session_state.user:
        is_watched = prop['id'] in [p['id'] for p in st.session_state.watchlist]
        
    watch_icon = "⭐ Watching" if is_watched else "☆ Watch"

    col1, col2, col3 = st.columns([0.5, 0.2, 0.3])
    
    with col1:
        st.markdown(f"**{prop['name']}** ({prop['market']})")
        st.markdown(f"Line: **{prop['line']}**")
        
    with col2:
        st.markdown(f'<div style="background-color: {color}; color: white; padding: 5px; border-radius: 5px; text-align: center;">{trend}</div>', unsafe_allow_html=True)
        
    with col3:
        # Note: toggle_watchlist uses the full prop dict.
        st.button(watch_icon, key=f"W_{prop['id']}", 
                  on_click=toggle_watchlist, args=(prop,), 
                  use_container_width=True, help="Add or remove from your watchlist")

    # Selection buttons
    c_over, c_under = st.columns(2)
    with c_over:
        st.button(f"OVER {prop['line']}", key=f"O_{prop['id']}", 
                  on_click=add_to_slip, args=(prop, 'OVER'), 
                  use_container_width=True)
    with c_under:
        st.button(f"UNDER {prop['line']}", key=f"U_{prop['id']}", 
                  on_click=add_to_slip, args=(prop, 'UNDER'), 
                  use_container_width=True)
    st.divider()

# --- 4. Main App Layout ---

st.title("🏀 Peezy AI Prop Builder")

page = st.sidebar.radio("Navigation", ["Players (Search)", "Build Slip (Analyzer)", "Profile (Login)"])

# --- PLAYERS SCREEN ---
if page == "Players (Search)":
    st.header("Search & Select Player Props")
    
    c1, c2 = st.columns([0.7, 0.3])
    search_term = c1.text_input("Search Player", key="search")
    sport_filter = c2.selectbox("Sport", ["NBA", "NFL", "MLB"], key="sport")
    
    # Simulate API Fetch (Requirement 4)
    with st.spinner(f"Fetching live lines for {sport_filter}..."):
        time.sleep(1) # Simulate network delay
        all_props = get_dummy_prop_data()
    
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

    if not st.session_state.user:
         st.warning("Please log in to view and analyze your slip.")
    elif not st.session_state.slip:
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
        
        st.metric(
            label="Overall Risk Score (Lower is better)",
            value=f"{risk_score:.1f} / 10",
            delta=f"Avg Trend: {trend_strength:.1f}"
        )

        if warning:
            st.error(f"Correlation Warning: {warning}")
        else:
            st.success("No major correlation warnings detected.")

# --- PROFILE / LOGIN SCREEN ---
elif page == "Profile (Login)":
    st.header("User Profile & Watchlist")
    
    if not db:
        st.error("Firebase is not connected. Please check 'firebase-key.json'.")
    
    if st