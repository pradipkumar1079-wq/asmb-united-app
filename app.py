import streamlit as st
import datetime
import math
import re
import random
import pandas as pd
from PIL import Image
import io
import json
import os
import base64

# ==========================================
# PERMANENT MEMORY FILE ENGINE (JSON STORAGE)
# ==========================================
DB_FILE = "asmb_football_club_data.json"

def load_data_from_file():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def save_data_to_file():
    data_to_save = {
        "app_settings": st.session_state.app_settings,
        "users": st.session_state.users,
        "ratings_db": {f"{k[0]}|||{k[1]}": v for k, v in st.session_state.ratings_db.items()},
        "player_stats": st.session_state.player_stats,
        "group_chat": st.session_state.group_chat,
        "football_ai_chats": st.session_state.football_ai_chats,
        "personal_ai_chats": st.session_state.personal_ai_chats,
        "notice_board": st.session_state.notice_board,
        "motm_votes": st.session_state.motm_votes,
        "injured_players": list(st.session_state.injured_players),
        "match_settings": st.session_state.match_settings,
        "block_appeals": st.session_state.block_appeals,
        "match_availability_poll": st.session_state.get("match_availability_poll", {})
    }
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, indent=4, ensure_ascii=False)

# ==========================================
# 0. INITIALIZE SESSION & DATABASE
# ==========================================
st.set_page_config(
    page_title="ASMB United Football Club",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_db():
    if "db_initialized" not in st.session_state:
        saved_data = load_data_from_file()
        
        if saved_data:
            st.session_state.app_settings = saved_data.get("app_settings", {
                "app_name": "ASMB United Football Club",
                "bg_color": "#00D2FF",
                "max_register_limit": 50,
                "club_photo_b64": None
            })
            st.session_state.users = saved_data.get("users", {})
            
            raw_ratings = saved_data.get("ratings_db", {})
            st.session_state.ratings_db = {}
            for key_str, val in raw_ratings.items():
                parts = key_str.split("|||")
                if len(parts) == 2:
                    st.session_state.ratings_db[(parts[0], parts[1])] = val

            st.session_state.player_stats = saved_data.get("player_stats", {})
            st.session_state.group_chat = saved_data.get("group_chat", [])
            st.session_state.football_ai_chats = saved_data.get("football_ai_chats", [])
            st.session_state.personal_ai_chats = saved_data.get("personal_ai_chats", {})
            st.session_state.notice_board = saved_data.get("notice_board", [])
            st.session_state.motm_votes = saved_data.get("motm_votes", {})
            st.session_state.injured_players = set(saved_data.get("injured_players", []))
            st.session_state.match_settings = saved_data.get("match_settings", {
                "asmb_player_count": 11,
                "opponent_player_count": 11,
                "opponent_formation": "4-4-2",
                "goals_conceded": 0
            })
            st.session_state.block_appeals = saved_data.get("block_appeals", {})
            st.session_state.match_availability_poll = saved_data.get("match_availability_poll", {})
        else:
            st.session_state.app_settings = {
                "app_name": "ASMB United Football Club",
                "bg_color": "#00D2FF",
                "max_register_limit": 50,
                "club_photo_b64": None
            }
            st.session_state.users = {}
            st.session_state.ratings_db = {}
            st.session_state.player_stats = {}
            st.session_state.group_chat = []
            st.session_state.football_ai_chats = []
            st.session_state.personal_ai_chats = {}
            st.session_state.notice_board = []
            st.session_state.motm_votes = {}
            st.session_state.injured_players = set()
            st.session_state.match_settings = {
                "asmb_player_count": 11,
                "opponent_player_count": 11,
                "opponent_formation": "4-4-2",
                "goals_conceded": 0
            }
            st.session_state.block_appeals = {}
            st.session_state.match_availability_poll = {}
            save_data_to_file()
            
        st.session_state.db_initialized = True

init_db()

# ==========================================
# 1. DYNAMIC COLOR ENGINE & CSS INJECTION
# ==========================================
def get_daily_theme_colors():
    bright_bg_colors = ["#FFD166", "#06D6A0", "#118AB2", "#FF70A6", "#FF9F1C", "#70D6FF", "#E76F51"]
    day_idx = datetime.datetime.now().day % len(bright_bg_colors)
    bg = bright_bg_colors[day_idx]
    
    text_colors = ["#000000", "#1A0033", "#002966", "#4A001F", "#330000", "#001A33", "#220000"]
    txt = text_colors[day_idx]
    
    return bg, txt

bg_color, title_text_color = get_daily_theme_colors()
st.session_state.app_settings["bg_color"] = bg_color

st.markdown(f"""
    <style>
    .stApp {{
        background-color: {bg_color} !important;
    }}
    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp span, .stApp label {{
        color: #000000 !important;
        font-weight: 600;
    }}
    .daily-club-title {{
        color: {title_text_color} !important;
        font-size: 2.3rem !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 5px rgba(255,255,255,0.6);
    }}
    /* ⚪ বাটনের ব্যাকগ্রাউন্ড সাদা এবং টেক্সট কালো করার আপডেট */
    div.stButton > button {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #000000 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: all 0.2s ease !important;
    }}
    div.stButton > button:hover {{
        background-color: #F0F2F6 !important;
        color: #000000 !important;
        border-color: #000000 !important;
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. HELPER CALCULATORS & BUSINESS LOGIC
# ==========================================
def get_active_unblocked_users():
    return {u: data for u, data in st.session_state.users.items() if data.get("status") == "Active"}

def compute_player_rating(username):
    user_ratings = [data["rating"] for (rater, target), data in st.session_state.ratings_db.items() if target == username]
    user_fouls = [data["fouls"] for (rater, target), data in st.session_state.ratings_db.items() if target == username]
    
    base_rating = (sum(user_ratings) / len(user_ratings)) if user_ratings else 6.0
    avg_fouls = (sum(user_fouls) / len(user_fouls)) if user_fouls else 0.0
    
    stats = st.session_state.player_stats.get(username, {
        "goals": 0, "assists": 0, "conceded_penalty": 0.0, "attendance": "Present", "rating_penalty": 0.0, "gk_saves": 0
    })
    
    goals_bonus = stats.get("goals", 0) * 0.5
    assists_bonus = stats.get("assists", 0) * 0.3
    gk_saves_bonus = stats.get("gk_saves", 0) * 0.2
    foul_penalty = avg_fouls * 0.2
    
    pos = st.session_state.users.get(username, {}).get("position", "")
    conceded = st.session_state.match_settings.get("goals_conceded", 0)
    
    conceded_penalty = 0.0
    if conceded > 0:
        if pos == "GK":
            conceded_penalty = conceded * 1.0
        elif pos in ["CB", "LB", "RB", "DF"]:
            conceded_penalty = conceded * 0.75
        else:
            conceded_penalty = conceded * 0.5
            
    net_rating = base_rating + goals_bonus + assists_bonus + gk_saves_bonus - foul_penalty - conceded_penalty - stats.get("rating_penalty", 0.0)
    
    if stats.get("attendance") == "Absent":
        net_rating -= 1.0
        
    return max(0.0, min(10.0, round(net_rating, 2)))

def get_highest_motm_player():
    if not st.session_state.motm_votes:
        return None
    votes_list = list(st.session_state.motm_votes.values())
    if not votes_list:
        return None
    return max(set(votes_list), key=votes_list.count)

def update_star_players():
    top_motm_player = get_highest_motm_player()
    for uname, udata in st.session_state.users.items():
        if udata["status"] == "Blocked":
            udata["is_star"] = False
            continue
            
        rating = compute_player_rating(uname)
        if rating >= 8.5 or (top_motm_player and uname == top_motm_player):
            udata["is_star"] = True
        else:
            udata["is_star"] = False

def check_and_publish_attendance_notice():
    active_users = get_active_unblocked_users()
    poll_data = st.session_state.get("match_availability_poll", {})
    
    all_answered = all(u in poll_data for u in active_users.keys())
    if all_answered and len(active_users) > 0:
        if not st.session_state.get("attendance_published_today", False):
            present_list = [f"• {active_users[u]['full_name']} (@{u})" for u, ans in poll_data.items() if ans == "Yes"]
            absent_list = [f"• {active_users[u]['full_name']} (@{u})" for u, ans in poll_data.items() if ans == "No"]
            
            notice_text = f"### 📋 Matchday Attendance Summary ({datetime.date.today()})\n\n"
            notice_text += f"**✅ Present ({len(present_list)}):**\n" + ("\n".join(present_list) if present_list else "None") + "\n\n"
            notice_text += f"**❌ Absent ({len(absent_list)}):**\n" + ("\n".join(absent_list) if absent_list else "None")
            
            st.session_state.notice_board.append({
                "id": len(st.session_state.notice_board) + 1,
                "author": "System Admin",
                "title": f"Official Attendance Summary - {datetime.date.today()}",
                "content": notice_text,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "comments": []
            })
            st.session_state.attendance_published_today = True
            save_data_to_file()

# ==========================================
# 3. AUTHENTICATION & FORGET PASSWORD SYSTEM
# ==========================================
if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

def login_register_surface():
    st.markdown(f'<h1 class="daily-club-title">⚽ {st.session_state.app_settings["app_name"]}</h1>', unsafe_allow_html=True)
    
    if st.session_state.app_settings.get("club_photo_b64"):
        try:
            img_bytes = base64.b64decode(st.session_state.app_settings["club_photo_b64"])
            st.image(Image.open(io.BytesIO(img_bytes)), use_container_width=True)
        except Exception:
            pass

    tab1, tab2, tab3 = st.tabs(["🔒 Login", "📝 Register", "🔑 Forget Password"])
    
    with tab1:
        st.subheader("Login to Dashboard")
        login_username = st.text_input("Username", key="login_uname").strip()
        login_password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login", key="btn_login"):
            if login_username in st.session_state.users:
                user = st.session_state.users[login_username]
                if user["password"] == login_password:
                    st.session_state.authenticated_user = login_username
                    st.success(f"Welcome back, {user['full_name']}!")
                    st.rerun()
                else:
                    st.error("Invalid password. Please try again.")
            else:
                st.error("Username does not exist. Please register first.")

    with tab2:
        st.subheader("Club Registration Form")
        active_count = len(get_active_unblocked_users())
        max_limit = st.session_state.app_settings.get("max_register_limit", 50)
        
        st.info(f"👥 **Registered Active Members:** {active_count} / {max_limit}")
        
        if active_count >= max_limit:
            st.error("⛔ Registration limit reached! Controlled by Admin.")
            return

        reg_username = st.text_input("Username (Unique ID)*", key="reg_uname").strip()
        reg_password = st.text_input("Password*", type="password", key="reg_pass")
        reg_sec_key = st.text_input("Security Key (Required for Reset Password)*", key="reg_sec_key", type="password")
        reg_full_name = st.text_input("Full Name*", key="reg_fullname")
        reg_jersey_num = st.number_input("Jersey Number*", min_value=1, max_value=99, step=1)
        reg_jersey_name = st.text_input("Jersey Player Name*", key="reg_jname")
        
        reg_photo_file = st.file_uploader("Upload Photo (Optional)", type=["jpg", "png", "jpeg"])
        reg_photo_b64 = None
        if reg_photo_file:
            reg_photo_b64 = base64.b64encode(reg_photo_file.read()).decode('utf-8')

        reg_personal_ai = st.text_input("Personal AI Custom Name*", value="Jarvis", key="reg_pai")
        
        is_first_user = len(st.session_state.users) == 0
        if is_first_user:
            st.info("ℹ️ First user automatically granted Superadmin (S.A) role.")
            reg_position = st.selectbox("Assign Initial Position (Superadmin Exclusive)", ["GK","CB", "LB", "RB", "CM", "CAM", "RW", "LW", "ST"])
        else:
            st.warning("🔒 Position assignment is strictly disabled during registration. S.A/Admin will set your position later.")
            reg_position = "Unassigned"

        if st.button("Register Account", key="btn_reg"):
            if not reg_username or not reg_password or not reg_full_name or not reg_jersey_name or not reg_personal_ai or not reg_sec_key:
                st.error("Please fill in all required fields!")
                return
            
            if reg_username in st.session_state.users:
                st.error("⚠️ Username already exists! Redirecting to login...")
                return
            
            role = "Superadmin" if is_first_user else "Player"
            
            st.session_state.users[reg_username] = {
                "password": reg_password,
                "sec_key": reg_sec_key,
                "full_name": reg_full_name,
                "jersey_num": reg_jersey_num,
                "jersey_name": reg_jersey_name,
                "photo_b64": reg_photo_b64,
                "personal_ai_name": reg_personal_ai,
                "role": role,
                "position": reg_position,
                "status": "Active",
                "block_reason": "",
                "is_star": False
            }
            
            st.session_state.player_stats[reg_username] = {
                "goals": 0, "assists": 0, "conceded_penalty": 0.0, "attendance": "Present", "rating_penalty": 0.0, "gk_saves": 0
            }
            
            save_data_to_file()
            st.success("Registration successful! You can now login.")

    with tab3:
        st.subheader("🔑 Forget Password Reset")
        fp_uname = st.text_input("Enter Username:", key="fp_uname").strip()
        fp_sec_key = st.text_input("Enter Security Key:", key="fp_sec_key", type="password")
        fp_new_pass = st.text_input("Enter New Password:", key="fp_new_pass", type="password")
        
        if st.button("Reset Password", key="btn_fp_reset"):
            if fp_uname in st.session_state.users:
                u = st.session_state.users[fp_uname]
                if u.get("sec_key") == fp_sec_key and fp_sec_key.strip():
                    u["password"] = fp_new_pass
                    save_data_to_file()
                    st.success("Password successfully updated! Please login with your new password.")
                else:
                    st.error("Incorrect Security Key or not set!")
            else:
                st.error("Username not found!")

if not st.session_state.authenticated_user:
    login_register_surface()
    st.stop()

# ==========================================
# MANDATORY SECURITY KEY POP-UP FOR EXISTING USERS
# ==========================================
curr_username = st.session_state.authenticated_user
curr_user = st.session_state.users[curr_username]

if "sec_key" not in curr_user or not curr_user["sec_key"]:
    st.warning("🔑 **Security Key Mandatory Update:** আপনার অ্যাকাউন্টে কোনো Security Key সেট করা নেই। পাসওয়ার্ড রিসেট করার নিরাপত্তার জন্য একটি গোপন সিকিউরিটি কী দিন।")
    legacy_key = st.text_input("Set Security Key:", type="password", key="pop_sec_key")
    if st.button("Save & Proceed to App", key="btn_save_pop_key"):
        if legacy_key.strip():
            curr_user["sec_key"] = legacy_key.strip()
            save_data_to_file()
            st.success("Security Key Saved!")
            st.rerun()
        else:
            st.error("Cannot leave Security Key empty.")
    st.stop()

# ==========================================
# SATURDAY-ONLY MATCHDAY PRE-POLL DIALOG
# ==========================================
is_saturday = datetime.datetime.now().weekday() == 5  # Monday=0 ... Saturday=5, Sunday=6

if is_saturday and curr_user["status"] == "Active" and curr_username not in st.session_state.match_availability_poll:
    st.info("📅 **Saturday Pre-Match Poll:** আগামীকাল রবিবারের (Sunday Matchday) ম্যাচে কি আপনি খেলবেন?")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("✅ Yes, I will attend", key="poll_yes"):
            st.session_state.match_availability_poll[curr_username] = "Yes"
            st.session_state.player_stats[curr_username]["attendance"] = "Present"
            save_data_to_file()
            check_and_publish_attendance_notice()
            st.rerun()
    with col_p2:
        if st.button("❌ No, I cannot attend", key="poll_no"):
            st.session_state.match_availability_poll[curr_username] = "No"
            st.session_state.player_stats[curr_username]["attendance"] = "Absent"
            save_data_to_file()
            check_and_publish_attendance_notice()
            st.rerun()

# ==========================================
# 4. SIDEBAR & NAVIGATION
# ==========================================
update_star_players()

st.sidebar.markdown(f'<h2 class="daily-club-title">{st.session_state.app_settings["app_name"]}</h2>', unsafe_allow_html=True)
st.sidebar.markdown(f"**User:** {curr_user['full_name']} (`@{curr_username}`)")
st.sidebar.markdown(f"**Role:** `{curr_user['role']}` | **Position:** `{curr_user['position']}`")

if curr_user["status"] == "Blocked":
    st.sidebar.error("🚨 ACCOUNT BLOCKED")

if st.sidebar.button("Logout", key="btn_logout"):
    st.session_state.authenticated_user = None
    st.rerun()

st.sidebar.divider()

if curr_user["status"] == "Blocked":
    nav_choice = "🚩 Blocked Dashboard / Appeals"
else:
    options = [
        "📌 Notice Board & News",
        "📋 Daily Attendance",
        "👥 Player Directory & Roster",
        "🖼️ Member Photo Gallery",
        "⚽ Squad Generation & Tactics",
        "⭐ Teammate Ratings & Guide",
        "⚙️ Manage Profile",
        "💬 Club House Group Chat",
        "🤖 Football AI (Public)",
        "👤 Personal AI (Private)"
    ]
    if curr_user["role"] in ["Superadmin", "Admin"]:
        options.append("⚙️ Admin Control Panel")
        
    nav_choice = st.sidebar.radio("Navigation Menu", options)

# ==========================================
# 5. BLOCKED USER SURFACE
# ==========================================
if curr_user["status"] == "Blocked":
    st.error("🚨 Your account is BLOCKED by management.")
    st.info(f"**Reason:** {curr_user.get('block_reason', 'Policy Violation')}")
    st.subheader("🚩 Report / Flag User for Fair-Play Violation")
    
    if curr_username in st.session_state.block_appeals:
        st.warning(f"Your Submitted Appeal: \"{st.session_state.block_appeals[curr_username]}\"")
    else:
        appeal_text = st.text_area("Write appeal to Superadmin:")
        if st.button("Submit Final Appeal", key="btn_appeal"):
            if appeal_text.strip():
                st.session_state.block_appeals[curr_username] = appeal_text.strip()
                save_data_to_file()
                st.success("Appeal submitted to Superadmin.")
                st.rerun()
    st.stop()

# ==========================================
# 6. NOTICE BOARD & COMMENTS
# ==========================================
if nav_choice == "📌 Notice Board & News":
    st.header("📌 Official Notice Board")
    
    if not st.session_state.notice_board:
        st.info("No notices posted yet.")
    else:
        for idx, notice in enumerate(reversed(st.session_state.notice_board)):
            with st.expander(f"📢 {notice['title']} - {notice['timestamp']} (By: {notice['author']})", expanded=(idx==0)):
                st.markdown(notice['content'])
                
                # 🗑️ Superadmin / Admin Delete Button Section
                if curr_user.get("role") in ["Superadmin", "Admin"]:
                    st.markdown("---")
                    if st.button("🗑️ Delete This Notice", key=f"del_notice_{notice['id']}", type="secondary"):
                        # Remove notice from session state
                        st.session_state.notice_board = [
                            n for n in st.session_state.notice_board if n["id"] != notice["id"]
                        ]
                        save_data_to_file()
                        st.success("Notice deleted successfully!")
                        st.rerun()
                
                st.markdown("---")
                st.markdown("##### 💬 Comments")
                comments = notice.get("comments", [])
                for c in comments:
                    st.caption(f"**{c['user']}:** {c['text']}")
                    
                comment_input = st.text_input("Add a comment:", key=f"cmt_{notice['id']}")
                if st.button("Post Comment", key=f"btn_cmt_{notice['id']}"):
                    if comment_input.strip():
                        if "comments" not in notice:
                            notice["comments"] = []
                        notice["comments"].append({
                            "user": curr_user["full_name"],
                            "text": comment_input.strip()
                        })
                        save_data_to_file()
                        st.rerun()

# ==========================================
# 📋 DAILY ATTENDANCE SHEET (ADMIN & S.A INPUT)
# ==========================================
elif nav_choice == "📋 Daily Attendance":
    st.header("📋 Daily Player Attendance Sheet")
    st.caption(f"📅 Today's Date: **{datetime.date.today().strftime('%B %d, %Y')}**")
    
    active_users = get_active_unblocked_users()
    
    if not active_users:
        st.info("No active players available in the system.")
    else:
        # -------------------------------------------------------------
        # 🟢 SUPERADMIN & ADMIN EDIT MODE
        # -------------------------------------------------------------
        if curr_user.get("role") in ["Superadmin", "Admin"]:
            st.markdown("### ⚙️ Mark Attendance for All Players")
            st.caption("Select attendance status for each player and click save.")
            
            with st.form("admin_attendance_form"):
                updated_attendance = {}
                
                # Header layout
                h_col1, h_col2, h_col3 = st.columns([3, 2, 4])
                with h_col1:
                    st.markdown("**Player Name**")
                with h_col2:
                    st.markdown("**Position**")
                with h_col3:
                    st.markdown("**Attendance Status**")
                
                st.divider()
                
                # Player list with radio buttons
                for username, user_info in active_users.items():
                    col1, col2, col3 = st.columns([3, 2, 4])
                    
                    with col1:
                        st.markdown(f"**{user_info['full_name']}** (`@{username}`)")
                    with col2:
                        st.markdown(f"`{user_info.get('position', 'N/A')}`")
                    with col3:
                        # Get existing status or default to "Present"
                        current_status = st.session_state.player_stats.get(username, {}).get("attendance", "Present")
                        status_options = ["Present", "Absent", "Late", "Injured"]
                        default_idx = status_options.index(current_status) if current_status in status_options else 0
                        
                        selected_status = st.radio(
                            f"Status_{username}",
                            options=status_options,
                            index=default_idx,
                            key=f"att_radio_{username}",
                            horizontal=True,
                            label_visibility="collapsed"
                        )
                        updated_attendance[username] = selected_status
                
                st.markdown("---")
                submit_att = st.form_submit_button("💾 Save & Publish Attendance", type="primary")
                
                if submit_att:
                    for username, status in updated_attendance.items():
                        if username not in st.session_state.player_stats:
                            st.session_state.player_stats[username] = {}
                        st.session_state.player_stats[username]["attendance"] = status
                        
                        # Injured থাকলে ইঞ্জার্ড লিস্টে আপডেট করার অটো-লজিক
                        if status == "Injured":
                            if username not in st.session_state.injured_players:
                                st.session_state.injured_players.append(username)
                        else:
                            if username in st.session_state.injured_players:
                                st.session_state.injured_players.remove(username)
                    
                    save_data_to_file()
                    st.success("✅ Attendance updated successfully for all players!")
                    st.rerun()

        # -------------------------------------------------------------
        # 🔵 GENERAL PLAYER VIEW MODE (READ ONLY)
        # -------------------------------------------------------------
        else:
            st.info("🔒 Read-Only Mode: Only Superadmin and Admins can modify attendance.")
            st.markdown("### 📊 Today's Player Status")
            
            att_summary = []
            for username, user_info in active_users.items():
                status = st.session_state.player_stats.get(username, {}).get("attendance", "Present")
                
                # Status formatting with emojis
                status_icon = "✅ Present" if status == "Present" else ("❌ Absent" if status == "Absent" else ("⏰ Late" if status == "Late" else "🏥 Injured"))
                
                att_summary.append({
                    "Player Name": user_info['full_name'],
                    "Username": f"@{username}",
                    "Position": user_info.get('position', 'N/A'),
                    "Status": status_icon
                })
            
            st.table(att_summary)
            
# ==========================================
# 7. PLAYER DIRECTORY & SPECIAL ROSTERS
# ==========================================
elif nav_choice == "👥 Player Directory & Roster":
    st.header("👥 Player Directory & Roster")
    tab1, tab2, tab3 = st.tabs(["📋 Public Directory", "⭐ Star Players List", "🏥 Injured Players List"])
    
    active_users = get_active_unblocked_users()
    
    with tab1:
        dir_data = []
        for u, d in active_users.items():
            dir_data.append({
                "Username": u,
                "Full Name": d["full_name"],
                "Jersey #": d["jersey_num"],
                "Jersey Name": d["jersey_name"],
                "Position": d["position"],
                "Role": d["role"]
            })
        st.dataframe(pd.DataFrame(dir_data), use_container_width=True)

    with tab2:
        star_players = [u for u, d in active_users.items() if d.get("is_star")]
        if not star_players:
            st.info("No star players at the moment.")
        else:
            for sp in star_players:
                u = active_users[sp]
                r = compute_player_rating(sp)
                st.success(f"🌟 **{u['full_name']}** (`@{sp}`) - Position: {u['position']} | Rating: **{r}**")

    with tab3:
        if not st.session_state.injured_players:
            st.info("No injured players listed.")
        else:
            for ip in st.session_state.injured_players:
                if ip in active_users:
                    u = active_users[ip]
                    st.warning(f"🩹 **{u['full_name']}** (`@{ip}`) - Position: {u['position']}")

# ==========================================
# 8. MEMBER PHOTO GALLERY
# ==========================================
elif nav_choice == "🖼️ Member Photo Gallery":
    st.header("🖼️ Member Photo Gallery")
    active_users = get_active_unblocked_users()
    photo_users = [u for u, data in active_users.items() if data.get("photo_b64")]
    
    if not photo_users:
        st.info("No member profile photos available.")
    else:
        cols = st.columns(3)
        for idx, u in enumerate(photo_users):
            udata = active_users[u]
            img_bytes = base64.b64decode(udata["photo_b64"])
            image = Image.open(io.BytesIO(img_bytes))
            with cols[idx % 3]:
                st.image(image, use_container_width=True)
                st.caption(f"👤 **{udata['full_name']}** (@{u})")

# ==========================================
# 9. SQUAD GENERATION & TACTICS
# ==========================================
elif nav_choice == "⚽ Squad Generation & Tactics":
    st.header("⚽ Tactical Squad Generator")
    
    if curr_user["role"] not in ["Superadmin", "Admin"]:
        st.warning("🔒 Only Superadmin/Admin can generate squads.")
    
    day_sel = st.selectbox("Operation Mode", ["Saturday Match Squad", "Practice Day Split (Mon-Thu)"])
    
    active_users = get_active_unblocked_users()
    max_avail = len(active_users)
    
    # ---------------------------------------------------------
    # MODE 1: SATURDAY MATCH SQUAD
    # ---------------------------------------------------------
    if day_sel == "Saturday Match Squad":
        if curr_user["role"] in ["Superadmin", "Admin"]:
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                target_count = st.number_input(
                    "🔢 Select Squad Size (Starters):", 
                    min_value=1, 
                    max_value=max_avail if max_avail > 0 else 11, 
                    value=min(11, max_avail if max_avail > 0 else 11),
                    step=1
                )
            with col_s2:
                custom_formation = st.text_input("📐 Enter Team Formation (e.g., 4-3-3, 3-2-1):", value="4-3-3")
        else:
            target_count = st.session_state.match_settings.get("asmb_player_count", 11)
            custom_formation = "Adaptive Formation"
            st.info(f"Target Squad Size: **{target_count} Players**")
        
        if curr_user["role"] in ["Superadmin", "Admin"] and st.button("Generate Match Squad", key="btn_gen_sq"):
            available = [u for u in active_users.keys() if u not in st.session_state.injured_players and st.session_state.player_stats.get(u, {}).get("attendance") != "Absent"]
            
            # Rule: Positional Conflict Filter (Same position highest rated player gets priority)
            pos_groups = {}
            for u in available:
                pos = active_users[u]["position"]
                pos_groups.setdefault(pos, []).append(u)
                
            selected_squad = []
            for pos, plist in pos_groups.items():
                plist_sorted = sorted(plist, key=lambda x: compute_player_rating(x), reverse=True)
                selected_squad.append(plist_sorted[0])  # Take highest rated per position
                
            rem_players = [u for u in available if u not in selected_squad]
            rem_players_sorted = sorted(rem_players, key=lambda x: compute_player_rating(x), reverse=True)
            
            needed = target_count - len(selected_squad)
            if needed > 0:
                selected_squad.extend(rem_players_sorted[:needed])
                subs = rem_players_sorted[needed:]
            else:
                subs = rem_players_sorted
                
            starters = selected_squad[:target_count]
            
            st.markdown(f"### 🏆 Starting Lineup ({len(starters)} Players)")
            notice_text = f"### ⚽ Match Squad Announcement ({datetime.date.today()})\n\n**Starting Lineup:**\n"
            
            for idx, p in enumerate(starters, 1):
                r = compute_player_rating(p)
                u = active_users[p]
                line = f"{idx}. **{u['full_name']}** (`@{p}`) - Pos: {u['position']} | Rating: **{r}**"
                st.markdown(line)
                notice_text += f"{line}\n"
                
            if subs:
                st.markdown(f"### 🔄 Substitutes ({len(subs)} Players)")
                notice_text += f"\n**Substitutes:**\n"
                for idx, p in enumerate(subs, 1):
                    r = compute_player_rating(p)
                    u = active_users[p]
                    line = f"Sub {idx}: **{u['full_name']}** (`@{p}`) - Pos: {u['position']} | Rating: **{r}**"
                    st.markdown(line)
                    notice_text += f"{line}\n"
                    
            formation = f"{custom_formation} ({len(starters)}-a-side)"
            notice_text += f"\n**Formation:** {formation}"
            
            st.session_state.notice_board.append({
                "id": len(st.session_state.notice_board) + 1,
                "author": "Football AI",
                "title": f"Match Squad ({target_count}-a-side)",
                "content": notice_text,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "comments": []
            })
            
            st.session_state.match_settings["asmb_player_count"] = target_count
            save_data_to_file()
            st.success(f"{target_count}-a-side Squad published to Notice Board!")

    # ---------------------------------------------------------
    # MODE 2: PRACTICE DAY SPLIT (TWO BALANCED TEAMS)
    # ---------------------------------------------------------
    elif day_sel == "Practice Day Split (Mon-Thu)":
        st.subheader("🏃 Practice Match Balanced Team Generator")
        
        if curr_user["role"] in ["Superadmin", "Admin"]:
            practice_formation = st.text_input("📐 Practice Tactical Formation (e.g., 3-2-1, 2-3-1):", value="Balanced Practice Formation")
            
            if st.button("Generate Balanced Teams", key="btn_gen_practice"):
                available = [u for u in active_users.keys() if u not in st.session_state.injured_players and st.session_state.player_stats.get(u, {}).get("attendance") != "Absent"]
                
                if len(available) < 2:
                    st.error("Need at least 2 active players to generate practice teams.")
                else:
                    # Sort players by rating descending
                    sorted_players = sorted(available, key=lambda x: compute_player_rating(x), reverse=True)
                    
                    team_tp = []
                    team_el = []
                    
                    # Snake Draft Allocation Logic for Rating Balance (1->A, 2->B, 3->B, 4->A, 5->A, 6->B...)
                    for idx, p in enumerate(sorted_players):
                        if (idx // 2) % 2 == 0:
                            if idx % 2 == 0:
                                team_tp.append(p)
                            else:
                                team_el.append(p)
                        else:
                            if idx % 2 == 0:
                                team_el.append(p)
                            else:
                                team_tp.append(p)
                                
                    tp_ratings = [compute_player_rating(p) for p in team_tp]
                    el_ratings = [compute_player_rating(p) for p in team_el]
                    
                    avg_tp = round(sum(tp_ratings) / len(tp_ratings), 2) if tp_ratings else 0.0
                    avg_el = round(sum(el_ratings) / len(el_ratings), 2) if el_ratings else 0.0
                    
                    col_t1, col_t2 = st.columns(2)
                    
                    # Team TP Output
                    with col_t1:
                        st.markdown(f"### 🐯 🐅 Tigers & Panthers ({len(team_tp)} Players)")
                        st.caption(f"Average Team Rating: **{avg_tp}**")
                        for idx, p in enumerate(team_tp, 1):
                            u = active_users[p]
                            r = compute_player_rating(p)
                            st.markdown(f"{idx}. **{u['full_name']}** (`@{p}`) - Pos: {u['position']} | Rating: **{r}**")
                            
                    # Team EL Output
                    with col_t2:
                        st.markdown(f"### 🦅 🦁 Eagles & Lions ({len(team_el)} Players)")
                        st.caption(f"Average Team Rating: **{avg_el}**")
                        for idx, p in enumerate(team_el, 1):
                            u = active_users[p]
                            r = compute_player_rating(p)
                            st.markdown(f"{idx}. **{u['full_name']}** (`@{p}`) - Pos: {u['position']} | Rating: **{r}**")
                            
                    # Prepare Notice Text for Practice Match
                    notice_text = f"### 🏃 Practice Match Teams - {datetime.date.today()}\n"
                    notice_text += f"**Formation:** {practice_formation}\n\n"
                    
                    notice_text += f"**🐯 🐅 Tigers & Panthers (Avg Rating: {avg_tp}):**\n"
                    for idx, p in enumerate(team_tp, 1):
                        u = active_users[p]
                        notice_text += f"{idx}. {u['full_name']} (@{p}) - Pos: {u['position']} ({compute_player_rating(p)})\n"
                        
                    notice_text += f"\n**🦅 🦁 Eagles & Lions (Avg Rating: {avg_el}):**\n"
                    for idx, p in enumerate(team_el, 1):
                        u = active_users[p]
                        notice_text += f"{idx}. {u['full_name']} (@{p}) - Pos: {u['position']} ({compute_player_rating(p)})\n"
                        
                    st.session_state.notice_board.append({
                        "id": len(st.session_state.notice_board) + 1,
                        "author": "Football AI",
                        "title": f"Practice Match Split ({len(available)} Players)",
                        "content": notice_text,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "comments": []
                    })
                    save_data_to_file()
                    st.success("Balanced practice teams published to Notice Board!")
        else:
            st.info("Practice teams can only be generated by Superadmin/Admin.")
            
# ==========================================
# 10. RATINGS & RATING GUIDE
# ==========================================
elif nav_choice == "⭐ Teammate Ratings & Guide":
    st.header("⭐ Rate Teammates & Performance Guide")
    
    with st.expander("📘 Rating Guide Panel (Click to expand)"):
    st.markdown("""
    ### ⚽ Player Rating Guide
    * **১০.০:** রূপকথাতুল্য বা সর্বকালের সেরা পারফরম্যান্স (যেমন: হ্যাটট্রিক + একাধিক অ্যাসিস্ট)।
    * **৯.০ - ৯.৯:** ম্যাচের একক নায়ক এবং ম্যাচজেতানো অসাধারণ নৈপুণ্য।
    * **৮.০ - ৮.৯:** চমৎকার খেলা, যার মধ্যে গুরুত্বপূর্ণ গোল বা অ্যাসিস্ট রয়েছে।
    * **৭.০ - ৭.৯:** নির্ভরযোগ্য ও ভালো পারফরম্যান্স, কোনো বড় ভুল ছাড়া।
    * **৬.০ - ৬.৯:** সাধারণ বা গড়পড়তা পারফরম্যান্স (ম্যাচ শুরুর সাধারণ বেস পয়েন্ট)।
    * **৫.০ - ৫.৯:** প্রভাবহীন ও হতাশাজনক খেলা বা সুযোগ হাতছাড়া করা।
    * **৪.০ - ৪.৯:** বাজে খেলা এবং পেনাল্টি বা প্রতিপক্ষকে সুযোগ উপহার দেওয়া।
    * **৩.০ - ৩.৯:** একের পর এক গুরুতর ভুল করে দলকে বিপদে ফেলা।
    * **১.০ - ২.৯:** লাল কার্ড পাওয়া বা আত্মঘাতী গোল করে ম্যাচ হারানো বিপর্যয়কর পারফরম্যান্স।
    * **০.০:** ইচ্ছাকৃতভাবে দলের ক্ষতি করা বা চরমতম ব্যর্থতা।

    ---
    ### ⚠️ Foul Rating Guide
    * **০:** একটি ফাউলও করেনি, একদম পরিচ্ছন্ন ও ফেয়ার প্লে বজায় রেখেছে।
    * **১:** মাত্র ১টি সাধারণ ও হালকা ফাউল করেছে (কোনো কার্ড নেই)।
    * **২:** ২টির মতো ছোটখাটো ফাউল করেছে, যেগুলো ট্যাকল বা বল দখলের চেষ্টা ছিল।
    * **৩:** বেশ কয়েকটি ছোট ফাউল করেছে, রেফারি মৌখিক সতর্কবার্তা দিয়েছেন।
    * **৪:** বারবার ফাউল করায় রেফারি শেষ সতর্কবার্তা (Final Warning) দিয়েছেন।
    * **৫:** আক্রমণ থামানোর জন্য কৌশলগত বা একটু কঠিন ফাউল করে হলুদ কার্ড খেয়েছে।
    * **৬:** ম্যাচে ২টি আলাদা ফাউলের কারণে ১টি হলুদ কার্ড পেয়েছে।
    * **৭:** ক্রমাগত বা ফাউলের ওপর ফাউল করে দলকে ঝুঁকিতে ফেলেছে।
    * **৮:** বিপজ্জনক বা খারাপ ট্যাকল করে সরাসরি লাল কার্ড পেয়ে মাঠ ছেড়েছে।
    * **৯:** চরম সহিংস বা উগ্র আচরণ করে ফাউল এবং সরাসরি লাল কার্ড খেয়েছে।
    * **১০:** ম্যাচের সবচেয়ে বেশি বা ক্ষতিকর ফাউলকারী (বিপজ্জনক ফাউল + লাল কার্ড + পেনাল্টি দেওয়া)।

    ---
    ### 🧤 Goalkeeper (GK) Rating Guide
    * **১০.০:** অবিশ্বসনীয় বা ম্যাচজেতানো সেভ (যেমন: শেষ মুহূর্তে পেনাল্টি সেভ বা ৪+ নিশ্চিত গোল বাঁচানো)।
    * **৯.০ - ৯.৯:** একের পর এক দুর্দান্ত সেভ করে দলকে একাই জয় এনে দেওয়া।
    * **৮.০ - ৮.৯:** অন্তত ৩-৪টি নিশ্চিত গোলের সেভ এবং ক্লিন শিট (Clean Sheet) বজায় রাখা।
    * **৭.০ - ৭.৯:** নির্ভরযোগ্য পারফরম্যান্স, সাধারণ সেভগুলো ঠিকঠাক করা এবং বড় কোনো ভুল না করা।
    * **৬.০ - ৬.৯:** গড়পড়তা খেলা (ম্যাচ শুরুর বেস পয়েন্ট), যেখানে গোলরক্ষককে খুব বেশি পরীক্ষা দিতে হয়নি।
    * **৫.০ - ৫.৯:** দুর্বল শট ক্লিয়ার করতে না পারা বা নিজের পজিশনিংয়ে হালকা ভুল থাকা।
    * **৪.০ - ৪.৯:** সহজ বলে হাত থেকে মিস করে বিপদ বাড়ানো বা বাজে পেনাল্টি দেওয়া।
    * **৩.০ - ৩.৯:** সহজ শটে গোল হজম করা এবং পাসিংয়ে বারবার ভুল করা।
    * **১.০ - ২.৯:** মারাত্মক ভুল (Howler) করে গোল খাওয়া বা লাল কার্ড পেয়ে মাঠ ছাড়া।
    * **০.০:** চরম বিপর্যয়কর পারফরম্যান্স (যেমন: একাধিক বাজে ভুল এবং আত্মঘাতী গোলে ম্যাচ হারানো)।
    """)
        
    active_users = get_active_unblocked_users()
    targets = [u for u in active_users.keys() if u != curr_username]
    
    if targets:
        target = st.selectbox("Select Teammate:", targets)
        prev = st.session_state.ratings_db.get((curr_username, target), {"rating": 6.0, "fouls": 0})
        
        new_r = st.slider("Rating (0.0 - 10.0)", 0.0, 10.0, float(prev["rating"]), 0.1)
        new_f = st.number_input("Fouls (0 - 10)", 0, 10, int(prev["fouls"]), 1)
        
        if st.button("Save/Correct Rating", key="btn_save_r"):
            st.session_state.ratings_db[(curr_username, target)] = {"rating": round(new_r, 2), "fouls": new_f}
            save_data_to_file()
            st.success("Rating saved!")

# ==========================================
# 11. MANAGE PROFILE (WITHOUT POSITION)
# ==========================================
elif nav_choice == "⚙️ Manage Profile":
    st.header("⚙️ Edit Profile")
    st.warning("🔒 Position can only be changed by Admin/Superadmin.")
    
    new_fn = st.text_input("Full Name:", value=curr_user["full_name"])
    new_jn = st.number_input("Jersey Number:", 1, 99, int(curr_user["jersey_num"]))
    new_jname = st.text_input("Jersey Player Name:", value=curr_user["jersey_name"])
    new_pai = st.text_input("Personal AI Name:", value=curr_user["personal_ai_name"])
    
    pic = st.file_uploader("Update Profile Photo:", type=["jpg", "png", "jpeg"])
    
    if st.button("Save Profile Updates", key="btn_prof_save"):
        curr_user["full_name"] = new_fn
        curr_user["jersey_num"] = new_jn
        curr_user["jersey_name"] = new_jname
        curr_user["personal_ai_name"] = new_pai
        if pic:
            curr_user["photo_b64"] = base64.b64encode(pic.read()).decode('utf-8')
        save_data_to_file()
        st.success("Profile updated!")
        st.rerun()

# ==========================================
# 12. CLUB HOUSE CHAT
# ==========================================
elif nav_choice == "💬 Club House Group Chat":
    st.header("💬 Member Chat")
    
    for msg in st.session_state.group_chat:
        st.markdown(f"**[{msg['timestamp']}] {msg['sender']}:** {msg['message']}")
        
    m = st.text_input("Type message...", key="chat_in")
    if st.button("Send", key="btn_chat_send"):
        if m.strip():
            st.session_state.group_chat.append({
                "sender": f"{curr_user['full_name']} (@{curr_username})",
                "message": m.strip(),
                "timestamp": datetime.datetime.now().strftime("%H:%M")
            })
            save_data_to_file()
            st.rerun()

# ==========================================
# 13. FOOTBALL AI (PUBLIC) WITH ANTI-LINK LEAK
# ==========================================
elif nav_choice == "🤖 Football AI (Public)":
    st.header("🤖 Football AI (Public - Tactics Only)")
    
    for chat in st.session_state.football_ai_chats:
        st.markdown(f"**👤 {chat['sender']}:** {chat['prompt']}")
        st.markdown(f"🤖 **Football AI:** {chat['response']}")
        st.divider()
        
    p = st.text_input("Ask Football AI regarding tactics/strategies:", key="fai_in")
    if st.button("Ask Football AI", key="btn_fai"):
        if p.strip():
            text = p.strip()
            
            # Anti-link and Anti-Scraping Feature
            if re.search(r'http[s]?://|www\.', text) or "link" in text.lower() or "feature" in text.lower() and "app" in text.lower():
                resp = "নিরাপত্তাজনিত কারণে অ্যাপের কোনো লিংক বা অভ্যন্তরীণ ফিচার ও আর্কিটেকচার বিশ্লেষণ বা প্রকাশ করা নিষিদ্ধ।"
            elif any(k in text.lower() for k in ["weather", "recipe", "math", "code", "movie", "song"]):
                resp = f"এটি ফুটবলের বাইরে প্রশ্ন। প্রশ্নটি স্বয়ংক্রিয়ভাবে আপনার **Personal AI ({curr_user['personal_ai_name']})** পেজে রিডাইরেক্ট করা হলো।"
                st.session_state.personal_ai_chats.setdefault(curr_username, []).append({
                    "prompt": text,
                    "response": f"হ্যালো {curr_user['full_name']}! আপনার প্রশ্নটির উত্তর নিয়ে আমি কাজ করছি।",
                    "timestamp": datetime.datetime.now().strftime("%H:%M")
                })
            else:
                resp = f"'{text}' সম্পর্কিত ট্যাকটিক্যাল পরামর্শ: ফর্মেশন কমপ্যাক্ট রাখুন, হাই-প্রেসিং করুন এবং উইং দিয়ে দ্রুত কাউন্টার অ্যাটাকে যান।"
                
            st.session_state.football_ai_chats.append({
                "sender": curr_user["full_name"],
                "prompt": text,
                "response": resp,
                "timestamp": datetime.datetime.now().strftime("%H:%M")
            })
            save_data_to_file()
            st.rerun()

# ==========================================
# 14. PERSONAL AI & MOTM VOTING
# ==========================================
elif nav_choice == "👤 Personal AI (Private)":
    pai_name = curr_user["personal_ai_name"]
    st.header(f"👤 {pai_name} (Private AI)")
    
    user_pchats = st.session_state.personal_ai_chats.setdefault(curr_username, [])
    
    for chat in user_pchats:
        st.markdown(f"**You:** {chat['prompt']}")
        st.markdown(f"🤖 **{pai_name}:** {chat['response']}")
        st.divider()
        
    p = st.text_input(f"Ask {pai_name} anything:", key="pai_in")
    if st.button("Send", key="btn_pai"):
        if p.strip():
            text = p.strip()
            if re.search(r'http[s]?://|www\.', text) or ("link" in text.lower() and "feature" in text.lower()):
                resp = "দুঃখিত, কোনো অ্যাপ লিংক থেকে তথ্য বা ফিচার বিশ্লেষণ করা আমার জন্য নিষিদ্ধ।"
            else:
                resp = f"হ্যালো {curr_user['full_name']}! আপনার প্রশ্ন: '{text}'। বাংলা ভাষায় যেকোনো তথ্যে আমি সাহায্য করতে পারি।"
                
            user_pchats.append({
                "prompt": text,
                "response": resp,
                "timestamp": datetime.datetime.now().strftime("%H:%M")
            })
            save_data_to_file()
            st.rerun()
            
    st.divider()
    st.subheader("🗳️ Sunday MOTM Poll")
    active_users = get_active_unblocked_users()
    vote = st.selectbox("Vote MOTM:", list(active_users.keys()), key="motm_sel")
    if st.button("Submit Vote", key="btn_motm"):
        st.session_state.motm_votes[curr_username] = vote
        save_data_to_file()
        st.success(f"Vote cast for @{vote}!")

# ==========================================
# 15. ADMIN CONTROL PANEL
# ==========================================
elif nav_choice == "⚙️ Admin Control Panel":
    st.header("⚙️ Admin Control Panel")
    
    if curr_user["role"] not in ["Superadmin", "Admin"]:
        st.error("Access Denied.")
        st.stop()
        
    t1, t2, t3, t4, t5 = st.tabs(["🎨 Branding & Limit", "👑 Roles & Password", "🚫 Block System", "📊 Match Stats & GK Saves", "🧹 Master Reset"])
    
    with t1:
        st.session_state.app_settings["app_name"] = st.text_input("App Name:", st.session_state.app_settings["app_name"])
        st.session_state.app_settings["max_register_limit"] = st.number_input("Max Member Limit:", 1, 200, int(st.session_state.app_settings["max_register_limit"]))
        cpic = st.file_uploader("Upload Club Logo/Photo:", type=["jpg", "png", "jpeg"])
        if cpic:
            st.session_state.app_settings["club_photo_b64"] = base64.b64encode(cpic.read()).decode('utf-8')
        if st.button("Save Settings", key="btn_save_brand"):
            save_data_to_file()
            st.success("Branding updated!")

    with t2:
        target_u = st.selectbox("Select User:", list(st.session_state.users.keys()))
        new_pos = st.selectbox("Assign Position:", ["GK", "CB", "LB", "RB", "CM", "CAM", "RW", "LW", "ST"])
        if st.button("Update Position", key="btn_adm_pos"):
            st.session_state.users[target_u]["position"] = new_pos
            save_data_to_file()
            st.success("Position updated!")
            
        if curr_user["role"] == "Superadmin":
            new_pass = st.text_input("Force Change Password:", key="adm_fpass")
            if st.button("Change Password", key="btn_fpass"):
                st.session_state.users[target_u]["password"] = new_pass
                save_data_to_file()
                st.success("Password changed!")

    with t3:
        btarget = st.selectbox("Target Player to Block/Unblock:", list(st.session_state.users.keys()), key="bsel")
        breason = st.text_input("Reason for Block (Mandatory):", key="breas")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("Block Player", key="btn_blk"):
                if breason.strip():
                    u = st.session_state.users[btarget]
                    u["status"] = "Blocked"
                    u["block_reason"] = breason.strip()
                    save_data_to_file()
                    st.warning("Player blocked.")
                    st.rerun()
                else:
                    st.error("Block reason is mandatory!")
        with col_b2:
            if st.button("Unblock Player", key="btn_unblk"):
                st.session_state.users[btarget]["status"] = "Active"
                save_data_to_file()
                st.success("Player unblocked.")
                st.rerun()
                
        st.subheader("📜 Blocked Players List")
        for bu, bd in st.session_state.users.items():
            if bd.get("status") == "Blocked":
                st.error(f"🚨 **{bd['full_name']}** (`@{bu}`) - Reason: {bd.get('block_reason')}")

    with t4:
        st.subheader("⚽ Match Stats, GK Saves & Conceded Goals")
        st.session_state.match_settings["goals_conceded"] = st.number_input("Match Goals Conceded (Team):", 0, 20, int(st.session_state.match_settings.get("goals_conceded", 0)))
        
        stat_u = st.selectbox("Select Player:", list(st.session_state.users.keys()), key="stat_u_sel")
        pstats = st.session_state.player_stats.setdefault(stat_u, {"goals": 0, "assists": 0, "conceded_penalty": 0.0, "attendance": "Present", "rating_penalty": 0.0, "gk_saves": 0})
        
        c1, c2, c3 = st.columns(3)
        with c1:
            pstats["goals"] = st.number_input("Goals:", 0, 50, int(pstats.get("goals", 0)))
        with c2:
            pstats["assists"] = st.number_input("Assists:", 0, 50, int(pstats.get("assists", 0)))
        with c3:
            pstats["gk_saves"] = st.number_input("GK Saves:", 0, 50, int(pstats.get("gk_saves", 0)))
            
        if st.button("Save Stats", key="btn_sav_stats"):
            save_data_to_file()
            st.success("Stats updated!")

    with t5:
        if curr_user["role"] == "Superadmin":
            if st.button("🔥 EXECUTE MASTER RESET", key="btn_mr"):
                st.session_state.group_chat = []
                st.session_state.football_ai_chats = []
                st.session_state.personal_ai_chats = {}
                save_data_to_file()
                st.success("Master Reset completed! Chats purged while keeping user IDs intact.")
                st.rerun()
