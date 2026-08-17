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
            img_bytes = base64.b64encode(st.session_state.app_settings["club_photo_b64"])
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
                if user.get("password") == login_password:
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
                "sec_key": reg_sec_key.strip(),
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
        fp_sec_key = st.text_input("Enter Security Key:", key="fp_sec_key", type="password").strip()
        fp_new_pass = st.text_input("Enter New Password:", key="fp_new_pass", type="password").strip()
        
        if st.button("Reset Password", key="btn_fp_reset"):
            if not fp_uname or not fp_sec_key or not fp_new_pass:
                st.error("Please fill in all fields (Username, Security Key, New Password)!")
            elif fp_uname in st.session_state.users:
                u = st.session_state.users[fp_uname]
                stored_sec_key = str(u.get("sec_key", "")).strip()
                
                if stored_sec_key and stored_sec_key == fp_sec_key:
                    u["password"] = fp_new_pass
                    save_data_to_file()
                    st.success("Password successfully updated! Please login with your new password.")
                elif not stored_sec_key:
                    st.error("Security Key not set for this user. Contact Admin!")
                else:
                    st.error("Incorrect Security Key!")
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
    st.info("📅 **Saturday Pre-Match Poll:** আগামীকাল রবিবারের (Sunday Matchday) ম্যাচে কি তুই খেলবি?")
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
# 6. NOTICE BOARD & COMMENTS (WITH POLL VOTE)
# ==========================================
if nav_choice == "📌 Notice Board & News":
    st.header("📌 Official Notice Board")
    
    if not st.session_state.notice_board:
        st.info("No notices posted yet.")
    else:
        for idx, notice in enumerate(reversed(st.session_state.notice_board)):
            with st.expander(f"📢 {notice['title']} - {notice['timestamp']} (By: {notice['author']})", expanded=(idx==0)):
                st.markdown(notice['content'])
                
                # 📊 Poll Voting Section
                if notice.get("poll_options"):
                    st.markdown("---")
                    st.markdown("#### 🗳️ Cast Your Vote")
                    
                    options = notice.get("poll_options", [])
                    votes = notice.setdefault("poll_votes", {})  # {username: selected_option}
                    
                    # Get existing vote of current user
                    current_vote = votes.get(st.session_state.authenticated_user)
                    default_index = options.index(current_vote) if current_vote in options else 0
                    
                    selected_option = st.radio(
                        "Select an option:",
                        options=options,
                        index=default_index,
                        key=f"poll_select_{notice['id']}"
                    )
                    
                    if st.button("Submit Vote", key=f"btn_vote_{notice['id']}", type="primary"):
                        votes[st.session_state.authenticated_user] = selected_option
                        save_data_to_file()
                        st.success(f"✅ Vote for '{selected_option}' submitted!")
                        st.rerun()
                    
                    # 📈 Live Results Display
                    st.markdown("##### 📊 Live Poll Results")
                    total_votes = len(votes)
                    if total_votes > 0:
                        for opt in options:
                            count = list(votes.values()).count(opt)
                            pct = (count / total_votes) * 100
                            st.write(f"**{opt}** — {count} vote(s) ({pct:.1f}%)")
                            st.progress(pct / 100)
                    else:
                        st.info("No votes cast yet. Be the first to vote!")
                
                # 🗑️ Superadmin / Admin Delete Button Section
                if curr_user.get("role") in ["Superadmin", "Admin"]:
                    st.markdown("---")
                    if st.button("🗑️ Delete This Notice", key=f"del_notice_{notice['id']}", type="secondary"):
                        st.session_state.notice_board = [
                            n for n in st.session_state.notice_board if n["id"] != notice["id"]
                        ]
                        save_data_to_file()
                        st.success("Notice deleted successfully!")
                        st.rerun()
                
                # 💬 Comments Section
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
# 7. PLAYER DIRECTORY & SPECIAL ROSTERS (WITH SERIAL NUMBERS)
# ==========================================
elif nav_choice == "👥 Player Directory & Roster":
    st.header("👥 Player Directory & Roster")
    tab1, tab2, tab3 = st.tabs(["📋 Public Directory", "⭐ Star Players List", "🏥 Injured Players List"])
    
    active_users = get_active_unblocked_users()
    
    with tab1:
        dir_data = []
        # serial number সহ লিস্ট তৈরি
        for idx, (u, d) in enumerate(active_users.items(), 1):
            dir_data.append({
                "#": idx,
                "Username": u,
                "Full Name": d["full_name"],
                "Jersey #": d["jersey_num"],
                "Jersey Name": d["jersey_name"],
                "Position": d["position"],
                "Role": d["role"]
            })
        
        df = pd.DataFrame(dir_data)
        if not df.empty:
            # Table-এর ডিফল্ট 0 ইনডেক্স লুকিয়ে # কলামটিকে দৃশ্যমান করা
            st.dataframe(df.set_index("#"), use_container_width=True)
        else:
            st.info("No active players found.")

    with tab2:
        star_players = [u for u, d in active_users.items() if d.get("is_star")]
        if not star_players:
            st.info("No star players at the moment.")
        else:
            # ১, ২, ৩ নম্বর দিয়ে স্টার প্লেয়ার দেখানো
            for idx, sp in enumerate(star_players, 1):
                u = active_users[sp]
                r = compute_player_rating(sp)
                st.success(f"{idx}. 🌟 **{u['full_name']}** (`@{sp}`) - Position: {u['position']} | Rating: **{r}**")

    with tab3:
        if not st.session_state.injured_players:
            st.info("No injured players listed.")
        else:
            # ১, ২, ৩ নম্বর দিয়ে ইনজুরড প্লেয়ার দেখানো
            count = 1
            for ip in st.session_state.injured_players:
                if ip in active_users:
                    u = active_users[ip]
                    st.warning(f"{count}. 🩹 **{u['full_name']}** (`@{ip}`) - Position: {u['position']}")
                    count += 1
                    
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
# 9. SQUAD GENERATION & TACTICS (WITH SMART POSITION MATCHING)
# ==========================================
elif nav_choice == "⚽ Squad Generation & Tactics":
    st.header("⚽ Tactical Squad Generator")
    
    if curr_user["role"] not in ["Superadmin", "Admin"]:
        st.warning("🔒 Only Superadmin/Admin can generate squads.")
    
    day_sel = st.selectbox("Operation Mode", ["Saturday Match Squad", "Practice Day Split (Mon-Thu)"])
    
    active_users = get_active_unblocked_users()
    max_avail = len(active_users)
    
    # Helper function for visual box creation
    def generate_visual_formation_box(gk_name, field_dict):
        def get_p(pos_key):
            return field_dict.get(pos_key, "Vacant")

        box = f"""
               [ 🧤 গোলরক্ষক (GK): {gk_name} ]
                               |
+---------------------------------------------------------------------------------+
| (LB): {get_p('LB')} | (LCB): {get_p('LCB')} | (RCB): {get_p('RCB')} | (RB): {get_p('RB')} | <-- ৪ জন ডিফেন্ডার
+---------------------------------------------------------------------------------+
                               |
       +-----------------------------------------------------------+
       | (LCM): {get_p('LCM')} | (CM): {get_p('CM')} | (RCM): {get_p('RCM')} | <-- ৩ জন মিডফিল্ডার
       +-----------------------------------------------------------+
                               |
                      +------------------+
                      | (LS): {get_p('LS')} | (RS): {get_p('RS')} | <-- ২ জন স্ট্রাইকার
                      +------------------+
        """
        return box

    # ---------------------------------------------------------
    # MODE 1: SATURDAY MATCH SQUAD
    # ---------------------------------------------------------
    if day_sel == "Saturday Match Squad":
        if curr_user["role"] in ["Superadmin", "Admin"]:
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                target_count = st.number_input(
                    "🔢 Select Field Squad Size (Starters):", 
                    min_value=1, 
                    max_value=max_avail if max_avail > 0 else 11, 
                    value=min(10, max_avail if max_avail > 0 else 10),
                    step=1
                )
            with col_s2:
                fmt_mode = st.radio("📐 Formation Input:", ["🤖 AI Auto-Select", "✍️ Manual Custom"], horizontal=True)
                if fmt_mode == "✍️ Manual Custom":
                    custom_formation = st.text_input("Enter Formation (e.g., 4-3-2):", value="4-3-2")
                else:
                    custom_formation = "AI Auto-Selected (4-3-2 Standard)"
        else:
            target_count = st.session_state.match_settings.get("asmb_player_count", 10)
            custom_formation = "Adaptive Formation"
            st.info(f"Target Squad Size: **{target_count} Field Players + GK**")
        
        if curr_user["role"] in ["Superadmin", "Admin"] and st.button("Generate Match Squad", key="btn_gen_sq", type="primary"):
            available = [u for u in active_users.keys() if u not in st.session_state.injured_players and st.session_state.player_stats.get(u, {}).get("attendance") != "Absent"]
            
            # 1. Separate Goalkeepers (GK) & Field Players strictly
            gk_candidates = [u for u in available if active_users[u].get("position") == "GK"]
            field_candidates = [u for u in available if active_users[u].get("position") != "GK"]
            
            # GK Selection: Highest rated original GK gets preference
            gk_player = None
            if gk_candidates:
                gk_candidates_sorted = sorted(gk_candidates, key=lambda x: compute_player_rating(x), reverse=True)
                gk_player = gk_candidates_sorted[0]
            elif available:
                # Fallback only if NO registered GK is available
                sorted_all = sorted(available, key=lambda x: compute_player_rating(x), reverse=True)
                gk_player = sorted_all[0]
                field_candidates = [u for u in available if u != gk_player]

            gk_name = f"{active_users[gk_player]['full_name']} (@{gk_player})" if gk_player else "No GK Assigned"
            
            # 2. Select top field players by rating
            field_sorted = sorted(field_candidates, key=lambda x: compute_player_rating(x), reverse=True)
            starters_field = field_sorted[:target_count]
            subs = field_sorted[target_count:]
            
            # 3. SMART POSITION MATCHING LOGIC
            # Defined pitch slot categories
            slot_categories = {
                "DEF": ["LB", "LCB", "RCB", "RB"],
                "MID": ["LCM", "CM", "RCM"],
                "ATT": ["LS", "RS"]
            }
            
            assigned_positions = {}
            unassigned_starters = []

            # Step 3A: Map players with exact/matching preferred positions first
            for p_uname in starters_field:
                p_pos = active_users[p_uname].get("position", "CM").upper()
                display_str = f"{active_users[p_uname]['full_name']} ({compute_player_rating(p_uname)})"
                
                # Check direct slot availability
                placed = False
                for cat, slots in slot_categories.items():
                    if p_pos in slots or p_pos in cat:
                        for s in slots:
                            if s not in assigned_positions:
                                assigned_positions[s] = display_str
                                placed = True
                                break
                    if placed:
                        break
                
                if not placed:
                    unassigned_starters.append((p_uname, display_str))

            # Step 3B: Fill remaining open slots with unassigned players
            all_slots = ["LB", "LCB", "RCB", "RB", "LCM", "CM", "RCM", "LS", "RS"]
            vacant_slots = [s for s in all_slots if s not in assigned_positions]
            
            for idx, (p_uname, display_str) in enumerate(unassigned_starters):
                if idx < len(vacant_slots):
                    assigned_positions[vacant_slots[idx]] = display_str
                else:
                    assigned_positions[f"EXTRA_{idx+1}"] = display_str
            
            chosen_formation = custom_formation if fmt_mode == "✍️ Manual Custom" else "4-3-2 Tactical Setup"

            # Display Formation Details
            st.markdown(f"### 🏆 Starting Lineup & Tactical Formation")
            st.info(f"🎯 **Tactical Formation:** `{chosen_formation}`")
            st.success(f"🧤 **Main Goalkeeper (GK):** {gk_name}")
            
            # ASCII Visual Box Display
            st.markdown("#### 🏟️ Pitch Position Diagram:")
            visual_box_str = generate_visual_formation_box(gk_name, assigned_positions)
            st.code(visual_box_str, language="text")
            
            notice_text = f"### ⚽ Match Squad Announcement ({datetime.date.today()})\n"
            notice_text += f"**Formation:** {chosen_formation}\n"
            notice_text += f"**🧤 GK:** {gk_name}\n\n"
            notice_text += f"**🏟️ Starting Field Lineup ({len(starters_field)} Players):**\n"
            
            for slot, p_det in assigned_positions.items():
                line = f"* **[{slot}]**: {p_det}"
                st.markdown(line)
                notice_text += f"{line}\n"
                
            # 4. Timed Substitutions Schedule (10:15 AM - 11:00 AM)
            st.markdown("---")
            st.markdown("### 🔄 Substitution Plan & Time Schedule (10:15 AM - 11:00 AM)")
            
            notice_text += f"\n**🔄 Substitution Schedule (10:15 - 11:00 AM without break):**\n"
            
            if subs:
                start_time = datetime.datetime.strptime("10:15", "%H:%M")
                match_duration = 45 # Minutes
                interval = match_duration // (len(subs) + 1)
                
                starters_to_replace = list(reversed(starters_field))
                
                for idx, sub_p in enumerate(subs):
                    sub_time = start_time + datetime.timedelta(minutes=interval * (idx + 1))
                    time_str = sub_time.strftime("%I:%M %p")
                    
                    sub_user = active_users[sub_p]
                    replaced_p = starters_to_replace[idx % len(starters_to_replace)]
                    replaced_user = active_users[replaced_p]
                    
                    sub_msg = (
                        f"⏰ **সময় {time_str}:** "
                        f"মাঠে নামবেন ➡️ **{sub_user['full_name']}** (`@{sub_p}` | Rating: {compute_player_rating(sub_p)}) "
                        f"| মাঠ ছাড়বেন ⬅️ **{replaced_user['full_name']}** (`@{replaced_p}`)"
                    )
                    st.warning(sub_msg)
                    notice_text += f"* {sub_msg}\n"
            else:
                st.info("ℹ️ No substitute players available. Starting XI will play full match.")
                notice_text += "* No substitutes available.\n"
            
            # Notice Board Publish
            st.session_state.notice_board.append({
                "id": len(st.session_state.notice_board) + 1,
                "author": "Football AI Generator",
                "title": f"Match Squad Lineup & Sub Schedule ({datetime.date.today()})",
                "content": notice_text,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "comments": []
            })
            
            st.session_state.match_settings["asmb_player_count"] = target_count
            save_data_to_file()
            st.success("✅ Match Squad and Substitution Schedule published to Notice Board!")

    # ---------------------------------------------------------
    # MODE 2: PRACTICE DAY SPLIT (TWO BALANCED TEAMS)
    # ---------------------------------------------------------
    elif day_sel == "Practice Day Split (Mon-Thu)":
        st.subheader("🏃 Practice Match Balanced Team Generator")
        
        active_users = get_active_unblocked_users()
        
        if curr_user["role"] in ["Superadmin", "Admin"]:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p_fmt_mode = st.radio("📐 Practice Formation:", ["🤖 AI Auto-Select", "✍️ Manual Custom"], horizontal=True, key="p_fmt_radio")
            with col_p2:
                if p_fmt_mode == "✍️ Manual Custom":
                    practice_formation = st.text_input("Enter Formation:", value="Balanced Practice Formation", key="input_practice_fmt")
                else:
                    practice_formation = "AI Adaptive Balanced Formation"

            if st.button("Generate & Publish Balanced Teams", key="btn_gen_practice", type="primary"):
                available = [
                    u for u in active_users.keys() 
                    if u not in st.session_state.injured_players 
                    and st.session_state.player_stats.get(u, {}).get("attendance") != "Absent"
                ]
                
                if len(available) < 2:
                    st.error("Need at least 2 active players to generate practice teams.")
                else:
                    sorted_players = sorted(available, key=lambda x: compute_player_rating(x), reverse=True)
                    
                    team_tp = []
                    team_el = []
                    
                    # Snake Draft Allocation Logic for equal team strength
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
                    
                    st.session_state["last_practice_teams"] = {
                        "team_tp": team_tp,
                        "team_el": team_el,
                        "avg_tp": avg_tp,
                        "avg_el": avg_el,
                        "formation": practice_formation
                    }
                    
                    notice_text = f"### 🏃 Practice Match Teams - {datetime.date.today()}\n"
                    notice_text += f"**Formation:** {practice_formation}\n\n"
                    
                    notice_text += f"**🐯 🐅 Tigers & Panthers (Avg Rating: {avg_tp}):**\n"
                    for idx, p in enumerate(team_tp, 1):
                        u = active_users[p]
                        notice_text += f"{idx}. {u['full_name']} (@{p}) - Pos: {u.get('position', 'N/A')} ({compute_player_rating(p)})\n"
                        
                    notice_text += f"\n**🦅 🦁 Eagles & Lions (Avg Rating: {avg_el}):**\n"
                    for idx, p in enumerate(team_el, 1):
                        u = active_users[p]
                        notice_text += f"{idx}. {u['full_name']} (@{p}) - Pos: {u.get('position', 'N/A')} ({compute_player_rating(p)})\n"
                    
                    st.session_state.notice_board.append({
                        "id": len(st.session_state.notice_board) + 1,
                        "author": "Football AI Generator",
                        "title": f"Practice Match Split ({len(available)} Players)",
                        "content": notice_text,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "comments": []
                    })
                    
                    save_data_to_file()
                    st.success("✅ Balanced practice teams generated & published to Notice Board!")
                    st.rerun()

            if "last_practice_teams" in st.session_state:
                p_data = st.session_state["last_practice_teams"]
                col_t1, col_t2 = st.columns(2)
                
                with col_t1:
                    st.markdown(f"### 🐯 🐅 Tigers & Panthers ({len(p_data['team_tp'])} Players)")
                    st.caption(f"Average Team Rating: **{p_data['avg_tp']}**")
                    for idx, p in enumerate(p_data['team_tp'], 1):
                        u = active_users.get(p, {})
                        r = compute_player_rating(p)
                        st.markdown(f"{idx}. **{u.get('full_name', p)}** (`@{p}`) - Pos: `{u.get('position', 'N/A')}` | Rating: **{r}**")
                        
                with col_t2:
                    st.markdown(f"### 🦅 🦁 Eagles & Lions ({len(p_data['team_el'])} Players)")
                    st.caption(f"Average Team Rating: **{p_data['avg_el']}**")
                    for idx, p in enumerate(p_data['team_el'], 1):
                        u = active_users.get(p, {})
                        r = compute_player_rating(p)
                        st.markdown(f"{idx}. **{u.get('full_name', p)}** (`@{p}`) - Pos: `{u.get('position', 'N/A')}` | Rating: **{r}**")

        else:
            st.info("ℹ️ Practice teams can only be generated by Superadmin/Admin.")
            
