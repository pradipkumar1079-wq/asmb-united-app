import streamlit as st
import datetime
import math
import re
import random
import pandas as pd
from PIL import Image
import io

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
    """Initialize global database tables in Streamlit's persistent session state."""
    if "db_initialized" not in st.session_state:
        # Dynamic Customization App Settings
        st.session_state.app_settings = {
            "app_name": "ASMB United Football Club",
            "club_photo": None,
            "bg_color": "#0e1117"  # Dynamic background daily color
        }
        
        # User Directory
        # Table Schema: username (PK), password, full_name, jersey_num, jersey_name, photo, personal_ai_name, role, position, status, block_reason
        st.session_state.users = {}
        
        # Ratings & Fouls Directory
        # Key: (rater_username, target_username) -> {"rating": float, "fouls": int}
        st.session_state.ratings_db = {}
        
        # Player Performance Adjustments & Stats
        # Key: username -> {"goals": int, "assists": int, "conceded_penalty": float, "attendance": str, "rating_penalty": float}
        st.session_state.player_stats = {}
        
        # Group Chat Messages List: [{"sender": str, "message": str, "timestamp": str}]
        st.session_state.group_chat = []
        
        # Football AI Conversations List (Public): [{"sender": str, "prompt": str, "response": str, "timestamp": str}]
        st.session_state.football_ai_chats = []
        
        # Personal AI Conversations Dict: {username: [{"prompt": str, "response": str, "timestamp": str}]}
        st.session_state.personal_ai_chats = {}
        
        # Notice Board List: [{"id": int, "author": str, "title": str, "content": str, "timestamp": str, "type": str}]
        st.session_state.notice_board = []
        
        # MOTM Sunday Polls: {username: voted_target_username}
        st.session_state.motm_votes = {}
        
        # Star & Injured Lists: set of usernames
        st.session_state.injured_players = set()
        
        # Matchday / Practice Settings
        st.session_state.match_settings = {
            "asmb_player_count": 11,
            "opponent_player_count": 11,
            "opponent_formation": "4-4-2",
            "goals_conceded": 0
        }
        
        # Block Appeals: {username: appeal_message}
        st.session_state.block_appeals = {}
        
        st.session_state.db_initialized = True

init_db()

