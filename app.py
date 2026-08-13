import streamlit as st
import json
import os
import datetime
import re
import random

# ==========================================
# 0. STREAMLIT PAGE CONFIG & DATA STORAGE
# ==========================================
st.set_page_config(
    page_title="Football Club Management",
    page_icon="⚽",
    layout="wide"
)

DATA_FILE = "data.json"

def load_data_from_file():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def save_data_to_file():
    data = {
        "users": st.session_state.users,
        "blocked_users": st.session_state.blocked_users,
        "player_stats": st.session_state.player_stats,
        "app_settings": st.session_state.app_settings,
        "match_settings": st.session_state.match_settings,
        "notice_board": st.session_state.notice_board,
        "match_poll": st.session_state.match_poll,
        "gk_saves": st.session_state.gk_saves,
        "injured_players": st.session_state.injured_players,
        "motm_votes": st.session_state.motm_votes,
        "group_chat": st.session_state.group_chat,
        "personal_ai_chats": st.session_state.personal_ai_chats,
        "football_ai_chats": st.session_state.football_ai_chats
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# SESSION STATE INITIALIZATION
saved_data = load_data_from_file()

if saved_data:
    st.session_state.users = saved_data.get("users", {})
    st.session_state.blocked_users = saved_data.get("blocked_users", {})
    st.session_state.player_stats = saved_data.get("player_stats", {})
    st.session_state.app_settings = saved_data.get("app_settings", {
        "app_name": "Phoenix Stars FC",
        "bg_color": "#1E293B",
        "club_photo": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2",
        "max_registration_limit": 30
    })
    st.session_state.match_settings = saved_data.get("match_settings", {
        "asmb_player_count": 11,
        "formation": "4-3-3"
    })
    st.session_state.notice_board = saved_data.get("notice_board", [])
    st.session_state.match_poll = saved_data.get("match_poll", {})
    st.session_state.gk_saves = saved_data.get("gk_saves", {})
    st.session_state.injured_players = saved_data.get("injured_players", [])
    st.session_state.motm_votes = saved_data.get("motm_votes", {})
    st.session_state.group_chat = saved_data.get("group_chat", [])
    st.session_state.personal_ai_chats = saved_data.get("personal_ai_chats", {})
    st.session_state.football_ai_chats = saved_data.get("football_ai_chats", {})
else:
    st.session_state.users = {
        "superadmin": {
            "full_name": "Super Admin",
            "password": "admin",
            "role": "Superadmin",
            "position": "CAM",
            "photo": "",
            "sec_question": "What is the club name?",
            "sec_answer": "phoenix"
        }
    }
    st.session_state.blocked_users = {}
    st.session_state.player_stats = {
        "superadmin": {"goals": 0, "assists": 0, "rating": 10.0, "attendance": "Present", "motm_count": 5}
    }
    st.session_state.app_settings = {
        "app_name": "Phoenix Stars FC",
        "bg_color": "#0F172A",
        "club_photo": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2",
        "max_registration_limit": 30
    }
    st.session_state.match_settings = {"asmb_player_count": 11, "formation": "4-3-3"}
    st.session_state.notice_board = []
    st.session_state.match_poll = {}
    st.session_state.gk_saves = {}
    st.session_state.injured_players = []
    st.session_state.motm_votes = {}
    st.session_state.group_chat = []
    st.session_state.personal_ai_chats = {}
    st.session_state.football_ai_chats = {}
    save_data_to_file()

if "logged_user" not in st.session_state:
    st.session_state.logged_user = None

# ==========================================
# HELPER FUNCTIONS & AI ENGINE
# ==========================================
def get_contrast_color(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return "#FFFFFF"
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    inv_r, inv_g, inv_b = 255 - r, 255 - g, 255 - b
    return f"#{inv_r:02x}{inv_g:02x}{inv_b:02x}"

def check_link_in_text(text):
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    return bool(url_pattern.search(text))

def respond_personal_ai(prompt, user_name):
    if check_link_in_text(prompt):
        return "⚠️ দুঃখিত, আমি কোনো ওয়েবসাইট বা ভিডিও লিংক পড়ে বিশ্লেষণ করতে পারি না।"
    return f"হ্যালো {user_name}! আমি আপনার পার্সোনাল AI অ্যাসিস্ট্যান্ট। আপনার প্রশ্নটি পেয়েছি। আমি সর্বদা বাংলা ভাষায় আপনার তথ্য ও পারফরম্যান্স ট্র্যাক করে সাহায্য করতে প্রস্তুত।"

def respond_football_ai(prompt):
    if check_link_in_text(prompt):
        return "⚠️ দুঃখিত, কোনো ওয়েবলিংকের বিষয়বস্তু বিশ্লেষণ করা আমার পক্ষে সম্ভব নয়।"
    
    football_keywords = ["tactics", "formation", "match", "squad", "goal", "pass", "dribble", "football", "খেলার", "ফুটবল", "গোল", "স্কোয়াড", "পজিশন", "ট্যাকটিক্স", "ডিফেন্স", "অ্যাটাক", "সেভ", "gk"]
    if not any(k in prompt.lower() for k in football_keywords):
        return "REDIRECT_PERSONAL"
        
    return "ফুটবল ট্যাকটিক্স অ্যান্ড ফরমেশন অ্যানালাইসিস: ম্যাচের ফর্মেশন, প্রেসিং এবং পজিশনিং বজায় রাখা যেকোনো বিজয়ী দলের মূল চাবিকাঠি।"

# ==========================================
# DYNAMIC CLUB HEADER (REQ 23)
# ==========================================
bg_col = st.session_state.app_settings.get("bg_color", "#0F172A")
text_col = get_contrast_color(bg_col)

st.markdown(f"""
    <div style="background-color: {bg_col}; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 25px;">
        <h1 style="color: {text_col}; margin: 0;">⚽ {st.session_state.app_settings['app_name']} ⚽</h1>
    </div>
""", unsafe_allow_stdio=True)

# ==========================================
# LOGIN & REGISTER SYSTEM (REQ 2, 8, 20)
# ==========================================
if not st.session_state.logged_user:
    tab_login, tab_reg, tab_forget = st.tabs(["🔑 Login", "📝 Register Player", "❓ Forgot Password"])
    
    with tab_login:
        st.subheader("Login to your Account")
        l_user = st.text_input("Username:", key="log_u").strip().lower()
        l_pass = st.text_input("Password:", type="password", key="log_p")
        
        if st.button("Login", key="btn_login_exec"):
            # REQ 14: Blocked ID login constraint
            if l_user in st.session_state.blocked_users:
                st.error("⛔ Your Account has been Blocked by the Administration.")
            elif l_user in st.session_state.users and st.session_state.users[l_user]["password"] == l_pass:
                # REQ 2: Force Security Question for Older Registered Users
                user_data = st.session_state.users[l_user]
                if "sec_question" not in user_data or not user_data["sec_question"]:
                    st.session_state.temp_login_user = l_user
                    st.warning("⚠️ নিরাপত্তার স্বার্থে আপনার অ্যাকাউন্টে পাসওয়ার্ড রিকভারি তথ্য সেটিং করা বাধ্যতামূলক!")
                    st.rerun()
                else:
                    st.session_state.logged_user = l_user
                    st.success("Log in successful!")
                    st.rerun()
            else:
                st.error("Invalid Username or Password.")

    # REQ 2 FORCE POPUP FOR OLD USERS
    if "temp_login_user" in st.session_state and st.session_state.temp_login_user:
        st.warning("🔐 রিকভারি প্রশ্ন ও উত্তর সেটআপ করুন (এটি ছাড়া ভেতরে প্রবেশ করা যাবে না):")
        with st.form("force_sec_form"):
            fq = st.text_input("Security Question (e.g., Your favorite club?):")
            fa = st.text_input("Security Answer:")
            if st.form_submit_button("Save & Complete Login"):
                if fq.strip() and fa.strip():
                    st.session_state.users[st.session_state.temp_login_user]["sec_question"] = fq.strip()
                    st.session_state.users[st.session_state.temp_login_user]["sec_answer"] = fa.strip().lower()
                    st.session_state.logged_user = st.session_state.temp_login_user
                    st.session_state.temp_login_user = None
                    save_data_to_file()
                    st.success("সেটআপ সম্পন্ন হয়েছে!")
                    st.rerun()
                else:
                    st.error("সবগুলো ঘর সঠিকভাবে পূরণ করুন!")

    with tab_reg:
        st.subheader("Register New Player Account")
        # REQ 20: Blocked players not counted in registration limit
        active_user_count = len([u for u in st.session_state.users if u not in st.session_state.blocked_users])
        max_limit = st.session_state.app_settings.get("max_registration_limit", 30)
        
        if active_user_count >= max_limit:
            st.error(f"⛔ Registration Closed. Maximum player limit ({max_limit}) reached!")
        else:
            r_user = st.text_input("Desired Username:", key="reg_u").strip().lower()
            r_fname = st.text_input("Full Name:", key="reg_fn")
            r_pass = st.text_input("Password:", type="password", key="reg_p")
            r_pos = st.selectbox("Preferred Position:", ["GK", "CB", "LB", "RB", "CM", "CAM", "RW", "LW", "ST"], key="reg_pos")
            r_photo = st.text_input("Profile Photo URL (Optional):", key="reg_pic")
            
            # REQ 2: Recovery details during registration
            st.markdown("**🔐 Forgot Password Recovery Setup:**")
            r_sec_q = st.text_input("Security Question:", placeholder="e.g., What was your first pet's name?")
            r_sec_a = st.text_input("Security Answer:", placeholder="Your answer here").strip().lower()
            
            if st.button("Register Player", key="btn_reg_exec"):
                if not r_user or not r_pass or not r_fname or not r_sec_q or not r_sec_a:
                    st.error("Please fill in all mandatory fields including security details!")
                elif r_user in st.session_state.users or r_user in st.session_state.blocked_users:
                    st.error("Username already taken!")
                else:
                    st.session_state.users[r_user] = {
                        "full_name": r_fname,
                        "password": r_pass,
                        "role": "Player",
                        "position": r_pos,
                        "photo": r_photo,
                        "sec_question": r_sec_q,
                        "sec_answer": r_sec_a
                    }
                    st.session_state.player_stats[r_user] = {
                        "goals": 0, "assists": 0, "rating": 6.0, "attendance": "Absent", "motm_count": 0
                    }
                    save_data_to_file()
                    st.success("Account registered successfully! You can now login.")

    with tab_forget:
        # REQ 2: Forgot Password Recovery Feature
        st.subheader("Reset Forgotten Password")
        fp_user = st.text_input("Enter your Username:", key="fp_u").strip().lower()
        if fp_user in st.session_state.users:
            u_info = st.session_state.users[fp_user]
            st.info(f"Security Question: **{u_info.get('sec_question', 'N/A')}**")
            ans_input = st.text_input("Your Answer:", key="fp_ans").strip().lower()
            new_fp_pass = st.text_input("New Password:", type="password", key="fp_np")
            
            if st.button("Reset Password", key="btn_reset_pass_user"):
                if ans_input == u_info.get("sec_answer", ""):
                    st.session_state.users[fp_user]["password"] = new_fp_pass
                    save_data_to_file()
                    st.success("Password updated successfully! Please login with your new password.")
                else:
                    st.error("Incorrect security answer!")
        elif fp_user:
            st.error("Username not found!")
    st.stop()

# ==========================================
# LOGGED IN DASHBOARD
# ==========================================
curr_username = st.session_state.logged_user
curr_user = st.session_state.users[curr_username]

# SIDEBAR NAVIGATION
st.sidebar.markdown(f"### 👋 Welcome, {curr_user['full_name']}")
st.sidebar.text(f"Role: {curr_user['role']} | Pos: {curr_user['position']}")
if curr_user.get("photo"):
    st.sidebar.image(curr_user["photo"], width=120)

# REQ 17: Admin Panel Visible strictly to Superadmin/Admin
nav_options = [
    "📌 Notice Board & Poll",
    "👤 Edit My Profile",
    "📸 Player Gallery",
    "📊 Squad & Matchday Engine",
    "💬 Group Chat",
    "👤 Personal AI (Private)",
    "⚽ Football AI (Tactics)"
]
if curr_user["role"] in ["Superadmin", "Admin"]:
    nav_options.append("⚙️ Admin Control Panel")

nav_choice = st.sidebar.radio("Navigation:", nav_options)

if st.sidebar.button("Logout 🚪"):
    st.session_state.logged_user = None
    st.rerun()

# ==========================================
# REQ 4 & 5: MATCHDAY POLL POPUP
# ==========================================
st.sidebar.divider()
st.sidebar.markdown("### 📅 Matchday Participation Poll")
poll_choice = st.sidebar.radio("Will you attend tomorrow's match?", ["Not Selected", "Yes", "No"], index=0 if curr_username not in st.session_state.match_poll else (1 if st.session_state.match_poll[curr_username] == "Yes" else 2))

if poll_choice != "Not Selected":
    st.session_state.match_poll[curr_username] = poll_choice
    # REQ 5: Attendance depends on Yes/No poll
    st.session_state.player_stats[curr_username]["attendance"] = "Present" if poll_choice == "Yes" else "Absent"
    save_data_to_file()

# ==========================================
# 1. FEATURE MODULE: NOTICE BOARD & POLL
# ==========================================
if nav_choice == "📌 Notice Board & Poll":
    st.header("📌 Official Announcements & Matchday Poll Status")
    
    # REQ 9: Club Photo Display
    if st.session_state.app_settings.get("club_photo"):
        st.image(st.session_state.app_settings["club_photo"], caption=f"{st.session_state.app_settings['app_name']} Official Club Photo", use_container_width=True)
        
    st.divider()
    st.subheader("📢 Active Notices")
    if not st.session_state.notice_board:
        st.info("No active notices.")
    else:
        for n in reversed(st.session_state.notice_board):
            st.markdown(f"### {n['title']}")
            st.caption(f"Posted by {n['author']} on {n['timestamp']}")
            st.write(n['content'])
            st.divider()

# ==========================================
# 2. FEATURE MODULE: EDIT PROFILE (REQ 3)
# ==========================================
elif nav_choice == "👤 Edit My Profile":
    st.header("👤 Edit Profile Information")
    st.caption("You can update all your profile details except your assigned position.")
    
    # REQ 3: Edit everything except position
    st.text_input("Position (Locked by Admin):", value=curr_user["position"], disabled=True)
    up_fn = st.text_input("Full Name:", value=curr_user["full_name"])
    up_pass = st.text_input("New Password:", value=curr_user["password"], type="password")
    up_photo = st.text_input("Profile Photo URL:", value=curr_user.get("photo", ""))
    up_sq = st.text_input("Security Question:", value=curr_user.get("sec_question", ""))
    up_sa = st.text_input("Security Answer:", value=curr_user.get("sec_answer", ""))
    
    if st.button("Save Profile Changes"):
        curr_user["full_name"] = up_fn
        curr_user["password"] = up_pass
        curr_user["photo"] = up_photo
        curr_user["sec_question"] = up_sq
        curr_user["sec_answer"] = up_sa.strip().lower()
        save_data_to_file()
        st.success("Profile updated successfully!")
        st.rerun()

# ==========================================
# 3. FEATURE MODULE: PLAYER GALLERY (REQ 21, 22)
# ==========================================
elif nav_choice == "📸 Player Gallery":
    st.header("📸 Official Player Photo Gallery")
    st.caption("Registered players with profile photos are highlighted here.")
    
    # REQ 22: Highest MOTM winner is always Star Player regardless of rating
    all_active = [u for u in st.session_state.users if u not in st.session_state.blocked_users]
    top_motm_user = max(all_active, key=lambda x: st.session_state.player_stats[x].get("motm_count", 0)) if all_active else None
    
    if top_motm_user and st.session_state.player_stats[top_motm_user].get("motm_count", 0) > 0:
        st.markdown(f"### ⭐ Star Player of the Club: **{st.session_state.users[top_motm_user]['full_name']}** (@{top_motm_user})")
        st.caption("Awarded for achieving the highest Man of the Match (MOTM) titles!")
        st.divider()

    # REQ 21: Dedicated Photo + Username Display Site
    cols = st.columns(4)
    idx = 0
    for uname in all_active:
        uinfo = st.session_state.users[uname]
        if uinfo.get("photo"):
            with cols[idx % 4]:
                st.image(uinfo["photo"], use_container_width=True)
                st.markdown(f"**@{uname}**")
                st.caption(f"{uinfo['full_name']} ({uinfo['position']})")
            idx += 1

# ==========================================
# 4. FEATURE MODULE: SQUAD & MATCHDAY ENGINE (REQ 7, 16, 18, 19, 22)
# ==========================================
elif nav_choice == "📊 Squad & Matchday Engine":
    st.header("📊 Squad Formation & Matchday Roster")
    
    # REQ 18: Squad can only be generated by Superadmin/Admin
    if curr_user["role"] in ["Superadmin", "Admin"]:
        st.subheader("⚙️ Generate Automated Balanced Squad")
        if st.button("🚀 Generate Match Squad"):
            squad_limit = st.session_state.match_settings.get("asmb_player_count", 11)
            
            # Filter available players (Yes in Poll, not injured, not blocked)
            eligible = []
            for u in all_active:
                if u in st.session_state.injured_players:
                    continue
                if st.session_state.match_poll.get(u) == "Yes":
                    # REQ 6: GK save count adds to rating
                    p_rating = st.session_state.player_stats[u]["rating"]
                    if st.session_state.users[u]["position"] == "GK":
                        p_rating += (st.session_state.gk_saves.get(u, 0) * 0.2)
                    eligible.append((u, st.session_state.users[u]["position"], p_rating))
            
            # REQ 7: No duplicate position in squad - pick highest rated player for each position
            position_map = {}
            for u, pos, rating in sorted(eligible, key=lambda x: x[2], reverse=True):
                if pos not in position_map:
                    position_map[pos] = u
            
            selected_squad = list(position_map.values())[:squad_limit]
            st.session_state.current_squad = selected_squad
            save_data_to_file()
            st.success("Squad generated successfully!")

    st.divider()
    st.subheader(f"📋 Final Match Squad (Formation: {st.session_state.match_settings.get('formation', '4-3-3')})")
    
    curr_sq = st.session_state.get("current_squad", [])
    if not curr_sq:
        st.info("No squad generated for the upcoming matchday yet.")
    else:
        for p_u in curr_sq:
            p_data = st.session_state.users[p_u]
            st.markdown(f"• **{p_data['full_name']}** (@{p_u}) - Position: `{p_data['position']}` | Rating: `{st.session_state.player_stats[p_u]['rating']}`")

    st.divider()
    st.subheader("🏥 Injured Player List")
    if not st.session_state.injured_players:
        st.write("No injured players reported.")
    else:
        for iu in st.session_state.injured_players:
            st.markdown(f"❌ **{st.session_state.users[iu]['full_name']}** (@{iu}) - Unavailable")

# ==========================================
# 5. FEATURE MODULE: GROUP CHAT
# ==========================================
elif nav_choice == "💬 Group Chat":
    st.header("💬 Club Public Group Chat")
    
    for msg in st.session_state.group_chat:
        st.markdown(f"**{msg['sender']}** ({msg['time']}): {msg['text']}")
        
    chat_input = st.text_input("Type your message:", key="gc_in")
    if st.button("Send Message", key="btn_send_gc"):
        if chat_input.strip():
            st.session_state.group_chat.append({
                "sender": f"{curr_user['full_name']} (@{curr_username})",
                "text": chat_input.strip(),
                "time": datetime.datetime.now().strftime("%H:%M")
            })
            save_data_to_file()
            st.rerun()

# ==========================================
# 6. FEATURE MODULE: PERSONAL AI (REQ 1, 11, 12)
# ==========================================
elif nav_choice == "👤 Personal AI (Private)":
    st.header("👤 Personal AI Assistant (Private)")
    st.caption("🔒 Ask anything freely. Your personal AI responds fluently in Bangla.")
    
    user_p_chats = st.session_state.personal_ai_chats.setdefault(curr_username, [])
    
    for c in user_p_chats:
        st.markdown(f"**You:** {c['prompt']}")
        st.markdown(f"🤖 **Personal AI:** {c['response']}")
        st.divider()
        
    p_prompt = st.text_input("Ask Personal AI:", key="in_pai")
    if st.button("Ask Personal AI", key="btn_pai"):
        if p_prompt.strip():
            resp = respond_personal_ai(p_prompt.strip(), curr_user["full_name"])
            user_p_chats.append({"prompt": p_prompt.strip(), "response": resp})
            save_data_to_file()
            st.rerun()

# ==========================================
# 7. FEATURE MODULE: FOOTBALL AI (REQ 1, 11, 12, 13)
# ==========================================
elif nav_choice == "⚽ Football AI (Tactics)":
    st.header("⚽ Football AI (Tactics & Formations)")
    st.caption("🧠 Exclusively handles football strategies, tactics, and formations in Bangla.")
    
    user_f_chats = st.session_state.football_ai_chats.setdefault(curr_username, [])
    
    for c in user_f_chats:
        st.markdown(f"**You:** {c['prompt']}")
        st.markdown(f"⚽ **Football AI:** {c['response']}")
        st.divider()
        
    f_prompt = st.text_input("Ask Football AI:", key="in_fai")
    if st.button("Ask Football AI", key="btn_fai"):
        if f_prompt.strip():
            resp = respond_football_ai(f_prompt.strip())
            # REQ 13: Non-football queries redirected immediately to Personal AI
            if resp == "REDIRECT_PERSONAL":
                p_resp = respond_personal_ai(f_prompt.strip(), curr_user["full_name"])
                st.session_state.personal_ai_chats.setdefault(curr_username, []).append({
                    "prompt": f_prompt.strip(),
                    "response": f"*(Football AI থেকে রিডাইরেক্ট করা হয়েছে)*\n{p_resp}"
                })
                st.warning("⚠️ এটি ফুটবল সংক্রান্ত প্রশ্ন না হওয়ায় উত্তরটি আপনার Personal AI ইন্টারফেসে পাঠিয়ে দেওয়া হয়েছে!")
            else:
                user_f_chats.append({"prompt": f_prompt.strip(), "response": resp})
            save_data_to_file()
            st.rerun()

# ==========================================
# 8. FEATURE MODULE: ADMIN CONTROL PANEL (REQ 6, 9, 10, 14, 15, 16, 17, 19, 20)
# ==========================================
elif nav_choice == "⚙️ Admin Control Panel":
    # REQ 17: Visible strictly to Superadmin/Admin
    if curr_user["role"] not in ["Superadmin", "Admin"]:
        st.error("⛔ Access Denied.")
        st.stop()
        
    st.header("⚙️ Administrative Control Panel")
    
    tab_a1, tab_a2, tab_a3, tab_a4, tab_a5 = st.tabs([
        "🎨 Branding & Club Photo",
        "👥 Player Management & Pass",
        "🚫 Blocked Players List",
        "⚽ Formation & GK Saves",
        "🏥 Injury & Attendance Admin"
    ])
    
    with tab_a1:
        # REQ 9: Club Photo setting
        st.subheader("Club Identity & Aesthetics")
        new_app_n = st.text_input("Club Name:", value=st.session_state.app_settings["app_name"])
        new_club_pic = st.text_input("Club Photo URL:", value=st.session_state.app_settings.get("club_photo", ""))
        new_max_reg = st.number_input("Maximum Registerable Players (REQ 20):", min_value=5, max_value=100, value=st.session_state.app_settings.get("max_registration_limit", 30))
        new_bg = st.color_picker("App Background Accent Color (REQ 23):", value=st.session_state.app_settings.get("bg_color", "#0F172A"))
        
        if st.button("Save Branding Settings"):
            st.session_state.app_settings["app_name"] = new_app_n
            st.session_state.app_settings["club_photo"] = new_club_pic
            st.session_state.app_settings["max_registration_limit"] = new_max_reg
            st.session_state.app_settings["bg_color"] = new_bg
            save_data_to_file()
            st.success("Branding updated!")
            st.rerun()

    with tab_a2:
        # REQ 10: Change other's password
        st.subheader("Manage Players & Passwords")
        target_u = st.selectbox("Select Target User:", [u for u in st.session_state.users if u not in st.session_state.blocked_users])
        admin_new_pass = st.text_input("Set New Password for User:", key="a_np")
        
        if st.button("Update User Password"):
            st.session_state.users[target_u]["password"] = admin_new_pass
            save_data_to_file()
            st.success(f"Password updated for @{target_u}!")

        # REQ 14: Blocking a user purges them everywhere except Admin Panel
        st.divider()
        st.subheader("Block Player")
        if st.button("🚫 Block Selected User"):
            st.session_state.blocked_users[target_u] = st.session_state.users.pop(target_u)
            save_data_to_file()
            st.warning(f"User @{target_u} blocked and removed from public views.")
            st.rerun()

    with tab_a3:
        # REQ 15: Admin Panel Blocked List
        st.subheader("🚫 Blocked Players List (Admin View Only)")
        if not st.session_state.blocked_users:
            st.info("No users currently blocked.")
        else:
            for bu in list(st.session_state.blocked_users.keys()):
                col_b1, col_b2 = st.columns([3, 1])
                with col_b1:
                    st.write(f"• **{st.session_state.blocked_users[bu]['full_name']}** (@{bu})")
                with col_b2:
                    if st.button("Unblock", key=f"unblock_{bu}"):
                        st.session_state.users[bu] = st.session_state.blocked_users.pop(bu)
                        save_data_to_file()
                        st.success(f"Unblocked @{bu}!")
                        st.rerun()

    with tab_a4:
        # REQ 16: Formation & Player Count | REQ 6: GK Saves Management
        st.subheader("Formation & GK Saves Admin Engine")
        
        sq_size = st.number_input("Squad Size:", min_value=5, max_value=11, value=st.session_state.match_settings.get("asmb_player_count", 11))
        formation = st.selectbox("Team Formation (REQ 16):", ["4-3-3", "4-4-2", "3-5-2", "4-2-3-1", "5-3-2"], index=0)
        
        if st.button("Save Match Setup"):
            st.session_state.match_settings["asmb_player_count"] = sq_size
            st.session_state.match_settings["formation"] = formation
            save_data_to_file()
            st.success("Match settings updated!")

        st.divider()
        st.subheader("🧤 Goalkeeper Save Tracking & Rating (REQ 6)")
        gk_users = [u for u in st.session_state.users if st.session_state.users[u]["position"] == "GK"]
        if gk_users:
            sel_gk = st.selectbox("Select Goalkeeper:", gk_users)
            saves = st.number_input("Add Shot Saves:", min_value=0, max_value=30, step=1)
            if st.button("Record Saves"):
                st.session_state.gk_saves[sel_gk] = st.session_state.gk_saves.get(sel_gk, 0) + saves
                save_data_to_file()
                st.success(f"Recorded {saves} saves for @{sel_gk}!")

    with tab_a5:
        # REQ 5: Override Attendance | REQ 19: Injured Player List
        st.subheader("Attendance Override & Injury Management")
        
        st.markdown("### 🏥 Injured Player Control (REQ 19)")
        inj_target = st.selectbox("Select Player for Injury List:", [u for u in st.session_state.users if u not in st.session_state.blocked_users])
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            if st.button("Mark as Injured"):
                if inj_target not in st.session_state.injured_players:
                    st.session_state.injured_players.append(inj_target)
                    save_data_to_file()
                    st.success(f"@{inj_target} marked as injured.")
        with col_i2:
            if st.button("Mark as Fit / Recovered"):
                if inj_target in st.session_state.injured_players:
                    st.session_state.injured_players.remove(inj_target)
                    save_data_to_file()
                    st.success(f"@{inj_target} marked as fit.")

        st.divider()
        st.markdown("### 📝 S.A / Admin Attendance Correction (REQ 5)")
        att_target = st.selectbox("Select Player to Override Attendance:", list(st.session_state.users.keys()), key="att_ov_u")
        att_val = st.radio("Attendance Status:", ["Present", "Absent"])
        if st.button("Update Attendance Record"):
            st.session_state.player_stats[att_target]["attendance"] = att_val
            save_data_to_file()
            st.success(f"Attendance override recorded for @{att_target}!")
