import streamlit as st
import pandas as pd
import datetime
import json
import os
import base64

# ==========================================
# 0. STREAMLIT CONFIG & BRIGHT VIBRANT CSS
# ==========================================
st.set_page_config(
    page_title="ASMB United Football Club",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Persistent JSON Database File Path
DB_FILE = "asmb_club_db.json"

# Daily Changing Bright & Vibrant Background Gradient Array
day_of_year = datetime.date.today().timetuple().tm_yday
bright_gradients = [
    "linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)",
    "linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%)",
    "linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)",
    "linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)",
    "linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)",
    "linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%)",
    "linear-gradient(135deg, #f6d365 0%, #fda085 100%)"
]
current_bg = bright_gradients[day_of_year % len(bright_gradients)]

# Inject Custom CSS for Bright Styling, WhatsApp Chat & Black Buttons
st.markdown(f"""
    <style>
    .stApp {{
        background: {current_bg};
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    /* Force Buttons to Solid Black (#000000) with White (#FFFFFF) text */
    div.stButton > button {{
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid #111111 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 8px 18px !important;
    }}
    div.stButton > button:hover {{
        background-color: #222222 !important;
        color: #FFFFFF !important;
        border-color: #555555 !important;
    }}
    /* WhatsApp Chat Bubble Styling */
    .chat-bubble-user {{
        background-color: #dcf8c6;
        color: #000000;
        padding: 10px 14px;
        border-radius: 12px 12px 0px 12px;
        margin: 6px 0px;
        max-width: 80%;
        float: right;
        clear: both;
        box-shadow: 0 1px 2px rgba(0,0,0,0.15);
    }}
    .chat-bubble-ai {{
        background-color: #ffffff;
        color: #000000;
        padding: 10px 14px;
        border-radius: 12px 12px 12px 0px;
        margin: 6px 0px;
        max-width: 80%;
        float: left;
        clear: both;
        box-shadow: 0 1px 2px rgba(0,0,0,0.15);
    }}
    .chat-meta {{
        font-size: 0.75rem;
        color: #666666;
        margin-top: 4px;
        text-align: right;
    }}
    /* Card Container */
    .content-card {{
        background-color: rgba(255, 255, 255, 0.92);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 15px;
    }}
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 1. PERSISTENT JSON DATABASE CONTROLLER
# ==========================================
def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "users": {},
            "notices": [],
            "public_chat": [],
            "private_chats": {},
            "app_config": {
                "app_name": "ASMB United Football Club",
                "logo_b64": ""
            },
            "ratings_db": {},
            "fouls_db": {},
            "motm_votes": {}
        }
        save_db(default_data)
        return default_data
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "users": {}, "notices": [], "public_chat": [],
            "private_chats": {}, "app_config": {"app_name": "ASMB United FC", "logo_b64": ""},
            "ratings_db": {}, "fouls_db": {}, "motm_votes": {}
        }

def save_db(data=None):
    if data is None:
        data = {
            "users": st.session_state.get("db_users", {}),
            "notices": st.session_state.get("db_notices", []),
            "public_chat": st.session_state.get("db_public_chat", []),
            "private_chats": st.session_state.get("db_private_chats", {}),
            "app_config": st.session_state.get("db_app_config", {"app_name": "ASMB United FC", "logo_b64": ""}),
            "ratings_db": st.session_state.get("db_ratings", {}),
            "fouls_db": st.session_state.get("db_fouls", {}),
            "motm_votes": st.session_state.get("db_motm_votes", {})
        }
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def init_session_from_db():
    db = load_db()
    if "db_users" not in st.session_state:
        st.session_state["db_users"] = db.get("users", {})
        st.session_state["db_notices"] = db.get("notices", [])
        st.session_state["db_public_chat"] = db.get("public_chat", [])
        st.session_state["db_private_chats"] = db.get("private_chats", {})
        st.session_state["db_app_config"] = db.get("app_config", {"app_name": "ASMB United FC", "logo_b64": ""})
        st.session_state["db_ratings"] = db.get("ratings_db", {})
        st.session_state["db_fouls"] = db.get("fouls_db", {})
        st.session_state["db_motm_votes"] = db.get("motm_votes", {})
        st.session_state["current_user"] = None

init_session_from_db()


# ==========================================
# 2. HELPER CALCULATIONS & BANGLA AI ENGINE
# ==========================================
def calculate_net_rating(username):
    users = st.session_state["db_users"]
    user = users.get(username)
    if not user:
        return 0.0
    
    # Base user ratings
    ratings_dict = st.session_state["db_ratings"]
    user_ratings = [v for k, v in ratings_dict.items() if k.startswith(f"{username}::")]
    base_rating = sum(user_ratings) / len(user_ratings) if user_ratings else user.get("rating", 7.0)
    
    # Calculate fouls
    fouls_dict = st.session_state["db_fouls"]
    user_fouls = [v for k, v in fouls_dict.items() if k.startswith(f"{username}::")]
    avg_foul = sum(user_fouls) / len(user_fouls) if user_fouls else user.get("fouls", 0.0)
    
    # Goal/Assist Bonus
    bonus = (user.get("goals", 0) * 0.5) + (user.get("assists", 0) * 0.3)
    
    # Attendance Factor
    att_factor = (user.get("attendance_count", 0) * 0.1)
    
    # Own Goal Penalties
    pos = user.get("position", "Midfielder")
    og_penalty_rate = 1.5
    if "GK" in pos or "Keeper" in pos:
        og_penalty_rate = 2.0
    elif "CB" in pos or "LB" in pos or "RB" in pos or "Defender" in pos:
        og_penalty_rate = 1.75
    og_penalty = user.get("own_goals", 0) * og_penalty_rate
    
    # Unfair block penalty
    fairplay_penalty = user.get("penalty_points", 0)
    
    final_score = base_rating - (avg_foul * 0.5) + bonus + att_factor - og_penalty - fairplay_penalty
    return round(max(1.0, min(10.0, final_score)), 2)

def is_star_player(username):
    return calculate_net_rating(username) > 8.5

def push_notice(title, body, author="Football AI"):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    st.session_state["db_notices"].insert(0, {
        "date": now,
        "title": title,
        "body": body,
        "author": author
    })
    save_db()

def generate_ai_response(prompt, ai_name="Football AI"):
    # Detect Bangla Script or Banglish
    is_bangla = any('\u0980' <= char <= '\u09ff' for char in prompt) or "kemon" in prompt.lower() or "ki" in prompt.lower()
    
    if is_bangla:
        responses = [
            f"ধন্যবাদ আপনার প্রশ্নের জন্য! {ai_name} হিসেবে আমি মনে করি আমাদের টিমের পাসিং একুরেসি এবং শর্ট পাসের দিকে আরও নজর দেওয়া উচিত।",
            f"অবশ্যই! আমাদের বর্তমান স্কোয়াড ফরমেশন এবং খেলোয়ারদের ফর্ম খুবই চমৎকার। পরবর্তী ম্যাচের জন্য প্রস্তুত থাকুন।",
            f"খেলোয়াড়দের ফিটনেস ও নিয়মিত প্র্যাকটিসই ম্যাচের মূল চাবিকাঠি। আপনার পরামর্শ টিমের জয়ে সাহায্য করবে।"
        ]
    else:
        responses = [
            f"Thanks for your message! As {ai_name}, I recommend keeping high pressing and swift counter-attacks for upcoming matches.",
            f"Analyzing stats... Our squad defensive compact structure is solid. Keep up the high stamina!",
            f"Tactical advice: Maintain mid-block stability and optimize chances on set-pieces."
        ]
    import random
    return random.choice(responses)


# ==========================================
# 3. AUTHENTICATION MODULE
# ==========================================
def auth_ui():
    st.title(f"⚽ {st.session_state['db_app_config']['app_name']}")
    st.caption("ASMB United Football Club Management System")
    
    tab_login, tab_register = st.tabs(["🔒 Login", "📝 Register New Account"])
    
    with tab_login:
        st.subheader("Account Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login"):
            users = st.session_state["db_users"]
            if username in users and users[username]["password"] == password:
                st.session_state["current_user"] = username
                st.success(f"Welcome back, {users[username]['full_name']}!")
                st.rerun()
            else:
                st.error("Invalid Username or Password!")
                
    with tab_register:
        st.subheader("Player Registration")
        is_first_user = len(st.session_state["db_users"]) == 0
        
        reg_username = st.text_input("Choose Username (Unique)", key="reg_user")
        reg_password = st.text_input("Choose Password", type="password", key="reg_pass")
        reg_fullname = st.text_input("Full Name")
        reg_jersey_no = st.number_input("Jersey Number", min_value=1, max_value=99, step=1)
        reg_jersey_name = st.text_input("Jersey Player Name")
        reg_ai_name = st.text_input("Name Your Personal AI Companion", value="Jarvis")
        
        # Position Exception: Only 1st user sets position during signup
        reg_position = "Unassigned"
        if is_first_user:
            st.info("👑 First registered user becomes the Superadmin automatically!")
            reg_position = st.selectbox("Assign Your Position", ["Goalkeeper (GK)", "Defender (CB/LB/RB)", "Midfielder (CM/CAM)", "Forward (ST/LW/RW)"])
        
        if st.button("Register Account"):
            if not reg_username or not reg_password or not reg_fullname:
                st.warning("Please complete all required fields.")
                return
            
            # Prevent duplicate registration & auto-redirect logic
            if reg_username in st.session_state["db_users"]:
                st.error("🚨 Username already taken! Duplicate registration is strictly prohibited. Redirecting to login tab...")
                return
            
            role = "Superadmin" if is_first_user else "Player"
            
            st.session_state["db_users"][reg_username] = {
                "password": reg_password,
                "full_name": reg_fullname,
                "jersey_no": reg_jersey_no,
                "jersey_name": reg_jersey_name,
                "position": reg_position,
                "role": role,
                "personal_ai_name": reg_ai_name,
                "is_blocked": False,
                "last_word_used": False,
                "rating": 7.0,
                "fouls": 0.0,
                "goals": 0,
                "assists": 0,
                "attendance_count": 0,
                "own_goals": 0,
                "is_injured": False,
                "penalty_points": 0
            }
            save_db()
            st.success("Registration Successful and Saved permanently! Please log in now.")


# ==========================================
# 4. MAIN DASHBOARD & CONTROLLER
# ==========================================
def main_app():
    user_id = st.session_state["current_user"]
    users = st.session_state["db_users"]
    user = users[user_id]
    
    # ----------------------------------
    # BLOCKED USER HANDLING
    # ----------------------------------
    if user["is_blocked"]:
        st.error("⛔ YOUR ACCOUNT IS BLOCKED BY THE ADMIN.")
        
        st.subheader("💬 Last Word Privilege")
        if not user["last_word_used"]:
            last_msg = st.text_area("Send your final message to Superadmin:")
            if st.button("Send Final Message"):
                if last_msg:
                    user["last_word_used"] = True
                    sa = [u for u, d in users.items() if d["role"] == "Superadmin"][0]
                    if sa not in st.session_state["db_private_chats"]:
                        st.session_state["db_private_chats"][sa] = []
                    st.session_state["db_private_chats"][sa].append({
                        "sender": f"BLOCKED_USER ({user_id})",
                        "text": f"LAST WORD: {last_msg}",
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    save_db()
                    st.success("Final message sent!")
                    st.rerun()
        else:
            st.info("You have already used your single last word privilege.")

        st.write("---")
        st.subheader("🚩 Fair-Play Block Audit Request")
        blocker = st.selectbox("Who blocked you?", [u for u, d in users.items() if d["role"] in ["Superadmin", "Admin"]])
        reason = st.text_area("Explain why this block is completely unfair:")
        
        if st.button("Audit Block via Personal AI"):
            if len(reason.strip()) > 10:
                user["is_blocked"] = False
                users[blocker]["penalty_points"] += 5
                save_db()
                st.success(f"🤖 {user['personal_ai_name']} Audit: Block found UNJUSTIFIED! You are unblocked, and {blocker} received -5 points penalty.")
                st.rerun()
            else:
                st.error("Audit rejected: Insufficient explanation.")
                
        if st.button("Logout"):
            st.session_state["current_user"] = None
            st.rerun()
        return

    # Header Bar & Logo
    c1, c2, c3 = st.columns([1, 4, 1.5])
    with c1:
        logo_b64 = st.session_state["db_app_config"].get("logo_b64", "")
        if logo_b64:
            st.markdown(f'<img src="{logo_b64}" width="70" style="border-radius:10px;">', unsafe_allow_html=True)
        else:
            st.title("⚽")
    with c2:
        st.title(st.session_state["db_app_config"]["app_name"])
    with c3:
        st.write(f"Logged in: **{user['jersey_name']}**")
        st.caption(f"Role: {user['role']} | Jersey: #{user['jersey_no']}")
        if st.button("Logout"):
            st.session_state["current_user"] = None
            st.rerun()

    # Sidebar Navigation
    st.sidebar.title("📌 Navigation Menu")
    menu = st.sidebar.radio("Go To", [
        "📢 Notice Board",
        "👥 Player Directory",
        "💬 WhatsApp Chat Lounge",
        "⚽ Squad & Captain Engine",
        "📊 Ratings, Fouls & Corrections",
        "👤 My Profile & Settings",
        "⭐ Sunday MOTM Poll",
        "⚙️ Admin Panels"
    ])

    # --------------------------------------------------
    # MENU 1: NOTICE BOARD
    # --------------------------------------------------
    if menu == "📢 Notice Board":
        st.header("📢 Club Notice Board")
        
        # Post Notice Option for Superadmin/Admin
        if user["role"] in ["Superadmin", "Admin"]:
            with st.expander("📝 Post New Notice (Admin / S.A Privilege)"):
                n_title = st.text_input("Notice Title")
                n_body = st.text_area("Notice Details")
                if st.button("Publish Notice"):
                    if n_title and n_body:
                        push_notice(n_title, n_body, f"{user['role']} ({user_id})")
                        st.success("Notice Published!")
                        st.rerun()
                        
        if not st.session_state["db_notices"]:
            st.info("No notices posted yet.")
        for n in st.session_state["db_notices"]:
            st.markdown(f"""
            <div class="content-card">
                <h3>{n['title']}</h3>
                <p><small>Posted by <b>{n['author']}</b> on {n['date']}</small></p>
                <hr>
                <p>{n['body']}</p>
            </div>
            """, unsafe_allow_html=True)

    # --------------------------------------------------
    # MENU 2: PLAYER DIRECTORY
    # --------------------------------------------------
    elif menu == "👥 Player Directory":
        st.header("👥 ASMB Public Player Directory")
        dir_list = []
        for u, d in users.items():
            dir_list.append({
                "Username": u,
                "Full Name": d["full_name"],
                "Jersey No": d["jersey_no"],
                "Jersey Name": d["jersey_name"],
                "Position": d["position"],
                "Role": d["role"],
                "Rating": calculate_net_rating(u),
                "Star Player": "⭐ YES" if is_star_player(u) else "NO",
                "Injured": "🚑 YES" if d["is_injured"] else "NO"
            })
        st.dataframe(pd.DataFrame(dir_list), use_container_width=True)

    # --------------------------------------------------
    # MENU 3: WHATSAPP STYLE CHAT LOUNGE
    # --------------------------------------------------
    elif menu == "💬 WhatsApp Chat Lounge":
        st.header("💬 WhatsApp-Style Chat Hub")
        chat_tab1, chat_tab2 = st.tabs(["🌐 Public Club Chat (Group)", f"🔒 Private Personal AI ({user['personal_ai_name']})"])
        
        # Public Group Chat
        with chat_tab1:
            st.subheader("🌐 Public Group Chat")
            
            chat_container = st.container()
            with chat_container:
                for c in st.session_state["db_public_chat"]:
                    is_me = c["user"] == user_id
                    bubble_class = "chat-bubble-user" if is_me else "chat-bubble-ai"
                    st.markdown(f"""
                    <div class="{bubble_class}">
                        <b>{c['user']}:</b> {c['question']}<br>
                        <div style="margin-top: 5px; color: #008000;">🤖 <b>Football AI:</b> {c['ai_response']}</div>
                        <div class="chat-meta">{c['timestamp']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.write("---")
            pub_msg = st.text_input("Type your message (Supports Bangla/English):", key="pub_msg_input")
            if st.button("Send Message"):
                if pub_msg:
                    ai_reply = generate_ai_response(pub_msg, "Football AI")
                    st.session_state["db_public_chat"].append({
                        "user": user_id,
                        "question": pub_msg,
                        "ai_response": ai_reply,
                        "timestamp": datetime.datetime.now().strftime("%I:%M %p")
                    })
                    save_db()
                    st.rerun()

        # Private Personal AI Chat
        with chat_tab2:
            st.subheader(f"🔒 Confidential AI: {user['personal_ai_name']}")
            
            p_chats = st.session_state["db_private_chats"].get(user_id, [])
            for pc in p_chats:
                is_user = pc["sender"] == user_id
                bubble_class = "chat-bubble-user" if is_user else "chat-bubble-ai"
                st.markdown(f"""
                <div class="{bubble_class}">
                    <b>{pc['sender']}:</b> {pc['text']}
                    <div class="chat-meta">{pc['timestamp']}</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.write("---")
            priv_msg = st.text_input(f"Chat privately with {user['personal_ai_name']}:", key="priv_msg_input")
            if st.button("Send Private Message"):
                if priv_msg:
                    if user_id not in st.session_state["db_private_chats"]:
                        st.session_state["db_private_chats"][user_id] = []
                        
                    now_str = datetime.datetime.now().strftime("%I:%M %p")
                    # User Msg
                    st.session_state["db_private_chats"][user_id].append({
                        "sender": user_id,
                        "text": priv_msg,
                        "timestamp": now_str
                    })
                    # AI Reply
                    ai_resp = generate_ai_response(priv_msg, user["personal_ai_name"])
                    st.session_state["db_private_chats"][user_id].append({
                        "sender": f"🤖 {user['personal_ai_name']}",
                        "text": ai_resp,
                        "timestamp": now_str
                    })
                    save_db()
                    st.rerun()

    # --------------------------------------------------
    # MENU 4: SQUAD & CAPTAIN ENGINE
    # --------------------------------------------------
    elif menu == "⚽ Squad & Captain Engine":
        st.header("⚽ Automated Squad & Captain Generator")
        
        if user["role"] in ["Superadmin", "Admin"]:
            st.subheader("🛠️ Match / Practice Day Squad Builder")
            squad_type = st.radio("Select Match Type", ["Match Day (1 Main Squad)", "Practice Day (2 Balanced Equal Teams)"])
            player_count = st.number_input("How many players will play total (kotojon khelbe)?", min_value=2, max_value=30, value=11)
            
            if st.button("Generate Squads & Appoint Captain"):
                active_p = [u for u, d in users.items() if not d["is_blocked"] and not d["is_injured"]]
                if len(active_p) < 2:
                    st.warning("Not enough active players to form a squad!")
                else:
                    # Sort active players by rating descending
                    active_p.sort(key=lambda u: calculate_net_rating(u), reverse=True)
                    
                    if squad_type == "Practice Day (2 Balanced Equal Teams)":
                        # Balanced Team Split (Snake Draft)
                        team_a, team_b = [], []
                        for idx, p in enumerate(active_p[:player_count]):
                            if idx % 2 == 0: team_a.append(p)
                            else: team_b.append(p)
                            
                        sum_a = sum(calculate_net_rating(p) for p in team_a)
                        sum_b = sum(calculate_net_rating(p) for p in team_b)
                        
                        cap_a = team_a[0]
                        cap_b = team_b[0]
                        
                        body = f"### ⚽ Practice Day Balanced Squads\n"
                        body += f"**Team Alpha (Avg Rating: {round(sum_a/len(team_a), 2)}):**\n"
                        for p in team_a:
                            cap_tag = "👑 CAPTAIN" if p == cap_a else ""
                            body += f"- {users[p]['jersey_name']} ({users[p]['position']}) - Rating: {calculate_net_rating(p)} {cap_tag}\n"
                            
                        body += f"\n**Team Beta (Avg Rating: {round(sum_b/len(team_b), 2)}):**\n"
                        for p in team_b:
                            cap_tag = "👑 CAPTAIN" if p == cap_b else ""
                            body += f"- {users[p]['jersey_name']} ({users[p]['position']}) - Rating: {calculate_net_rating(p)} {cap_tag}\n"
                            
                        push_notice("Practice Squad Announcement", body, "Football AI")
                        st.success("Practice Squads published to Notice Board!")
                        
                    else:
                        # Match Day Squad
                        selected = active_p[:player_count]
                        subs = active_p[player_count:]
                        captain = selected[0] # Highest rated player is captain
                        
                        body = f"### 🏆 Official Match Day Squad Announcement\n"
                        body += f"**👑 Team Captain:** {users[captain]['jersey_name']} (Rating: {calculate_net_rating(captain)})\n\n"
                        body += "**Starting Lineup:**\n"
                        for idx, p in enumerate(selected, 1):
                            cap_tag = "👑 (C)" if p == captain else ""
                            body += f"{idx}. {users[p]['jersey_name']} [{users[p]['position']}] - Rating: {calculate_net_rating(p)} {cap_tag}\n"
                            
                        if subs:
                            body += "\n**Substitutes:**\n"
                            for idx, p in enumerate(subs, 1):
                                body += f"Sub {idx}: {users[p]['jersey_name']} - Rating: {calculate_net_rating(p)}\n"
                                
                        push_notice("Official Match Day Squad", body, "Football AI")
                        st.success("Match Day Squad & Captain Published!")
        else:
            st.info("Squad generation is managed exclusively by Superadmin & Admins.")

    # --------------------------------------------------
    # MENU 5: RATINGS, FOULS & CORRECTIONS
    # --------------------------------------------------
    elif menu == "📊 Ratings, Fouls & Corrections":
        st.header("📊 Player Rating & Foul Entry")
        
        st.subheader("✍️ Submit / Update Your Given Ratings")
        st.caption("You can update or change your submitted ratings at any time.")
        
        other_players = [u for u in users.keys() if u != user_id]
        if other_players:
            target = st.selectbox("Select Player to Rate", other_players)
            
            # Key for rating DB: "target_user::rater_user"
            rate_key = f"{target}::{user_id}"
            
            existing_rat = st.session_state["db_ratings"].get(rate_key, 7.0)
            existing_foul = st.session_state["db_fouls"].get(rate_key, 0.0)
            
            new_rat = st.slider("Assign Rating (1.0 - 10.0)", 1.0, 10.0, float(existing_rat), step=0.1)
            new_foul = st.slider("Assign Foul Impact (0.0 - 10.0)", 0.0, 10.0, float(existing_foul), step=0.5)
            
            if st.button("Save / Update Rating & Foul"):
                st.session_state["db_ratings"][rate_key] = new_rat
                st.session_state["db_fouls"][rate_key] = new_foul
                save_db()
                st.success(f"Rating for {target} updated successfully to {new_rat}!")
                
        st.write("---")
        st.subheader("✏️ Admin Override & Stats Correction")
        if user["role"] in ["Superadmin", "Admin"]:
            edit_p = st.selectbox("Select Player to Edit Stats", list(users.keys()))
            p_goals = st.number_input("Goals", value=users[edit_p]["goals"])
            p_assists = st.number_input("Assists", value=users[edit_p]["assists"])
            p_og = st.number_input("Own Goals", value=users[edit_p]["own_goals"])
            
            if st.button("Save Stats Override"):
                users[edit_p]["goals"] = p_goals
                users[edit_p]["assists"] = p_assists
                users[edit_p]["own_goals"] = p_og
                save_db()
                st.success(f"Stats for {edit_p} saved successfully!")

    # --------------------------------------------------
    # MENU 6: MY PROFILE & SETTINGS
    # --------------------------------------------------
    elif menu == "👤 My Profile & Settings":
        st.header("👤 Player Profile Settings")
        st.caption("You can edit and update your own personal information here.")
        
        with st.form("edit_profile_form"):
            e_fullname = st.text_input("Full Name", value=user["full_name"])
            e_jersey_no = st.number_input("Jersey Number", min_value=1, max_value=99, value=int(user["jersey_no"]))
            e_jersey_name = st.text_input("Jersey Name", value=user["jersey_name"])
            e_ai_name = st.text_input("Personal AI Name", value=user["personal_ai_name"])
            e_password = st.text_input("Change Password", value=user["password"], type="password")
            
            if st.form_submit_button("Update My Information"):
                user["full_name"] = e_fullname
                user["jersey_no"] = e_jersey_no
                user["jersey_name"] = e_jersey_name
                user["personal_ai_name"] = e_ai_name
                user["password"] = e_password
                save_db()
                st.success("Your profile details have been successfully updated and saved!")

    # --------------------------------------------------
    # MENU 7: SUNDAY MOTM POLL
    # --------------------------------------------------
    elif menu == "⭐ Sunday MOTM Poll":
        st.header("⭐ Sunday Man of the Match Poll")
        
        today_str = datetime.datetime.now().strftime("%A")
        if today_str == "Sunday":
            st.subheader(f"🤖 {user['personal_ai_name']} Query:")
            st.write("**'Who is the Man of the Match today?'**")
            
            candidates = [u for u, d in users.items() if not d["is_blocked"]]
            motm_pick = st.selectbox("Vote MOTM Player:", candidates)
            
            if st.button("Submit MOTM Vote"):
                st.session_state["db_motm_votes"][user_id] = motm_pick
                save_db()
                st.success("Your MOTM vote has been saved!")
                
            if user["role"] in ["Superadmin", "Admin"]:
                st.write("---")
                if st.button("Publish Final MOTM Winner"):
                    votes = list(st.session_state["db_motm_votes"].values())
                    if votes:
                        winner = max(set(votes), key=votes.count)
                        push_notice("🏆 Sunday Man of the Match Result", f"The MOTM Winner is **{users[winner]['full_name']} ({winner})**!", "Football AI")
                        st.success("MOTM Result Published!")
                    else:
                        st.warning("No votes recorded yet.")
        else:
            st.info("Automated MOTM poll runs exclusively on Sundays.")

    # --------------------------------------------------
    # MENU 8: ADMIN PANELS
    # --------------------------------------------------
    elif menu == "⚙️ Admin Panels":
        st.header("⚙️ Admin & Superadmin Management")
        
        # Club Photo & Branding Upload
        st.subheader("🖼️ Club Photo & Branding Customization")
        c_name = st.text_input("App / Club Name", value=st.session_state["db_app_config"]["app_name"])
        logo_file = st.file_uploader("Upload New Club Photo / Logo", type=["png", "jpg", "jpeg"])
        
        if st.button("Save Club Photo & Branding"):
            st.session_state["db_app_config"]["app_name"] = c_name
            if logo_file is not None:
                bytes_data = logo_file.read()
                b64 = base64.b64encode(bytes_data).decode("utf-8")
                st.session_state["db_app_config"]["logo_b64"] = f"data:image/png;base64,{b64}"
            save_db()
            st.success("Branding & Club Photo updated!")
            st.rerun()
            
        st.write("---")
        
        # Superadmin Specific Control Panel
        if user["role"] == "Superadmin":
            st.subheader("👑 Superadmin Admin & Block Panel")
            target_usr = st.selectbox("Select Target User", list(users.keys()))
            
            ca, cb, cc, cd = st.columns(4)
            with ca:
                if st.button("Promote to Admin"):
                    users[target_usr]["role"] = "Admin"
                    save_db()
                    st.success(f"{target_usr} promoted to Admin.")
            with cb:
                if st.button("Dismiss Admin"):
                    users[target_usr]["role"] = "Player"
                    save_db()
                    st.success(f"{target_usr} demoted.")
            with cc:
                if st.button("Block User"):
                    users[target_usr]["is_blocked"] = True
                    save_db()
                    st.success(f"{target_usr} blocked.")
            with cd:
                if st.button("Unblock User"):
                    users[target_usr]["is_blocked"] = False
                    save_db()
                    st.success(f"{target_usr} unblocked.")

            st.write("---")
            st.subheader("📌 Manual Position Assignment")
            pos_u = st.selectbox("User for Position Edit", list(users.keys()), key="pos_u_select")
            new_p_pos = st.selectbox("Assign Position", ["Goalkeeper (GK)", "Defender (CB)", "Midfielder (CM)", "Forward (ST)"])
            if st.button("Save Position"):
                users[pos_u]["position"] = new_p_pos
                save_db()
                st.success(f"Position updated for {pos_u}.")

            st.write("---")
            st.subheader("🔴 Danger Zone")
            st.caption("Deletes AI chats, group chats, notices & rating records WITHOUT deleting User Accounts.")
            if st.button("🔥 MASTER RESET / REFRESH"):
                st.session_state["db_notices"] = []
                st.session_state["db_public_chat"] = []
                st.session_state["db_private_chats"] = {}
                st.session_state["db_ratings"] = {}
                st.session_state["db_fouls"] = {}
                st.session_state["db_motm_votes"] = {}
                save_db()
                st.success("Master Reset Complete! All chats, notices, and ratings cleared while User IDs remain intact.")
                st.rerun()
        else:
            st.info("Superadmin features are locked.")


# ==========================================
# 5. ENTRY POINT
# ==========================================
if st.session_state["current_user"] is None:
    auth_ui()
else:
    main_app()