# ==========================================
# 10. RATINGS & RATING GUIDE
# ==========================================
elif nav_choice == "⭐ Teammate Ratings & Guide":
    st.header("⭐ Rate Teammates & Performance Guide")
    
    # 📘 Rating Guide Panel
    with st.expander("📘 Rating Guide Panel (Click to expand)", expanded=False):
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
    
    st.markdown("---")
    st.subheader("🗳️ Submit Teammate Rating")
    
    # Get active users excluding current user
    active_users = get_active_unblocked_users()
    targets = [u for u in active_users.keys() if u != curr_username]
    
    if not targets:
        st.info("No other active teammates available to rate.")
    else:
        # User Selection Outside Form to Dynamically Load Previous Rating
        target = st.selectbox(
            "Select Teammate:", 
            options=targets,
            format_func=lambda x: f"{active_users[x].get('full_name', x)} (@{x})"
        )
        
        # Load previous rating data
        prev = st.session_state.ratings_db.get((curr_username, target), {"rating": 6.0, "fouls": 0})
        
        # Form to handle submit cleanly
        with st.form(key=f"rating_form_{target}"):
            new_r = st.slider("Rating (0.0 - 10.0)", 0.0, 10.0, float(prev.get("rating", 6.0)), 0.1)
            new_f = st.number_input("Fouls (0 - 10)", 0, 10, int(prev.get("fouls", 0)), 1)
            
            submit_btn = st.form_submit_button("💾 Save/Correct Rating", type="primary")
            
            if submit_btn:
                st.session_state.ratings_db[(curr_username, target)] = {
                    "rating": round(new_r, 2), 
                    "fouls": new_f
                }
                save_data_to_file()
                st.success(f"✅ Rating for {active_users[target].get('full_name', target)} saved successfully!")
                st.rerun()
