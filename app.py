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

# ==========================================
# PERMANENT MEMORY FILE ENGINE (JSON STORAGE)
# ==========================================
DB_FILE = "asmb_football_club_data.json"

def load_data_from_file():
    """ফাইল থেকে সেভ থাকা ডাটা অ্যাপে নিয়ে আসে"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def save_data_to_file():
    """মেমোরি সেভ রাখতে সব ডাটা ফাইলে রাইট করে"""
    data_to_save = {
        "app_settings": {
            "app_name": st.session_state.app_settings.get("app_name", "ASMB United Football Club"),
            "bg_color": st.session_state.app_settings.get("bg_color", "#0e1117"),
            "max_register_limit": st.session_state.app_settings.get("max_register_limit", 50),
            "club_photo_b64": st.session_state.app_settings.get("club_photo_b64", None)
        },
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
    with open(DB_FILE, "w") as f:
        json.dump(data_to_save, f, indent=4)

# ==========================================
# 0. PAGE CONFIG & PERSISTENT SESSION STATE
# ==========================================
st.set_page_config(
    page_title="ASMB United FC",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_db():
    """Initialize global database tables and restore permanent memory."""
    if "db_initialized" not in st.session_state:
        saved_data = load_data_from_file()
        
        if saved_data:
            st.session_state.app_settings = saved_data.get("app_settings", {
                "app_name": "ASMB United Football Club",
                "bg_color": "#0e1117",
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
                "bg_color": "#0e1117",
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
# 1. DYNAMIC CSS & BRANDING OVERRIDES
# ==========================================

def execute_daily_ai_background_script():
    bright_colors = [
        "#00D2FF", "#FF5E7E", "#FFD166", "#06D6A0", 
        "#A29BFE", "#FF9F43", "#00CECB"
    ]
    today_index = datetime.datetime.now().day % len(bright_colors)
    if "custom_bg_set" not in st.session_state:
        st.session_state.app_settings["bg_color"] = bright_colors[today_index]

execute_daily_ai_background_script()

def get_daily_club_title_color():
    title_colors = ["#FF1493", "#00FF7F", "#FF4500", "#FFD700", "#1E90FF", "#9370DB", "#FF00FF"]
    return title_colors[datetime.datetime.now().day % len(title_colors)]

bg_color = st.session_state.app_settings.get("bg_color", "#00D2FF")
title_color = get_daily_club_title_color()

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
        color: {title_color} !important;
        font-size: 2.2rem !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}
    div.stButton > button {{
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 2px solid #000000 !important;
        border-radius: 6px !important;
        font-weight: bold !important;
    }}
    div.stButton > button:hover {{
        background-color: #222222 !important;
        color: #FFFFFF !important;
        border-color: #000000 !important;
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. HELPER CALCULATORS & BUSINESS LOGIC
# ==========================================
def compute_player_rating(username):
    user_ratings = [data["rating"] for (rater, target), data in st.session_state.ratings_db.items() if target == username]
    user_fouls = [data["fouls"] for (rater, target), data in st.session_state.ratings_db.items() if target == username]
    
    base_rating = (sum(user_ratings) / len(user_ratings)) if user_ratings else 6.0
    avg_fouls = (sum(user_fouls) / len(user_fouls)) if user_fouls else 0.0
    
    stats = st.session_state.player_stats.get(username, {"goals": 0, "assists": 0, "conceded_penalty": 0.0, "attendance": "Present", "rating_penalty": 0.0, "gk_saves": 0})
    
    goals_bonus = stats["goals"] * 0.5
    assists_bonus = stats["assists"] * 0.3
    gk_saves_bonus = stats.get("gk_saves", 0) * 0.2
    foul_penalty = avg_fouls * 0.2
    
    net_rating = base_rating + goals_bonus + assists_bonus + gk_saves_bonus - foul_penalty - stats["conceded_penalty"] - stats["rating_penalty"]
    
    if stats.get("attendance") == "Absent":
        net_rating -= 1.0
        
    return max(0.0, min(10.0, round(net_rating, 2)))

def get_highest_motm_player():
    if not st.session_state.motm_votes:
        return None
    votes_list = list(st.session_state.motm_votes.values())
    if not votes_list:
        return None
    winner = max(set(votes_list), key=votes_list.count)
    return winner

def update_star_players():
    top_motm_player = get_highest_motm_player()
    for uname, udata in st.session_state.users.items():
        if udata["status"] == "Blocked":
            udata["is_star"] = False
            continue
            
        rating = compute_player_rating(uname)
        if rating > 7.5 or (top_motm_player and uname == top_motm_player):
            udata["is_star"] = True
        else:
            udata["is_star"] = False

def audit_block_reason(reason):
    invalid_keywords = ["test", "joke", "nothing", "fun", "no reason", "random", "asdf", "lol"]
    clean_reason = reason.strip().lower()
    if len(clean_reason) < 5 or any(k in clean_reason for k in invalid_keywords):
        return False
    return True

def get_active_unblocked_users():
    return {u: data for u, data in st.session_state.users.items() if data.get("status") == "Active"}

# ==========================================
# 3. AUTHENTICATION & LOGIN / REGISTRATION
# ==========================================
if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

def login_register_surface():
    st.markdown(f'<h1 class="daily-club-title">⚽ {st.session_state.app_settings["app_name"]}</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔒 Member Login", "📝 New Registration"])
    
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
            st.error("⛔ Registration limit reached! New registrations are currently paused by Admin.")
            return

        reg_username = st.text_input("Username (Unique Key)*", key="reg_uname").strip()
        reg_password = st.text_input("Password*", type="password", key="reg_pass")
        reg_sec_key = st.text_input("Set Forget Password Security Key*", key="reg_sec_key", help="Required to reset password if forgotten.")
        reg_full_name = st.text_input("Full Name*", key="reg_fullname")
        reg_jersey_num = st.number_input("Jersey Number*", min_value=1, max_value=99, step=1)
        reg_jersey_name = st.text_input("Jersey Player Name*", key="reg_jname")
        
        reg_photo_file = st.file_uploader("Photo Upload (Optional)", type=["jpg", "png", "jpeg"])
        reg_photo_b64 = None
        if reg_photo_file:
            import base64
            reg_photo_b64 = base64.b64encode(reg_photo_file.read()).decode('utf-8')

        reg_personal_ai = st.text_input("Personal AI Custom Name*", value="Jarvis", key="reg_pai")
        
        is_first_user = len(st.session_state.users) == 0
        if is_first_user:
            st.info("ℹ️ You are the first registered user. You will automatically be granted Superadmin (S.A) privileges!")
            reg_position = st.selectbox("Assign Initial Position (Superadmin Exclusive)", ["GK","CB", "LB", "RB", "CM", "CAM", "RW", "LW", "ST"])
        else:
            st.warning("🔒 Position field is strictly disabled during registration. An Admin/Superadmin will assign your position post-registration.")
            reg_position = "Unassigned"

        if st.button("Register Account", key="btn_reg"):
            if not reg_username or not reg_password or not reg_full_name or not reg_jersey_name or not reg_personal_ai or not reg_sec_key:
                st.error("Please fill in all mandatory fields including Security Key.")
                return
            
            if reg_username in st.session_state.users:
                st.error("⚠️ Username already exists!")
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
            st.success("Registration successful! Redirecting to login...")
            st.rerun()

if not st.session_state.authenticated_user:
    login_register_surface()
    st.stop()

# ==========================================
# FORGET / LEGACY USER SECURITY KEY POP-UP
# ==========================================
curr_username = st.session_state.authenticated_user
curr_user = st.session_state.users[curr_username]

if "sec_key" not in curr_user or not curr_user["sec_key"]:
    st.warning("🔑 **Security Update Required:** Security Key সেট করা নেই। নিরাপত্তা ব্যবস্থার অংশ হিসেবে আপনার গোপন সিকিউরিটি কী (Forget Password Key) সেট করুন।")
    legacy_key = st.text_input("Enter your new Security Key:", type="password", key="legacy_sec_key_input")
    if st.button("Save Security Key", key="btn_save_legacy_key"):
        if legacy_key.strip():
            curr_user["sec_key"] = legacy_key.strip()
            save_data_to_file()
            st.success("Security Key saved successfully!")
            st.rerun()
        else:
            st.error("Please enter a valid key.")
    st.stop()

# ==========================================
# MATCHDAY PRE-POLL DIALOG (FRIDAY/SATURDAY)
# ==========================================
if curr_user["status"] == "Active" and curr_username not in st.session_state.match_availability_poll:
    st.info("📅 **Matchday Availability Poll:** আগামীকালের (Matchday) খেলায় আপনি কি উপস্থিত থাকবেন?")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("✅ Yes, I will attend", key="poll_yes"):
            st.session_state.match_availability_poll[curr_username] = "Yes"
            st.session_state.player_stats[curr_username]["attendance"] = "Present"
            save_data_to_file()
            st.rerun()
    with col_p2:
        if st.button("❌ No, I cannot attend", key="poll_no"):
            st.session_state.match_availability_poll[curr_username] = "No"
            st.session_state.player_stats[curr_username]["attendance"] = "Absent"
            save_data_to_file()
            st.rerun()

# ==========================================
# 4. AUTHENTICATED SESSION SETUP & SIDEBAR
# ==========================================
update_star_players()

st.sidebar.markdown(f'<h2 class="daily-club-title">{st.session_state.app_settings["app_name"]}</h2>', unsafe_allow_html=True)
st.sidebar.markdown(f"**Logged in as:** {curr_user['full_name']} (`@{curr_username}`)")
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
        "⭐ Teammate Ratings & Fouls",
        "⚙️ Manage Profile",
        "💬 Club House Group Chat",
        "🤖 Football AI (Public)",
        "👤 Personal AI (Private)"
    ]
    if curr_user["role"] in ["Superadmin", "Admin"]:
        options.append("⚙️ Admin Control Panel")
        
    nav_choice = st.sidebar.radio("Navigation Menu", options)

# ==========================================
# 5. BLOCKED USER LOCKED DOWN SURFACE
# ==========================================
if curr_user["status"] == "Blocked":
    st.error("🚨 Your account has been blocked by the Management due to policy/discipline rules.")
    st.info(f"**Reason for Block:** {curr_user.get('block_reason', 'No reason provided')}")
    
    st.subheader("🚩 Report / Flag User for Fair-Play Violation & Appeal Block")
    st.write("You are permitted to submit **one final appeal message** to the Superadmin.")
    
    if curr_username in st.session_state.block_appeals:
        st.warning(f"Your submitted appeal: \"{st.session_state.block_appeals[curr_username]}\"")
        st.info("Your appeal has been received and is under review by the Superadmin.")
    else:
        appeal_msg = st.text_area("Type your appeal / dispute message here:")
        if st.button("Submit Final Appeal", key="btn_submit_appeal"):
            if appeal_msg.strip():
                st.session_state.block_appeals[curr_username] = appeal_msg.strip()
                save_data_to_file()
                st.success("Your appeal message has been submitted to the Superadmin.")
                st.rerun()
            else:
                st.error("Please enter a valid message before submitting.")
    st.stop()

# ==========================================
# 6. FEATURE MODULE: NOTICE BOARD & NEWS
# ==========================================
if nav_choice == "📌 Notice Board & News":
    st.header("📌 Official Notice Board & Communications")
    
    if not st.session_state.notice_board:
        st.info("No notices posted yet.")
    else:
        for notice in reversed(st.session_state.notice_board):
            with st.expander(f"[{notice['type']}] {notice['title']} - {notice['timestamp']} (By: {notice['author']})", expanded=True):
                st.markdown(notice['content'])

# ==========================================
# 7. FEATURE MODULE: PLAYER DIRECTORY & ROSTERS
# ==========================================
elif nav_choice == "👥 Player Directory & Roster":
    st.header("👥 Public Player Directory & Specialized Rosters")
    
    tab_dir, tab_star, tab_inj = st.tabs(["📋 Public Player Directory", "⭐ Star Players List", "🏥 Injured Players List"])
    
    active_users = get_active_unblocked_users()
    
    with tab_dir:
        st.subheader("Registered Active Club Members")
        dir_data = []
        for uname, udata in active_users.items():
            dir_data.append({
                "Username": uname,
                "Full Name": udata["full_name"],
                "Jersey #": udata["jersey_num"],
                "Jersey Name": udata["jersey_name"],
                "Position": udata["position"],
                "Role": udata["role"],
                "Rating": compute_player_rating(uname)
            })
        st.dataframe(pd.DataFrame(dir_data), use_container_width=True)

    with tab_star:
        st.subheader("⭐ Designated Star Players (> 7.5 Rating or MOTM Winner)")
        star_players = [u for u, udata in active_users.items() if udata.get("is_star")]
        if not star_players:
            st.info("No star players designated at this moment.")
        else:
            for sp in star_players:
                u = active_users[sp]
                r = compute_player_rating(sp)
                st.success(f"🌟 **{u['full_name']}** (`@{sp}`) - Position: {u['position']} | Rating: **{r} / 10.0**")

    with tab_inj:
        st.subheader("🏥 Injured Player Roster")
        if not st.session_state.injured_players:
            st.info("No injured players currently logged.")
        else:
            for ip in st.session_state.injured_players:
                if ip in active_users:
                    u = active_users[ip]
                    st.warning(f"🩹 **{u['full_name']}** (`@{ip}`) - Position: {u['position']}")

# ==========================================
# GALLERY MODULE: MEMBER PHOTO GALLERY
# ==========================================
elif nav_choice == "🖼️ Member Photo Gallery":
    st.header("🖼️ Member Photo Gallery")
    active_users = get_active_unblocked_users()
    photo_users = [u for u, data in active_users.items() if data.get("photo_b64")]
    
    if not photo_users:
        st.info("এখনো কোনো প্লেয়ার প্রোফাইল ছবি আপলোড করেনি।")
    else:
        cols = st.columns(3)
        import base64
        for idx, u in enumerate(photo_users):
            udata = active_users[u]
            img_bytes = base64.b64decode(udata["photo_b64"])
            image = Image.open(io.BytesIO(img_bytes))
            with cols[idx % 3]:
                st.image(image, use_container_width=True)
                st.caption(f"👤 **{udata['full_name']}** (@{u})")

# ==========================================
# 8. FEATURE MODULE: SQUAD GENERATION & TACTICS
# ==========================================
elif nav_choice == "⚽ Squad Generation & Tactics":
    st.header("⚽ Football AI Tactical Engine & Squad Output")
    
    if curr_user["role"] not in ["Superadmin", "Admin"]:
        st.warning("🔒 স্কোয়াড তৈরির ক্ষমতা শুধুমাত্র Superadmin এবং Admin-দের রয়েছে। নিচে লেটেস্ট স্কোয়াড দেওয়া হলো:")
    
    day_selection = st.selectbox("Select Operational Day Simulation", ["Saturday (Match Squad Generation)", "Practice Day (Mon-Thu Team Split)"])
    
    if day_selection == "Saturday (Match Squad Generation)":
        target_count = st.session_state.match_settings.get("asmb_player_count", 11)
        st.info(f"📋 **Configured Squad Size:** Management selected **{target_count} Players** for this squad.")
        
        can_generate = curr_user["role"] in ["Superadmin", "Admin"]
        
        if can_generate and st.button("Generate Match Squad", key="btn_gen_squad"):
            active_users = get_active_unblocked_users()
            available_players = [u for u in active_users.keys() if u not in st.session_state.injured_players and st.session_state.player_stats.get(u, {}).get("attendance") != "Absent"]
            
            position_groups = {}
            for u in available_players:
                pos = active_users[u]["position"]
                if pos not in position_groups:
                    position_groups[pos] = []
                position_groups[pos].append(u)
            
            selected_squad = []
            
            for pos, players in position_groups.items():
                sorted_p = sorted(players, key=lambda x: compute_player_rating(x), reverse=True)
                selected_squad.append(sorted_p[0])
            
            remaining_players = [u for u in available_players if u not in selected_squad]
            remaining_players = sorted(remaining_players, key=lambda x: compute_player_rating(x), reverse=True)
            
            needed = target_count - len(selected_squad)
            if needed > 0:
                selected_squad.extend(remaining_players[:needed])
                subs = remaining_players[needed:]
            else:
                subs = remaining_players
                
            starters = selected_squad[:target_count]
            
            st.markdown(f"### 🏆 Starting Lineup ({len(starters)} Players)")
            squad_notice_text = f"### ⚽ Dynamic Match Squad ({datetime.date.today()})\n\n**Starting Lineup ({len(starters)} Players):**\n"
            
            for idx, p in enumerate(starters, 1):
                r = compute_player_rating(p)
                u = active_users[p]
                line = f"{idx}. **{u['full_name']}** (`@{p}`) - Pos: {u['position']} | Rating: **{r}**"
                st.markdown(line)
                squad_notice_text += f"{line}\n"
                
            if subs:
                st.markdown(f"### 🔄 Substitutes Bench ({len(subs)} Players)")
                squad_notice_text += f"\n**Substitutes ({len(subs)} Players):**\n"
                for idx, p in enumerate(subs, 1):
                    r = compute_player_rating(p)
                    u = active_users[p]
                    line = f"Sub {idx}: **{u['full_name']}** (`@{p}`) - Pos: {u['position']} | Rating: **{r}**"
                    st.markdown(line)
                    squad_notice_text += f"{line}\n"
            
            formation = f"Adaptive Tactical Formation ({len(starters)}-a-side Optimized System)"
            squad_notice_text += f"\n**Tactical Formation:** {formation}"
            st.success(f"**Tactical Formation Engine:** {formation}")
            
            st.session_state.notice_board.append({
                "id": len(st.session_state.notice_board) + 1,
                "author": st.session_state.app_settings["app_name"] + " (Football AI)",
                "title": f"Official Match Squad ({target_count}-a-side) Announcement",
                "content": squad_notice_text,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "type": "Match Announcement"
            })
            save_data_to_file()
            st.info("📢 Match squad automatically published to Notice Board!")

    elif day_selection == "Practice Day (Mon-Thu Team Split)":
        if curr_user["role"] in ["Superadmin", "Admin"] and st.button("Generate Balanced Practice Teams", key="btn_gen_practice"):
            active_users = get_active_unblocked_users()
            available_players = [u for u in active_users.keys() if u not in st.session_state.injured_players]
            sorted_players = sorted(available_players, key=lambda u: compute_player_rating(u), reverse=True)
            
            team_a, team_b = [], []
            rate_a, rate_b = 0.0, 0.0
            
            for idx, p in enumerate(sorted_players):
                r = compute_player_rating(p)
                if idx % 2 == 0:
                    team_a.append((p, r))
                    rate_a += r
                else:
                    team_b.append((p, r))
                    rate_b += r
                    
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"### 🛡️⚡ Iron Strike (Aggregate Rating: {round(rate_a, 2)})")
                for p, r in team_a:
                    u = active_users[p]
                    st.write(f"• **{u['full_name']}** ({u['position']}) - Rating: **{r}**")
            with col2:
                st.markdown(f"### 🛡️🔥 Titan Shield (Aggregate Rating: {round(rate_b, 2)})")
                for p, r in team_b:
                    u = active_users[p]
                    st.write(f"• **{u['full_name']}** ({u['position']}) - Rating: **{r}**")

# ==========================================
# 9. FEATURE MODULE: TEAMMATE RATINGS & FOULS
# ==========================================
elif nav_choice == "⭐ Teammate Ratings & Fouls":
    st.header("⭐ Teammate Performance Rating & Foul Management")
    active_users = get_active_unblocked_users()
    target_users = [u for u in active_users.keys() if u != curr_username]
    
    if not target_users:
        st.warning("No other active members available to rate.")
    else:
        selected_target = st.selectbox("Select Teammate to Rate:", target_users)
        existing_entry = st.session_state.ratings_db.get((curr_username, selected_target), {"rating": 6.0, "fouls": 0})
        
        new_rating = st.slider("Performance Rating (0.0 - 10.0)", min_value=0.0, max_value=10.0, value=float(existing_entry["rating"]), step=0.1)
        new_fouls = st.number_input("Fouls / Infractions Count (0 - 10)", min_value=0, max_value=10, value=int(existing_entry["fouls"]), step=1)
        
        if st.button("Submit / Correct Rating", key="btn_save_rating"):
            st.session_state.ratings_db[(curr_username, selected_target)] = {
                "rating": round(new_rating, 2),
                "fouls": new_fouls
            }
            save_data_to_file()
            st.success(f"Successfully recorded rating for @{selected_target}!")

# ==========================================
# PROFILE MANAGEMENT MODULE
# ==========================================
elif nav_choice == "⚙️ Manage Profile":
    st.header("⚙️ Personal Profile Settings")
    new_fn = st.text_input("Full Name:", value=curr_user["full_name"])
    new_jn = st.number_input("Jersey Number:", min_value=1, max_value=99, value=int(curr_user["jersey_num"]))
    new_pai = st.text_input("Personal AI Name:", value=curr_user["personal_ai_name"])
    
    prof_photo = st.file_uploader("Update Profile Photo:", type=["jpg", "png", "jpeg"])
    
    if st.button("Update Profile Info", key="btn_update_profile"):
        curr_user["full_name"] = new_fn
        curr_user["jersey_num"] = new_jn
        curr_user["personal_ai_name"] = new_pai
        if prof_photo:
            import base64
            curr_user["photo_b64"] = base64.b64encode(prof_photo.read()).decode('utf-8')
        save_data_to_file()
        st.success("Profile updated successfully!")
        st.rerun()

# ==========================================
# 10. FEATURE MODULE: CLUB HOUSE GROUP CHAT
# ==========================================
elif nav_choice == "💬 Club House Group Chat":
    st.header("💬 ASMB United WhatsApp-Style Member Chat")
    
    chat_container = st.container()
    with chat_container:
        if not st.session_state.group_chat:
            st.info("No public messages yet. Start the conversation!")
        else:
            for msg in st.session_state.group_chat:
                st.markdown(f"**[{msg['timestamp']}] {msg['sender']}:** {msg['message']}")
                
    st.divider()
    msg_input = st.text_input("Type message...", key="group_msg_input")
    if st.button("Send Message", key="btn_send_chat"):
        if msg_input.strip():
            st.session_state.group_chat.append({
                "sender": curr_user["full_name"] + f" (@{curr_username})",
                "message": msg_input.strip(),
                "timestamp": datetime.datetime.now().strftime("%H:%M")
            })
            save_data_to_file()
            st.rerun()

# ==========================================
# 11. FEATURE MODULE: FOOTBALL AI (PUBLIC)
# ==========================================
elif nav_choice == "🤖 Football AI (Public)":
    st.header(f"🤖 Football AI - Public Assistant ({st.session_state.app_settings['app_name']})")
    st.caption("ℹ️ Public Assistant. Specialized STRICTLY in football tactics and strategies.")
    
    for chat in st.session_state.football_ai_chats:
        st.markdown(f"**👤 {chat['sender']} ({chat['timestamp']}):** {chat['prompt']}")
        st.markdown(f"🤖 **Football AI:** {chat['response']}")
        st.divider()
        
    prompt = st.text_input("Ask Football AI regarding tactics, counter-plays, or team advice:", key="f_ai_prompt")
    if st.button("Ask Football AI", key="btn_ask_fai"):
        if prompt.strip():
            p_text = prompt.strip()
            
            if re.search(r'http[s]?://|www\.', p_text) or "link" in p_text.lower() or "url" in p_text.lower():
                resp = "আমি আন্তরিকভাবে দুঃখিত। কোনো এক্সটার্নাল লিংক বিশ্লেষণ বা ব্রাউজ করার অনুমতি আমার নেই।"
            elif any(w in p_text.lower() for w in ["weather", "math", "code", "politics", "recipe", "movie", "song"]):
                resp = f"এই প্রশ্নটি ফুটবলের সাথে সম্পর্কিত নয়। আমি আপনার প্রশ্নটি স্বয়ংক্রিয়ভাবে আপনার **Personal AI ({curr_user['personal_ai_name']})** তে পাঠিয়ে দিয়েছি।"
                
                if curr_username not in st.session_state.personal_ai_chats:
                    st.session_state.personal_ai_chats[curr_username] = []
                st.session_state.personal_ai_chats[curr_username].append({
                    "prompt": p_text,
                    "response": f"হ্যালো {curr_user['full_name']}! আপনার ফুটবল AI থেকে রিডাইরেক্ট হওয়া প্রশ্নের উত্তর: আমি যেকোনো বিষয়ে আপনাকে সাহায্য করতে পারি। আপনার প্রশ্নটি নিয়ে আমি বিস্তারিত কাজ করছি!",
                    "timestamp": datetime.datetime.now().strftime("%H:%M")
                })
            else:
                resp = f"'{p_text}' সম্পর্কিত ফুটবল ট্যাকটিক্যাল বিশ্লেষণ: খেলায় জয়ী হতে সঠিক পজিশনিং ধরে রাখুন, হাই-প্রেসিং করুন এবং দলগত সমন্বয় নিশ্চিত করুন।"
            
            st.session_state.football_ai_chats.append({
                "sender": curr_user["full_name"],
                "prompt": p_text,
                "response": resp,
                "timestamp": datetime.datetime.now().strftime("%H:%M")
            })
            save_data_to_file()
            st.rerun()

# ==========================================
# 12. FEATURE MODULE: PERSONAL AI (PRIVATE)
# ==========================================
elif nav_choice == "👤 Personal AI (Private)":
    pai_name = curr_user["personal_ai_name"]
    st.header(f"👤 {pai_name} - Personal Assistant (Private)")
    st.caption("🔒 Strictly confidential. Ask ANY questions freely in Bengali.")
    
    if curr_username not in st.session_state.personal_ai_chats:
        st.session_state.personal_ai_chats[curr_username] = []
        
    user_p_chats = st.session_state.personal_ai_chats[curr_username]
    
    for chat in user_p_chats:
        st.markdown(f"**You ({chat['timestamp']}):** {chat['prompt']}")
        st.markdown(f"🤖 **{pai_name}:** {chat['response']}")
        st.divider()
        
    p_prompt = st.text_input(f"Chat with {pai_name}:", key="p_ai_prompt")
    if st.button("Send to Personal AI", key="btn_ask_pai"):
        if p_prompt.strip():
            p_text = p_prompt.strip()
            if re.search(r'http[s]?://|www\.', p_text) or "link" in p_text.lower() or "url" in p_text.lower():
                resp = "আমি অত্যন্ত দুঃখিত। কোনো এক্সটার্নাল লিংক বা ইউআরএল ফিচার পরীক্ষা করা আমার সিকিউরিটি প্রোটোকলে নিষিদ্ধ।"
            else:
                resp = f"হ্যালো {curr_user['full_name']}! আপনার প্রশ্ন: '{p_text}'। আমি আপনার সার্বিক সহায়তায় প্রস্তুত।"
            
            user_p_chats.append({
                "prompt": p_text,
                "response": resp,
                "timestamp": datetime.datetime.now().strftime("%H:%M")
            })
            save_data_to_file()
            st.rerun()
            
    st.divider()
    st.subheader("🗳️ Sunday Man of the Match (MOTM) Polling Interface")
    active_users = get_active_unblocked_users()
    motm_vote = st.selectbox("Cast your Sunday MOTM Vote:", list(active_users.keys()), key="motm_select")
    
    if st.button("Submit MOTM Vote", key="btn_vote_motm"):
        st.session_state.motm_votes[curr_username] = motm_vote
        save_data_to_file()
        st.success(f"Vote cast successfully for @{motm_vote}!")

# ==========================================
# 13. FEATURE MODULE: ADMIN CONTROL PANEL
# ==========================================
elif nav_choice == "⚙️ Admin Control Panel":
    st.header("⚙️ Administrative Control & Management Panel")
    
    if curr_user["role"] not in ["Superadmin", "Admin"]:
        st.error("⛔ Access Denied. Administrative privileges required.")
        st.stop()
        
    tab_branding, tab_roles, tab_block, tab_stats, tab_reset = st.tabs([
        "🎨 App Customization & Notices",
        "👑 Role, Position & Password",
        "🚫 Block System & Fair-Play Arbitration",
        "📊 GK Saves, Conceded & Stats",
        "🧹 Master Reset (S.A Only)"
    ])
    
    with tab_branding:
        st.subheader("Dynamically Configure Branding & Limits")
        new_app_name = st.text_input("Application / Club Name:", value=st.session_state.app_settings["app_name"])
        max_limit_input = st.number_input("Max Member Registration Limit:", min_value=1, max_value=200, value=int(st.session_state.app_settings.get("max_register_limit", 50)))
        
        club_pic = st.file_uploader("Upload Club Photo / Banner:", type=["jpg", "png", "jpeg"])
        if club_pic:
            import base64
            st.session_state.app_settings["club_photo_b64"] = base64.b64encode(club_pic.read()).decode('utf-8')
            
        if st.button("Update Branding Settings", key="btn_save_branding"):
            st.session_state.app_settings["app_name"] = new_app_name
            st.session_state.app_settings["max_register_limit"] = max_limit_input
            save_data_to_file()
            st.success("App branding and registration limits updated successfully!")
            st.rerun()

    with tab_roles:
        st.subheader("Manage User Positions, Password & Roles")
        target_role_user = st.selectbox("Select Target User:", list(st.session_state.users.keys()), key="role_target_select")
        
        col_pos, col_pass = st.columns(2)
        with col_pos:
            new_pos = st.selectbox("Position:", ["GK", "CB", "LB", "RB", "CM", "CAM", "RW", "LW", "ST"], key="select_new_pos")
            if st.button("Update Position", key="btn_update_pos"):
                st.session_state.users[target_role_user]["position"] = new_pos
                save_data_to_file()
                st.success(f"Updated position of @{target_role_user} to {new_pos}!")
                
        with col_pass:
            if curr_user["role"] == "Superadmin":
                st.markdown("### 🔑 Force Change User Password")
                forced_pass = st.text_input("Set New Password:", key="forced_pass_input")
                if st.button("Change Password", key="btn_force_pass"):
                    if forced_pass.strip():
                        st.session_state.users[target_role_user]["password"] = forced_pass.strip()
                        save_data_to_file()
                        st.success(f"Password changed successfully for @{target_role_user}!")

    with tab_block:
        st.subheader("Block / Unblock Users & Mandatory Fair-Play Arbitration")
        block_target = st.selectbox("Select Target User to Block/Unblock:", list(st.session_state.users.keys()), key="block_target_select")
        mandatory_reason = st.text_input("Mandatory Reason for Block:", key="block_reason_input")
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("Block Target User", key="btn_exec_block"):
                if not mandatory_reason.strip():
                    st.error("⛔ Every block action requires a mandatory Reason for Block entry!")
                else:
                    target_u = st.session_state.users[block_target]
                    target_u["status"] = "Blocked"
                    target_u["block_reason"] = mandatory_reason.strip()
                    save_data_to_file()
                    st.warning(f"User @{block_target} has been blocked.")
                    st.rerun()
                    
        with col_b2:
            if st.button("Unblock Target User", key="btn_exec_unblock"):
                st.session_state.users[block_target]["status"] = "Active"
                save_data_to_file()
                st.success(f"User @{block_target} unblocked successfully.")
                st.rerun()
                
        st.divider()
        st.subheader("📜 Blocked Players List")
        blocked_users = {u: data for u, data in st.session_state.users.items() if data.get("status") == "Blocked"}
        if not blocked_users:
            st.info("No blocked players found.")
        else:
            for bu, bdata in blocked_users.items():
                st.error(f"🚨 **{bdata['full_name']}** (`@{bu}`) - Reason: {bdata.get('block_reason', 'N/A')}")

    with tab_stats:
        st.subheader("Attendance, Performance Adjustments & GK Saves")
        
        col_att, col_gk = st.columns(2)
        with col_att:
            st.markdown("### Override Attendance")
            att_user = st.selectbox("Select Player for Attendance:", list(st.session_state.users.keys()), key="att_u_select")
            att_status = st.radio("Status:", ["Present", "Absent"], key="att_rad")
            if st.button("Save Attendance", key="btn_save_att"):
                st.session_state.player_stats[att_user]["attendance"] = att_status
                save_data_to_file()
                st.success(f"Attendance recorded for @{att_user}!")
                
        with col_gk:
            st.markdown("### 🧤 GK Saves Tracker")
            gk_users = [u for u, d in st.session_state.users.items() if d.get("position") == "GK"]
            if gk_users:
                sel_gk = st.selectbox("Select Goalkeeper:", gk_users, key="gk_select")
                add_saves = st.number_input("Add GK Saves Count:", min_value=0, max_value=30, step=1)
                if st.button("Save GK Stats", key="btn_save_gk"):
                    st.session_state.player_stats[sel_gk]["gk_saves"] = st.session_state.player_stats[sel_gk].get("gk_saves", 0) + add_saves
                    save_data_to_file()
                    st.success(f"Updated saves for GK @{sel_gk}!")

    with tab_reset:
        st.subheader("Master System Reset")
        if curr_user["role"] != "Superadmin":
            st.error("⛔ Master Reset operation is restricted exclusively to Superadmin.")
        else:
            if st.button("🔥 EXECUTE MASTER RESET", key="btn_master_reset"):
                st.session_state.group_chat = []
                st.session_state.football_ai_chats = []
                st.session_state.personal_ai_chats = {}
                save_data_to_file()
                st.success("Master Reset completed! All chat logs and AI conversations purged safely.")
                st.rerun()