# ==========================================
# 1. DYNAMIC CSS & BRANDING OVERRIDES
# ==========================================
# Strict CSS override: Button Background #000000, Button Text #FFFFFF
bg_color = st.session_state.app_settings.get("bg_color", "#0e1117")
st.markdown(f"""
    <style>
    /* Dynamic AI Background Color */
    .stApp {{
        background-color: {bg_color};
    }}
    /* Strict Button Override Rules */
    div.stButton > button {{
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
        border-radius: 6px !important;
        font-weight: bold !important;
    }}
    div.stButton > button:hover {{
        background-color: #222222 !important;
        color: #00FFCC !important;
        border-color: #00FFCC !important;
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. HELPER CALCULATORS & BUSINESS LOGIC
# ==========================================
def compute_player_rating(username):
    """Calculates player net rating factoring base ratings, fouls, goals, assists, conceded penalties, and admin penalties."""
    # Base user ratings from teammates
    user_ratings = [data["rating"] for (rater, target), data in st.session_state.ratings_db.items() if target == username]
    user_fouls = [data["fouls"] for (rater, target), data in st.session_state.ratings_db.items() if target == username]
    
    base_rating = (sum(user_ratings) / len(user_ratings)) if user_ratings else 6.0
    avg_fouls = (sum(user_fouls) / len(user_fouls)) if user_fouls else 0.0
    
    # Adjustments
    stats = st.session_state.player_stats.get(username, {"goals": 0, "assists": 0, "conceded_penalty": 0.0, "attendance": "Present", "rating_penalty": 0.0})
    
    # Rating adjustment matrix: Base + Goals + Assists - Fouls Penalty - Defensive Penalty - Fairplay Penalty
    goals_bonus = stats["goals"] * 0.5
    assists_bonus = stats["assists"] * 0.3
    foul_penalty = avg_fouls * 0.2
    
    net_rating = base_rating + goals_bonus + assists_bonus - foul_penalty - stats["conceded_penalty"] - stats["rating_penalty"]
    
    # Attendance Factor
    if stats.get("attendance") == "Absent":
        net_rating -= 1.0
        
    return max(0.0, min(10.0, round(net_rating, 2)))

def update_star_players():
    """Automatically designates any player with total rating above 8.5 as a Star Player."""
    for uname, udata in st.session_state.users.items():
        rating = compute_player_rating(uname)
        # Star designation
        if rating > 8.5:
            udata["is_star"] = True
        else:
            udata["is_star"] = False

def audit_block_reason(reason):
    """Personal AI automated audit logic to assess block validity."""
    invalid_keywords = ["test", "joke", "nothing", "fun", "no reason", "random", "asdf", "lol"]
    clean_reason = reason.strip().lower()
    if len(clean_reason) < 5 or any(k in clean_reason for k in invalid_keywords):
        return False  # Unjustified block
    return True  # Valid block

def execute_daily_ai_background_script():
    """Simulates automated AI background update script."""
    colors = ["#0e1117", "#121824", "#1a0f1a", "#0f1a18", "#1c1912"]
    today_index = datetime.datetime.now().day % len(colors)
    st.session_state.app_settings["bg_color"] = colors[today_index]

execute_daily_ai_background_script()

# ==========================================
# 3. AUTHENTICATION & LOGIN / REGISTRATION
# ==========================================
if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

def login_register_surface():
    st.title("⚽ " + st.session_state.app_settings["app_name"])
    if st.session_state.app_settings["club_photo"]:
        st.image(st.session_state.app_settings["club_photo"], width=300)
        
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
        reg_username = st.text_input("Username (Unique Key)*", key="reg_uname").strip()
        reg_password = st.text_input("Password*", type="password", key="reg_pass")
        reg_full_name = st.text_input("Full Name*", key="reg_fullname")
        reg_jersey_num = st.number_input("Jersey Number*", min_value=1, max_value=99, step=1)
        reg_jersey_name = st.text_input("Jersey Player Name*", key="reg_jname")
        reg_photo = st.file_uploader("Photo Upload (Optional)", type=["jpg", "png", "jpeg"])
        reg_personal_ai = st.text_input("Personal AI Custom Name*", value="Jarvis", key="reg_pai")
        
        # Position input logic
        is_first_user = len(st.session_state.users) == 0
        if is_first_user:
            st.info("ℹ️ You are the first registered user. You will automatically be granted Superadmin (S.A) privileges!")
            reg_position = st.selectbox("Assign Initial Position (Superadmin Exclusive)", ["GK", "CB", "LB", "RB", "CM", "CAM", "RW", "LW", "ST"])
        else:
            st.warning("🔒 Position field is strictly disabled during registration. An Admin/Superadmin will assign your position post-registration.")
            reg_position = "Unassigned"

        if st.button("Register Account", key="btn_reg"):
            if not reg_username or not reg_password or not reg_full_name or not reg_jersey_name or not reg_personal_ai:
                st.error("Please fill in all mandatory fields.")
                return
            
            # Duplicate registration constraint
            if reg_username in st.session_state.users:
                st.error("⚠️ Username already exists! Redirecting duplicate registration attempt to Login surface...")
                st.rerun()
                return
            
            # Photo processing
            photo_bytes = reg_photo.read() if reg_photo else None
            
            # Role Determination
            role = "Superadmin" if is_first_user else "Player"
            
            # Register User
            st.session_state.users[reg_username] = {
                "password": reg_password,
                "full_name": reg_full_name,
                "jersey_num": reg_jersey_num,
                "jersey_name": reg_jersey_name,
                "photo": photo_bytes,
                "personal_ai_name": reg_personal_ai,
                "role": role,
                "position": reg_position,
                "status": "Active",
                "block_reason": "",
                "is_star": False
            }
            
            # Initialize stats
            st.session_state.player_stats[reg_username] = {
                "goals": 0, "assists": 0, "conceded_penalty": 0.0, "attendance": "Present", "rating_penalty": 0.0
            }
            
            st.success("Registration successful! Redirecting to login...")
            st.rerun()

if not st.session_state.authenticated_user:
    login_register_surface()
    st.stop()

# ==========================================
# 4. AUTHENTICATED SESSION SETUP & SIDEBAR
# ==========================================
curr_username = st.session_state.authenticated_user
curr_user = st.session_state.users[curr_username]
update_star_players()

# SIDEBAR & LOGOUT
st.sidebar.title(st.session_state.app_settings["app_name"])
if curr_user["photo"]:
    st.sidebar.image(curr_user["photo"], width=100)
st.sidebar.markdown(f"**Logged in as:** {curr_user['full_name']} (`@{curr_username}`)")
st.sidebar.markdown(f"**Role:** `{curr_user['role']}` | **Position:** `{curr_user['position']}`")

if curr_user["status"] == "Blocked":
    st.sidebar.error("🚨 ACCOUNT BLOCKED")

if st.sidebar.button("Logout", key="btn_logout"):
    st.session_state.authenticated_user = None
    st.rerun()

st.sidebar.divider()

# Navigation Tabs
if curr_user["status"] == "Blocked":
    nav_choice = "🚩 Blocked Dashboard / Appeals"
else:
    nav_choice = st.sidebar.radio("Navigation Menu", [
        "📌 Notice Board & News",
        "👥 Player Directory & Roster",
        "⚽ Squad Generation & Tactics",
        "⭐ Teammate Ratings & Fouls",
        "💬 Club House Group Chat",
        "🤖 Football AI (Public)",
        "👤 Personal AI (Private)",
        "⚙️ Admin Control Panel"
    ])

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
    
    # Official Notices display
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
    
    with tab_dir:
        st.subheader("Registered Club Members")
        st.write("Full directory accessible to all past, present, and future registered members.")
        
        dir_data = []
        for uname, udata in st.session_state.users.items():
            dir_data.append({
                "Username": uname,
                "Full Name": udata["full_name"],
                "Jersey #": udata["jersey_num"],
                "Jersey Name": udata["jersey_name"],
                "Position": udata["position"],
                "Role": udata["role"],
                "Status": udata["status"]
            })
        st.dataframe(pd.DataFrame(dir_data), use_container_width=True)

    with tab_star:
        st.subheader("⭐ Designated Star Players (> 8.5 Total Rating)")
        star_players = [u for u, udata in st.session_state.users.items() if udata.get("is_star")]
        if not star_players:
            st.info("No star players designated at this moment.")
        else:
            for sp in star_players:
                u = st.session_state.users[sp]
                r = compute_player_rating(sp)
                st.success(f"🌟 **{u['full_name']}** (`@{sp}`) - Position: {u['position']} | Rating: **{r} / 10.0**")

    with tab_inj:
        st.subheader("🏥 Injured Player Roster")
        if not st.session_state.injured_players:
            st.info("No injured players currently logged.")
        else:
            for ip in st.session_state.injured_players:
                u = st.session_state.users.get(ip)
                if u:
                    st.warning(f"🩹 **{u['full_name']}** (`@{ip}`) - Position: {u['position']}")

# ==========================================
# 8. FEATURE MODULE: SQUAD GENERATION & TACTICS
# ==========================================
elif nav_choice == "⚽ Squad Generation & Tactics":
    st.header("⚽ Football AI Tactical Engine & Squad Output")
    
    st.subheader("📅 Weekly Schedule Operational Workflow")
    st.info("• **Practice Days (Mon-Thu):** Auto-splits active players into 2 balanced teams with equal aggregate ratings.\n"
            "• **Squad Release Day (Saturday):** Generates single dynamic match squad sorted strictly by descending performance rating.\n"
            "• **Match Day (Sunday):** Competitive match deployment and MOTM polling.")
    
    day_selection = st.selectbox("Select Operational Day Simulation", ["Saturday (Match Squad Generation)", "Practice Day (Mon-Thu Team Split)", "Sunday (Matchday)"])
    
    if day_selection == "Saturday (Match Squad Generation)":
        st.subheader("Saturday Dynamic Match Squad Generation")
        target_count = st.session_state.match_settings["asmb_player_count"]
        st.write(f"Active Selected Player Count Constraint: **{target_count} Players**")
        
        if st.button("Generate Match Squad", key="btn_gen_squad"):
            active_players = [u for u, udata in st.session_state.users.items() if udata["status"] == "Active" and u not in st.session_state.injured_players]
            
            # Sort strictly in descending order of ratings
            sorted_players = sorted(active_players, key=lambda u: compute_player_rating(u), reverse=True)
            
            starters = sorted_players[:target_count]
            subs = sorted_players[target_count:]
            
            st.markdown("### 🏆 ASMB United Starting Lineup")
            squad_notice_text = f"### ⚽ Dynamic Match Squad ({datetime.date.today()})\n\n**Starting Lineup:**\n"
            
            for idx, p in enumerate(starters, 1):
                r = compute_player_rating(p)
                u = st.session_state.users[p]
                line = f"{idx}. **{u['full_name']}** (`@{p}`) - Pos: {u['position']} | Rating: **{r}**"
                st.markdown(line)
                squad_notice_text += f"{line}\n"
                
            if subs:
                st.markdown("### 🔄 Substitutes Bench")
                squad_notice_text += "\n**Substitutes:**\n"
                for idx, p in enumerate(subs, 1):
                    r = compute_player_rating(p)
                    u = st.session_state.users[p]
                    line = f"Sub {idx}: **{u['full_name']}** (`@{p}`) - Pos: {u['position']} | Rating: **{r}**"
                    st.markdown(line)
                    squad_notice_text += f"{line}\n"
            
            # Dynamic Tactical Formation Logic
            if target_count < 11:
                formation = f"Adaptive Custom {target_count}-a-side Formation (Optimized Balance)"
            else:
                formation = "Standard 4-3-3 Balanced Formation"
                
            squad_notice_text += f"\n**Tactical Formation:** {formation}"
            st.success(f"**Tactical Formation Engine:** {formation}")
            
            # Auto Publish to Notice Board
            st.session_state.notice_board.append({
                "id": len(st.session_state.notice_board) + 1,
                "author": st.session_state.app_settings["app_name"] + " (Football AI)",
                "title": "Official Match Squad & Formation Announcement",
                "content": squad_notice_text,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "type": "Match Announcement"
            })
            st.info("📢 Match squad automatically published to Notice Board!")

    elif day_selection == "Practice Day (Mon-Thu Team Split)":
        st.subheader("Practice Days Dynamic Balanced Team Generator")
        if st.button("Generate Balanced Practice Teams", key="btn_gen_practice"):
            active_players = [u for u, udata in st.session_state.users.items() if udata["status"] == "Active" and u not in st.session_state.injured_players]
            sorted_players = sorted(active_players, key=lambda u: compute_player_rating(u), reverse=True)
            
            team_a, team_b = [], []
            rate_a, rate_b = 0.0, 0.0
            
            # Snake draft allocation for equalized aggregate ratings
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
                st.markdown(f"### 🔵 Team Alpha (Aggregate Rating: {round(rate_a, 2)})")
                for p, r in team_a:
                    u = st.session_state.users[p]
                    st.write(f"• **{u['full_name']}** ({u['position']}) - Rating: **{r}**")
            with col2:
                st.markdown(f"### 🔴 Team Beta (Aggregate Rating: {round(rate_b, 2)})")
                for p, r in team_b:
                    u = st.session_state.users[p]
                    st.write(f"• **{u['full_name']}** ({u['position']}) - Rating: **{r}**")

# ==========================================
# 9. FEATURE MODULE: TEAMMATE RATINGS & FOULS
# ==========================================
elif nav_choice == "⭐ Teammate Ratings & Fouls":
    st.header("⭐ Teammate Performance Rating & Foul Management")
    
    st.info("🔒 **Rating Visibility Rules:** Peer ratings are hidden during general browsing. Ratings become visible in squad views or to S.A/Admins.")
    
    # Rating Guide Link
    with st.expander("📖 View Official Rating & Foul Scoring Guide Panel"):
        st.markdown("""
        **Rating Scale Guide (0.0 to 10.0):**
        - **9.0 - 10.0:** World Class / Match Winner (Automatic Star Player above 8.5)
        - **7.5 - 8.9:** Outstanding Performance
        - **6.0 - 7.4:** Solid / Average Performance
        - **0.0 - 5.9:** Poor Performance / Disciplinary Issues
        
        **Foul Scale Guide (0 to 10):**
        - Tracks tactical fouls, yellow/red card infractions, and unsportsmanlike behavior.
        """)
        
    st.subheader("Submit / Edit Teammate Rating")
    target_users = [u for u in st.session_state.users.keys() if u != curr_username]
    
    if not target_users:
        st.warning("No other registered members available to rate.")
    else:
        selected_target = st.selectbox("Select Teammate to Rate:", target_users)
        
        # Self-rating prohibition enforcement
        if selected_target == curr_username:
            st.error("⛔ Self-rating is strictly prohibited!")
        else:
            # Check existing submission for correction panel
            existing_entry = st.session_state.ratings_db.get((curr_username, selected_target), {"rating": 6.0, "fouls": 0})
            
            st.markdown("### Rating Correction / Override Panel")
            new_rating = st.slider("Performance Rating (0.0 - 10.0)", min_value=0.0, max_value=10.0, value=float(existing_entry["rating"]), step=0.1)
            new_fouls = st.number_input("Fouls / Infractions Count (0 - 10)", min_value=0, max_value=10, value=int(existing_entry["fouls"]), step=1)
            
            if st.button("Submit / Correct Rating", key="btn_save_rating"):
                st.session_state.ratings_db[(curr_username, selected_target)] = {
                    "rating": round(new_rating, 2),
                    "fouls": new_fouls
                }
                st.success(f"Successfully recorded rating for @{selected_target}!")

# ==========================================
# 10. FEATURE MODULE: CLUB HOUSE GROUP CHAT
# ==========================================
elif nav_choice == "💬 Club House Group Chat":
    st.header("💬 ASMB United WhatsApp-Style Member Chat")
    
    # Message Display
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
            st.rerun()

# ==========================================
# 11. FEATURE MODULE: FOOTBALL AI (PUBLIC)
# ==========================================
elif nav_choice == "🤖 Football AI (Public)":
    st.header(f"🤖 Football AI - Public Assistant ({st.session_state.app_settings['app_name']})")
    st.caption("ℹ️ Public Assistant. All queries and responses are publicly visible to all members.")
    
    # Display public chat logs
    for chat in st.session_state.football_ai_chats:
        st.markdown(f"**👤 {chat['sender']} ({chat['timestamp']}):** {chat['prompt']}")
        st.markdown(f"🤖 **Football AI:** {chat['response']}")
        st.divider()
        
    prompt = st.text_input("Ask Football AI regarding tactics, counter-plays, or team advice:", key="f_ai_prompt")
    if st.button("Ask Football AI", key="btn_ask_fai"):
        if prompt.strip():
            # Simulated Football AI Intelligence
            resp = f"Tactical Analysis for '{prompt}': Maintain high pressing intensity, utilize overlap wing play, and restrict space between defensive lines."
            st.session_state.football_ai_chats.append({
                "sender": curr_user["full_name"],
                "prompt": prompt.strip(),
                "response": resp,
                "timestamp": datetime.datetime.now().strftime("%H:%M")
            })
            st.rerun()

# ==========================================
# 12. FEATURE MODULE: PERSONAL AI (PRIVATE)
# ==========================================
elif nav_choice == "👤 Personal AI (Private)":
    pai_name = curr_user["personal_ai_name"]
    st.header(f"👤 {pai_name} - Personal Assistant (Private)")
    st.caption("🔒 Strictly confidential. Conversations are private to you.")
    
    if curr_username not in st.session_state.personal_ai_chats:
        st.session_state.personal_ai_chats[curr_username] = []
        
    user_p_chats = st.session_state.personal_ai_chats[curr_username]
    
    # Display private chats
    for chat in user_p_chats:
        st.markdown(f"**You ({chat['timestamp']}):** {chat['prompt']}")
        st.markdown(f"🤖 **{pai_name}:** {chat['response']}")
        st.divider()
        
    p_prompt = st.text_input(f"Chat with {pai_name}:", key="p_ai_prompt")
    if st.button("Send to Personal AI", key="btn_ask_pai"):
        if p_prompt.strip():
            resp = f"Hello {curr_user['full_name']}! As your personal assistant {pai_name}, I am tracking your ratings and performance metrics closely."
            user_p_chats.append({
                "prompt": p_prompt.strip(),
                "response": resp,
                "timestamp": datetime.datetime.now().strftime("%H:%M")
            })
            st.rerun()
            
    st.divider()
    st.subheader("🗳️ Sunday Man of the Match (MOTM) Polling Interface")
    active_candidates = [u for u in st.session_state.users.keys()]
    motm_vote = st.selectbox("Cast your Sunday MOTM Vote:", active_candidates, key="motm_select")
    
    if st.button("Submit MOTM Vote", key="btn_vote_motm"):
        st.session_state.motm_votes[curr_username] = motm_vote
        st.success(f"Vote cast successfully for @{motm_vote}!")
        
        # Aggregation check
        total_votes = len(st.session_state.motm_votes)
        if total_votes >= len(st.session_state.users) and len(st.session_state.users) > 0:
            # Aggregate Winner
            votes_list = list(st.session_state.motm_votes.values())
            winner = max(set(votes_list), key=votes_list.count)
            winner_user = st.session_state.users[winner]
            
            # Publish to Notice Board
            st.session_state.notice_board.append({
                "id": len(st.session_state.notice_board) + 1,
                "author": "Personal AI Aggregator",
                "title": "🏆 Sunday Man of the Match (MOTM) Winner Announced!",
                "content": f"The votes have been aggregated! **{winner_user['full_name']}** (`@{winner}`) has been voted Man of the Match for {datetime.date.today()}!",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "type": "MOTM Award"
            })

# ==========================================
# 13. FEATURE MODULE: ADMIN CONTROL PANEL
# ==========================================
elif nav_choice == "⚙️ Admin Control Panel":
    st.header("⚙️ Administrative Control & Management Panel")
    
    # Permission Verification
    if curr_user["role"] not in ["Superadmin", "Admin"]:
        st.error("⛔ Access Denied. Administrative privileges required.")
        st.stop()
        
    tab_branding, tab_roles, tab_block, tab_stats, tab_reset = st.tabs([
        "🎨 App Customization & Notices",
        "👑 Role & Position Management",
        "🚫 Block System & Fair-Play Arbitration",
        "📊 Conceded Goals & Match Adjustments",
        "🧹 Master Reset (S.A Only)"
    ])
    
    with tab_branding:
        st.subheader("Dynamically Configure Branding & Notices")
        new_app_name = st.text_input("Application / Club Name:", value=st.session_state.app_settings["app_name"])
        club_photo_file = st.file_uploader("Upload Header Photo", type=["jpg", "png", "jpeg"], key="admin_club_photo")
        
        if st.button("Update Branding Settings", key="btn_save_branding"):
            st.session_state.app_settings["app_name"] = new_app_name
            if club_photo_file:
                st.session_state.app_settings["club_photo"] = club_photo_file.read()
            st.success("App branding updated successfully!")
            st.rerun()
            
        st.divider()
        st.subheader("Post Official Announcement")
        notice_title = st.text_input("Notice Title:")
        notice_content = st.text_area("Notice Content:")
        if st.button("Post Announcement", key="btn_post_notice"):
            if notice_title and notice_content:
                st.session_state.notice_board.append({
                    "id": len(st.session_state.notice_board) + 1,
                    "author": curr_user["full_name"],
                    "title": notice_title,
                    "content": notice_content,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": "Official Announcement"
                })
                st.success("Notice posted successfully!")
                st.rerun()

    with tab_roles:
        st.subheader("Manage User Positions & Admin Status")
        target_role_user = st.selectbox("Select Target User:", list(st.session_state.users.keys()), key="role_target_select")
        
        col_pos, col_adm = st.columns(2)
        with col_pos:
            st.markdown("### Assign / Update Position")
            new_pos = st.selectbox("Position:", ["GK", "CB", "LB", "RB", "CM", "CAM", "RW", "LW", "ST"], key="select_new_pos")
            if st.button("Update Position", key="btn_update_pos"):
                st.session_state.users[target_role_user]["position"] = new_pos
                st.success(f"Updated position of @{target_role_user} to {new_pos}!")
                st.rerun()
                
        with col_adm:
            if curr_user["role"] == "Superadmin":
                st.markdown("### Grant / Dismiss Admin Role")
                if st.button("Promote to Admin", key="btn_promote"):
                    st.session_state.users[target_role_user]["role"] = "Admin"
                    st.success(f"Granted Admin privileges to @{target_role_user}!")
                    st.rerun()
                if st.button("Dismiss Admin Role", key="btn_dismiss"):
                    if st.session_state.users[target_role_user]["role"] != "Superadmin":
                        st.session_state.users[target_role_user]["role"] = "Player"
                        st.success(f"Revoked Admin privileges from @{target_role_user}!")
                        st.rerun()

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
                    # Execute Block
                    target_u = st.session_state.users[block_target]
                    target_u["status"] = "Blocked"
                    target_u["block_reason"] = mandatory_reason.strip()
                    
                    # Instantly purge chat messages & personal AI logs of blocked user
                    st.session_state.group_chat = [m for m in st.session_state.group_chat if f"(@{block_target})" not in m["sender"]]
                    if block_target in st.session_state.personal_ai_chats:
                        st.session_state.personal_ai_chats[block_target] = []
                        
                    st.warning(f"User @{block_target} has been blocked.")
                    
                    # Execute Personal AI Arbitration Audit
                    valid = audit_block_reason(mandatory_reason)
                    if not valid:
                        # Automated Fair-play Arbitration Triggered
                        target_u["status"] = "Active"
                        st.session_state.player_stats[curr_username]["rating_penalty"] += 5.0
                        st.error(f"🚨 FAIR-PLAY ARBITRATION AUDIT: Block reason deemed invalid/unjustified! @{block_target} was automatically unblocked. A 5-point rating penalty has been applied to Admin @{curr_username}!")
                    st.rerun()
                    
        with col_b2:
            if st.button("Unblock Target User", key="btn_exec_unblock"):
                st.session_state.users[block_target]["status"] = "Active"
                st.success(f"User @{block_target} unblocked successfully.")
                st.rerun()

    with tab_stats:
        st.subheader("Attendance, Performance Adjustments & Conceded Goal Penalties")
        
        col_att, col_perf = st.columns(2)
        with col_att:
            st.markdown("### Mark Attendance")
            att_user = st.selectbox("Select Player for Attendance:", list(st.session_state.users.keys()), key="att_u_select")
            att_status = st.radio("Status:", ["Present", "Absent"], key="att_rad")
            if st.button("Save Attendance", key="btn_save_att"):
                st.session_state.player_stats[att_user]["attendance"] = att_status
                st.success(f"Attendance recorded for @{att_user}!")
                
        with col_perf:
            st.markdown("### Goals & Assists Adjustments")
            perf_user = st.selectbox("Select Player:", list(st.session_state.users.keys()), key="perf_u_select")
            add_goals = st.number_input("Goals Scored:", min_value=0, max_value=20, step=1)
            add_assists = st.number_input("Assists Provided:", min_value=0, max_value=20, step=1)
            if st.button("Save Performance Stats", key="btn_save_perf"):
                st.session_state.player_stats[perf_user]["goals"] += add_goals
                st.session_state.player_stats[perf_user]["assists"] += add_assists
                st.success(f"Performance stats updated for @{perf_user}!")
                
        st.divider()
        st.markdown("### Defensive Conceded Goals Auto-Deduction Engine")
        conceded_count = st.number_input("Total Match Goals Conceded:", min_value=0, max_value=20, step=1)
        if st.button("Apply Defensive Concession Deductions", key="btn_apply_conceded"):
            for u, udata in st.session_state.users.items():
                pos = udata["position"]
                if pos == "GK":
                    st.session_state.player_stats[u]["conceded_penalty"] += (conceded_count * 2.0)
                elif pos in ["CB", "LB", "RB", "LWB", "RWB"]:
                    st.session_state.player_stats[u]["conceded_penalty"] += (conceded_count * 1.75)
                else:
                    st.session_state.player_stats[u]["conceded_penalty"] += (conceded_count * 1.5)
            st.success(f"Applied conceded goal penalties across defensive positions for {conceded_count} goal(s)!")

    with tab_reset:
        st.subheader("Master System Reset")
        if curr_user["role"] != "Superadmin":
            st.error("⛔ Master Reset operation is restricted exclusively to Superadmin.")
        else:
            st.warning("⚠️ **Master Reset Action:** Instantly purges all public group chats, Football AI chats, and Personal AI conversations while preserving registered user profiles, credentials, and database schemas.")
            if st.button("🔥 EXECUTE MASTER RESET", key="btn_master_reset"):
                st.session_state.group_chat = []
                st.session_state.football_ai_chats = []
                st.session_state.personal_ai_chats = {}
                st.success("Master Reset completed! All chat logs and AI conversations purged safely.")
                st.rerun()