# ==========================================
# 11. MANAGE PROFILE (EASY PIN & PASS CHANGE - SAFE & FIXED)
# ==========================================
elif nav_choice == "⚙️ Manage Profile":
    st.header("⚙️ Edit Profile")
    st.warning("🔒 Position can only be changed by Admin/Superadmin.")
    
    # -------------------------------------------------------------
    # 👤 SECTION 1: PERSONAL DETAILS
    # -------------------------------------------------------------
    st.subheader("👤 Personal Details")
    new_fn = st.text_input("Full Name:", value=curr_user.get("full_name", ""))
    new_jn = st.number_input("Jersey Number:", 1, 99, int(curr_user.get("jersey_num", 1)))
    new_jname = st.text_input("Jersey Player Name:", value=curr_user.get("jersey_name", ""))
    new_pai = st.text_input("Personal AI Name:", value=curr_user.get("personal_ai_name", ""))
    
    pic = st.file_uploader("Update Profile Photo:", type=["jpg", "png", "jpeg"])
    
    if st.button("Save Profile Updates", key="btn_prof_save", type="primary"):
        curr_user["full_name"] = new_fn
        curr_user["jersey_num"] = new_jn
        curr_user["jersey_name"] = new_jname
        curr_user["personal_ai_name"] = new_pai
        
        if pic:
            curr_user["photo_b64"] = base64.b64encode(pic.read()).decode('utf-8')
            
        # Safe session storage sync to prevent KeyError
        uname = curr_user.get("username")
        if uname and "users" in st.session_state and uname in st.session_state.users:
            st.session_state.users[uname] = curr_user
            
        save_data_to_file()
        st.success("✅ Profile updated successfully!")
        st.rerun()

    st.divider()

    # -------------------------------------------------------------
    # 🔑 SECTION 2: EASY PASSWORD & PIN CHANGE
    # -------------------------------------------------------------
    st.subheader("🔑 Security & Account Settings")
    
    with st.expander("🛡️ Change Password / Security PIN", expanded=True):
        new_pass_input = st.text_input("Set New Password (নতুন পাসওয়ার্ড):", value=curr_user.get("password", ""), type="password")
        new_pin_input = st.text_input("Set Security PIN (যেকোনো পিন):", value=curr_user.get("pin", ""))
        
        if st.button("💾 Save PIN & Password", key="btn_save_pin_pass", type="primary"):
            updated = False
            uname = curr_user.get("username")
            
            # 1. পাসওয়ার্ড নিরাপদ আপডেট
            if new_pass_input.strip():
                curr_user["password"] = new_pass_input.strip()
                if uname and "users" in st.session_state and uname in st.session_state.users:
                    st.session_state.users[uname]["password"] = new_pass_input.strip()
                updated = True
            
            # 2. সিকিউরিটি পিন নিরাপদ আপডেট
            if new_pin_input.strip():
                curr_user["pin"] = new_pin_input.strip()
                if uname and "users" in st.session_state and uname in st.session_state.users:
                    st.session_state.users[uname]["pin"] = new_pin_input.strip()
                updated = True

            if updated:
                save_data_to_file()
                st.success("✅ Password & PIN updated successfully!")
                st.rerun()
            else:
                st.error("Please enter a valid Password or PIN.")

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
# 13. FOOTBALL AI (PUBLIC) WITH GEMINI INTEGRATION
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
            if re.search(r'http[s]?://|www\.', text) or "link" in text.lower() or ("feature" in text.lower() and "app" in text.lower()):
                resp = "নিরাপত্তাজনিত কারণে অ্যাপের কোনো লিংক বা অভ্যন্তরীণ ফিচার ও আর্কিটেকচার বিশ্লেষণ বা প্রকাশ করা নিষিদ্ধ।"
            elif any(k in text.lower() for k in ["weather", "recipe", "math", "code", "movie", "song"]):
                resp = f"এটি ফুটবলের বাইরে প্রশ্ন। প্রশ্নটি স্বয়ংক্রিয়ভাবে আপনার **Personal AI ({curr_user['personal_ai_name']})** পেজে রিডাইরেক্ট করা হলো।"
                st.session_state.personal_ai_chats.setdefault(curr_username, []).append({
                    "prompt": text,
                    "response": f"হ্যালো {curr_user['full_name']}! আপনার প্রশ্নটির উত্তর নিয়ে আমি কাজ করছি।",
                    "timestamp": datetime.datetime.now().strftime("%H:%M")
                })
            else:
                # --- GEMINI INTEGRATION HERE ---
                try:
                    # Secrets থেকে API Key গ্রহণ ও কনফিগারেশন
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    
                    # কাস্টম ট্যাকটিক্যাল প্রম্পট
                    tactical_prompt = (
                        "তুমি একজন বিশেষজ্ঞ ফুটবল ট্যাকটিশিয়ান এবং কোচ। "
                        "শুধুমাত্র ফুটবল ট্যাকটিক্স, স্ট্র্যাটেজি, পজিশন বিশ্লেষণ ও ফর্মেশন সংক্রান্ত "
                        "সংক্ষিপ্ত, স্পষ্ট ও কার্যকর উত্তর দাও। "
                        f"ব্যবহারকারীর প্রশ্ন: {text}"
                    )
                    
                    with st.spinner("AI ট্যাকটিক্স বিশ্লেষণ করছে..."):
                        response = model.generate_content(tactical_prompt)
                        resp = response.text
                except Exception as e:
                    # API তে কোনো সমস্যা হলে ব্যাকআপ স্ট্যাটিক উত্তর
                    resp = f"'{text}' সম্পর্কিত ট্যাকটিক্যাল পরামর্শ: ফর্মেশন কমপ্যাক্ট রাখুন, হাই-প্রেসিং করুন এবং উইং দিয়ে দ্রুত কাউন্টার অ্যাটাকে যান।"
                
            st.session_state.football_ai_chats.append({
                "sender": curr_user["full_name"],
                "prompt": text,
                "response": resp,
                "timestamp": datetime.datetime.now().strftime("%H:%M")
            })
            save_data_to_file()
            st.rerun()

# ==========================================
# 14. PERSONAL AI & MOTM VOTING WITH GEMINI INTEGRATION
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
            
            # Anti-link and Anti-Scraping Feature
            if re.search(r'http[s]?://|www\.', text) or ("link" in text.lower() and "feature" in text.lower()):
                resp = "দুঃখিত, কোনো অ্যাপ লিংক থেকে তথ্য বা ফিচার বিশ্লেষণ করা আমার জন্য নিষিদ্ধ।"
            else:
                # --- GEMINI INTEGRATION HERE ---
                try:
                    # Secrets থেকে API Key কনফিগারেশন
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    
                    # পার্সোনাল অ্যাসিস্ট্যান্ট কনটেক্সট প্রম্পট
                    personal_prompt = (
                        f"তোমার নাম {pai_name}। তুমি {curr_user['full_name']}-এর একজন অত্যন্ত বিশ্বস্ত এবং সাহায্যকারী ব্যক্তিগত সহকারী (Personal AI Assistant)। "
                        "তোমার কাজ হলো যেকোনো সাধারণ প্রশ্ন, পড়াশোনা, টেকনোলজি, প্ল্যানিং কিংবা ফিটনেস সংক্রান্ত বিষয়ে সম্পূর্ণ বাংলা ভাষায় বন্ধুসুলভ ও বুদ্ধিমত্তার সাথে উত্তর দেওয়া। "
                        f"ব্যবহারকারীর প্রশ্ন: {text}"
                    )
                    
                    with st.spinner(f"{pai_name} উত্তর তৈরি করছে..."):
                        response = model.generate_content(personal_prompt)
                        resp = response.text
                except Exception as e:
                    # API তে কোনো সমস্যা হলে ব্যাকআপ স্ট্যাটিক উত্তর
                    resp = f"হ্যালো {curr_user['full_name']}! আপনার প্রশ্ন: '{text}'। বাংলা ভাষায় যেকোনো তথ্যে আমি সাহায্য করতে পারি।"
                
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
        
    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "🎨 Branding & Limit", 
        "👑 Roles & Password", 
        "🚫 Block System", 
        "📊 Match Stats & GK Saves", 
        "📋 Player Attendance", 
        "📢 Notice & Poll",
        "🧹 Master Reset"
    ])
    
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
        new_pos = st.selectbox("Assign Position:", ["GK", "CB", "LB", "RB", "RCM","LCM","CAM", "RW", "LW", "ST"])
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
                
        st.subheader("📜 Blocked Players List & Last Messages")
        blocked_found = False
        for bu, bd in st.session_state.users.items():
            if bd.get("status") == "Blocked":
                blocked_found = True
                st.error(f"🚨 **{bd['full_name']}** (`@{bu}`) - Reason: {bd.get('block_reason')}")
                
                # Fetch last message sent by blocked player
                user_msgs = [msg for msg in st.session_state.get("group_chat", []) if msg.get("sender") == bu]
                if user_msgs:
                    last_msg = user_msgs[-1]
                    st.info(f"💬 **Last Message:** \"{last_msg.get('text', '')}\" — *(Sent at {last_msg.get('timestamp', 'N/A')})*")
                else:
                    st.caption("💬 No messages found from this user.")
                st.divider()
                
        if not blocked_found:
            st.info("No blocked players currently.")

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
        st.subheader("📋 Daily Player Attendance Sheet")
        st.caption(f"📅 Date: **{datetime.date.today().strftime('%B %d, %Y')}**")
        
        active_users = get_active_unblocked_users()
        
        if not active_users:
            st.info("No active players available.")
        else:
            with st.form("admin_tab_attendance_form"):
                updated_attendance = {}
                
                h_c1, h_c2, h_c3 = st.columns([3, 2, 4])
                with h_c1:
                    st.markdown("**Player Name**")
                with h_c2:
                    st.markdown("**Position**")
                with h_c3:
                    st.markdown("**Attendance Status**")
                
                st.divider()
                
                for username, user_info in active_users.items():
                    col1, col2, col3 = st.columns([3, 2, 4])
                    
                    with col1:
                        st.markdown(f"**{user_info['full_name']}** (`@{username}`)")
                    with col2:
                        st.markdown(f"`{user_info.get('position', 'N/A')}`")
                    with col3:
                        current_status = st.session_state.player_stats.get(username, {}).get("attendance", "Present")
                        status_options = ["Present", "Absent", "Late", "Injured"]
                        default_idx = status_options.index(current_status) if current_status in status_options else 0
                        
                        selected_status = st.radio(
                            f"Att_{username}",
                            options=status_options,
                            index=default_idx,
                            key=f"tab_att_radio_{username}",
                            horizontal=True,
                            label_visibility="collapsed"
                        )
                        updated_attendance[username] = selected_status
                
                st.markdown("---")
                if st.form_submit_button("💾 Save Attendance Sheet", type="primary"):
                    for username, status in updated_attendance.items():
                        if username not in st.session_state.player_stats:
                            st.session_state.player_stats[username] = {}
                        st.session_state.player_stats[username]["attendance"] = status
                        
                        if status == "Injured":
                            if username not in st.session_state.injured_players:
                                st.session_state.injured_players.append(username)
                        else:
                            if username in st.session_state.injured_players:
                                st.session_state.injured_players.remove(username)
                    
                    save_data_to_file()
                    st.success("✅ Attendance updated successfully!")
                    st.rerun()

                    # ==========================================
                    # 📢 TAB 6: NOTICE & POLL GENERATOR (FIXED)
                    # ==========================================
                    with t6:
                        st.subheader("📌 Admin Announcement & Voting Tool")
                        
                        action_type = st.radio("Select Action:", ["Create Notice", "Create Poll"], horizontal=True, key="admin_notice_poll_radio")
                        
                        if action_type == "Create Notice":
                            with st.form("admin_create_notice_form"):
                                n_title = st.text_input("Notice Title:")
                                n_content = st.text_area("Notice Details:")
                                
                                if st.form_submit_button("📢 Publish Notice", type="primary"):
                                    if n_title.strip() and n_content.strip():
                                        if "notice_board" not in st.session_state:
                                            st.session_state.notice_board = []
                                            
                                        st.session_state.notice_board.append({
                                            "id": len(st.session_state.notice_board) + 1,
                                            "author": f"{curr_user['full_name']} ({curr_user['role']})",
                                            "title": n_title.strip(),
                                            "content": n_content.strip(),
                                            "is_poll": False,
                                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                            "comments": []
                                        })
                                        save_data_to_file()
                                        st.success("✅ Notice successfully published to Notice Board!")
                                        st.rerun()
                                    else:
                                        st.error("Please fill in both title and content.")
                    
                        elif action_type == "Create Poll":
                            with st.form("admin_create_poll_form"):
                                p_question = st.text_input("Poll Question / Title:")
                                p_options_raw = st.text_area("Options (Enter each option on a new line):", value="Yes\nNo")
                                
                                if st.form_submit_button("📊 Publish Poll", type="primary"):
                                    options = [opt.strip() for opt in p_options_raw.split("\n") if opt.strip()]
                                    if p_question.strip() and len(options) >= 2:
                                        if "notice_board" not in st.session_state:
                                            st.session_state.notice_board = []
                                            
                                        st.session_state.notice_board.append({
                                            "id": len(st.session_state.notice_board) + 1,
                                            "author": f"{curr_user['full_name']} ({curr_user['role']})",
                                            "title": f"📊 Poll: {p_question.strip()}",
                                            "content": p_question.strip(),
                                            "is_poll": True,
                                            "poll_options": options,
                                            "poll_votes": {},  # {username: selected_option}
                                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                            "comments": []
                                        })
                                        save_data_to_file()
                                        st.success("✅ Poll successfully published to Notice Board!")
                                        st.rerun()
                                    else:
                                        st.error("Please provide a question and at least 2 options.")
                    
                    with t7:
                        if curr_user["role"] == "Superadmin":
                            if st.button("🔥 EXECUTE MASTER RESET", key="btn_mr"):
                                st.session_state.group_chat = []
                                st.session_state.football_ai_chats = []
                                st.session_state.personal_ai_chats = {}
                                save_data_to_file()
                                st.success("Master Reset completed!")
                                st.rerun()    
