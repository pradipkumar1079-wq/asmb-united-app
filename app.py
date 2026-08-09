import streamlit as st
import pandas as pd
import json
import os
import datetime
import hashlib
import random

DATA_FILE = "data/club_store.json"

# ===================import streamlit as st
import pandas as pd
import json
import os
import datetime
import hashlib
import random

DATA_FILE = "data/club_store.json"

# ==========================================
# 1. DATABASE PERSISTENCE LAYER & SETUP
# ==========================================
def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(DATA_FILE):
        default_data = {
            "app_config": {
                "app_name": "ASMB United Football Club",
                "photo_path": None
            },
            "users": {},
            "ratings": {},
            "notices": [],
            "chat_messages": [],
            "ai_chats": {},
            "motm_votes": {},
            "motm_history": []  # List of winning usernames
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4, ensure_ascii=False)

def load_db():
    init_db()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# 2. BUSINESS LOGIC & ALGORITHMS
# ==========================================
def calculate_effective_rating(username, db):
    r = db["ratings"].get(username, {})
    u = db["users"].get(username, {})
    if not r or not r.get("attendance", True):
        return 0.0
    
    evals = r.get("evaluations_received", {})
    if evals:
        base = sum(evals.values()) / len(evals)
    else:
        base = r.get("base_rating", 6.0)
        
    fouls = r.get("foul_score", 0.0)
    goals = r.get("goals", 0)
    assists = r.get("assists", 0)
    conceded = r.get("conceded", 0)
    pos = u.get("preferred_position", "Midfielder")
    penalty = u.get("rating_penalty", 0.0)
    
    conceded_weights = {"Goalkeeper": -2.0, "Defender": -1.75, "Midfielder": -1.5, "Striker": -1.5}
    conceded_penalty = conceded * conceded_weights.get(pos, -1.5)
    
    performance = base - fouls + (goals * 1.0) + (assists * 0.5) + conceded_penalty - penalty
    return round(max(0.0, min(10.0, performance)), 2)

def get_star_players(db):
    """সর্বোচ্চ MOTM বিজয়ী সর্বোচ্চ ৫ জন প্লেয়ারকে Star Player হিসেবে রিটার্ন করে"""
    history = db.get("motm_history", [])
    if not history:
        return []
    
    counts = {}
    for user in history:
        counts[user] = counts.get(user, 0) + 1
    
    # সর্ট করে সর্বোচ্চ ৫ জনক বাছাই
    sorted_motm = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_5 = [user for user, count in sorted_motm[:5] if count > 0]
    return top_5

def generate_dynamic_formation(player_count):
    if player_count >= 11:
        return "4-3-3", {"Goalkeeper": 1, "Defender": 4, "Midfielder": 3, "Striker": 3}
    elif player_count >= 9:
        return "3-3-2", {"Goalkeeper": 1, "Defender": 3, "Midfielder": 3, "Striker": 2}
    elif player_count >= 7:
        return "2-3-1", {"Goalkeeper": 1, "Defender": 2, "Midfielder": 3, "Striker": 1}
    else:
        return "1-2-1", {"Goalkeeper": 1, "Defender": 1, "Midfielder": 2, "Striker": 1}

# ==========================================
# 3. PAGE INITIALIZATION & HIGH-CONTRAST THEME
# ==========================================
st.set_page_config(page_title="ASMB United FC", layout="wide", page_icon="⚽")
db = load_db()

# Dynamic Light Theme CSS
st.markdown("""
    <style>
    .stApp { 
        background-color: #F4F6F9 !important; 
        color: #111111 !important;
    }
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #111111 !important;
    }
    div.stButton > button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid #000000;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #333333 !important;
        color: #FFFFFF !important;
        border-color: #333333;
    }
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
        border-radius: 6px;
    }
    .chat-bubble-me {
        background-color: #DCF8C6;
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 6px;
        text-align: right;
    }
    .chat-bubble-other {
        background-color: #FFFFFF;
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 6px;
        border: 1px solid #E0E0E0;
    }
    </style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None

# ==========================================
# 4. AUTHENTICATION & ACCESS CONTROL
# ==========================================
def auth_section():
    st.sidebar.title("⚽ ASMB Access Portal")
    if st.session_state.user is None:
        tab1, tab2 = st.sidebar.tabs(["🔑 Login", "📝 Register"])
        
        with tab1:
            u_log = st.text_input("Username", key="l_user")
            p_log = st.text_input("Password", type="password", key="l_pass")
            if st.button("Sign In", use_container_width=True):
                if u_log in db["users"]:
                    # ব্লকড ইউজার সুপারঅ্যাডমিন/অ্যাডমিনের পারমিশন ছাড়া ঢুকতে পারবে না
                    if db["users"][u_log].get("is_blocked", False):
                        st.error("⛔ আপনার অ্যাকাউন্ট ব্লক করা হয়েছে। Superadmin বা Admin এর পারমিশন ছাড়া আপনি লগইন করতে পারবেন না।")
                    elif db["users"][u_log]["password_hash"] == hash_pass(p_log):
                        st.session_state.user = u_log
                        st.rerun()
                    else:
                        st.error("ভুল পাসওয়ার্ড!")
                else:
                    st.error("ব্যবহারকারী খুঁজে পাওয়া যায়নি!")
                    
        with tab2:
            is_first = len(db["users"]) == 0
            if is_first:
                st.info("⭐ প্রথম রেজিস্টার্ড অ্যাকাউন্ট অটোমেটিক Superadmin (s.a) হবে!")
            else:
                st.caption("Player Registration Portal")
                
            u_reg = st.text_input("New Username", key="r_user")
            p_reg = st.text_input("New Password", type="password", key="r_pass")
            full_n = st.text_input("Full Name")
            j_num = st.number_input("Jersey Number", min_value=1, max_value=99, step=1, value=10)
            j_name = st.text_input("Jersey Name")
            ai_nam = st.text_input("Personal AI Name", value="TacticsBot")
            
            if u_reg in db["users"]:
                st.warning("এই Username টি অলরেডি ব্যবহ্রত হচ্ছে!")
                
            if st.button("Register Account", use_container_width=True):
                if u_reg and p_reg and u_reg not in db["users"]:
                    # প্রথম ইউজার সরাসরি Superadmin হবে
                    role = "Superadmin" if is_first else "Player"
                    pos = "Midfielder" if is_first else "Unassigned"
                    
                    db["users"][u_reg] = {
                        "password_hash": hash_pass(p_reg),
                        "full_name": full_n if full_n else u_reg,
                        "jersey_number": j_num,
                        "jersey_name": j_name if j_name else u_reg,
                        "preferred_position": pos,
                        "personal_ai_name": ai_nam,
                        "role": role,
                        "is_blocked": False,
                        "block_reason": "",
                        "rating_penalty": 0.0,
                        "is_practice_only": False  # Practice match constraint
                    }
                    db["ratings"][u_reg] = {
                        "base_rating": 6.0, "foul_score": 0.0, "attendance": True,
                        "goals": 0, "assists": 0, "conceded": 0, "is_substitute": False,
                        "evaluations_received": {}
                    }
                    save_db(db)
                    st.success("Registration successful! Please login.")
    else:
        u_data = db["users"][st.session_state.user]
        st.sidebar.markdown(f"**User:** {u_data['full_name']}")
        st.sidebar.markdown(f"**Role:** `{u_data['role']}`")
        st.sidebar.markdown(f"**Personal AI:** {u_data['personal_ai_name']}")
        if u_data.get("is_practice_only", False):
            st.sidebar.warning("⚠️ Practice Only Player")
        st.sidebar.divider()
        
        # Self-Profile Edit Option
        with st.sidebar.expander("⚙️ Edit Profile Info"):
            new_fn = st.text_input("Full Name", value=u_data['full_name'])
            new_jn = st.text_input("Jersey Name", value=u_data['jersey_name'])
            new_num = st.number_input("Jersey #", 1, 99, int(u_data['jersey_number']))
            new_ai = st.text_input("AI Bot Name", value=u_data['personal_ai_name'])
            
            if st.button("Save Profile"):
                db["users"][st.session_state.user]["full_name"] = new_fn
                db["users"][st.session_state.user]["jersey_name"] = new_jn
                db["users"][st.session_state.user]["jersey_number"] = new_num
                db["users"][st.session_state.user]["personal_ai_name"] = new_ai
                save_db(db)
                st.success("Profile Updated!")
                st.rerun()

        if st.sidebar.button("Log Out", use_container_width=True):
            st.session_state.user = None
            st.rerun()

auth_section()

# নিরাপত্তা পরীক্ষা: ব্লক করা থাকলে লগইন অবস্থায়ও সেশন মুছে যাবে
if st.session_state.user and db["users"][st.session_state.user].get("is_blocked", False):
    st.session_state.user = None
    st.error("⛔ আপনার অ্যাকাউন্ট ব্লক করা হয়েছে। Admin বা Superadmin ছাড়া আপনি ঢুকতে পারবেন না।")
    st.stop()

# ==========================================
# 5. HEADER BRANDING & LOGO
# ==========================================
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if db["app_config"].get("photo_path") and os.path.exists(db["app_config"]["photo_path"]):
        st.image(db["app_config"]["photo_path"], width=90)
    else:
        st.title("⚽")
with col_title:
    st.title(db["app_config"]["app_name"])

st.divider()

# ==========================================
# 6. MAIN NAVIGATION TABS
# ==========================================
tab_dir, tab_rate, tab_squad, tab_ai, tab_notice, tab_chat, tab_admin = st.tabs([
    "📋 Directory", "⭐ Rating Panel", "⚽ Squad Generator", 
    "🤖 Football & Personal AI", "📢 Notice Board", "💬 Club Chat", "👑 Admin Controls"
])

# চলতি ইউজার practice_only কি না চেক
is_cur_practice_only = False
if st.session_state.user:
    is_cur_practice_only = db["users"][st.session_state.user].get("is_practice_only", False)

# ------------------------------------------
# TAB 1: PUBLIC PLAYER DIRECTORY
# ------------------------------------------
with tab_dir:
    st.subheader("📋 Public Player Roster & Position List")
    roster = []
    is_admin = st.session_state.user and db["users"][st.session_state.user]["role"] in ["Admin", "Superadmin"]
    
    # ব্লক করা প্লেয়ারদের প্লেয়ার লিস্ট থেকে সম্পূর্ণ বাদ দেওয়া হলো
    active_users = [u for u in db["users"].keys() if not db["users"][u].get("is_blocked", False)]
    sorted_users = sorted(active_users, key=lambda x: calculate_effective_rating(x, db), reverse=True)
    
    # সর্বোচ্চ ৫ জন MOTM বিজয়ী প্লেয়ারদের Star Player হিসেবে চিহ্নিত করা
    star_players = get_star_players(db)
    
    for u in sorted_users:
        d = db["users"][u]
        eff = calculate_effective_rating(u, db)
        is_star = u in star_players
        
        roster.append({
            "Jersey #": f"#{d['jersey_number']}",
            "Full Name": d["full_name"],
            "Display Name": d["jersey_name"],
            "Position": d["preferred_position"],
            "Role": d["role"],
            "Type": "Practice Only" if d.get("is_practice_only", False) else "Standard",
            "Status": "⭐ Star Player" if is_star else "Standard",
            "Effective Rating": eff if is_admin else "Hidden (Admin Only)"
        })
    st.dataframe(pd.DataFrame(roster), use_container_width=True)

# ------------------------------------------
# TAB 2: PEER RATING & METRIC CORRECTION PANEL
# ------------------------------------------
with tab_rate:
    st.subheader("⭐ Peer Rating & Entry Corrections")
    if not st.session_state.user:
        st.warning("Please log in to rate teammates.")
    else:
        st.markdown("#### Rate Teammates")
        # ব্লক থাকা ইউজার রেটিং অপশনে আসবে না
        other_players = [u for u in db["users"].keys() if u != st.session_state.user and not db["users"][u].get("is_blocked", False)]
        if other_players:
            target_p = st.selectbox("Select Player to Rate", other_players)
            given_r = st.slider("Rating Score (0.0 - 10.0)", 0.0, 10.0, 7.0, step=0.1)
            given_f = st.slider("Foul Score Penalty (0.0 - 10.0)", 0.0, 10.0, 0.0, step=0.1)
            
            if st.button("Submit Peer Rating"):
                db["ratings"][target_p]["evaluations_received"][st.session_state.user] = given_r
                db["ratings"][target_p]["foul_score"] = given_f
                save_db(db)
                st.success(f"Evaluation submitted for {target_p}.")
        
        st.divider()
        st.markdown("#### ✏️ Self Base Metric Correction")
        my_r = db["ratings"][st.session_state.user]
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            corr_r = st.number_input("Base Rating", 0.0, 10.0, float(my_r.get("base_rating", 6.0)), step=0.1)
        with col_c2:
            corr_f = st.number_input("Foul Score", 0.0, 10.0, float(my_r.get("foul_score", 0.0)), step=0.1)
            
        if st.button("Apply Metric Correction"):
            db["ratings"][st.session_state.user]["base_rating"] = corr_r
            db["ratings"][st.session_state.user]["foul_score"] = corr_f
            save_db(db)
            st.success("Metrics updated successfully.")

# ------------------------------------------
# TAB 3: AI SQUAD GENERATOR & POSTING
# ------------------------------------------
with tab_squad:
    st.subheader("⚽ Automated AI Squad Generator")
    
    # Practice Only প্লেয়ার মেইন ম্যাচের তথ্য দেখতে পারবে না
    if is_cur_practice_only:
        st.warning("⚠️ আপনি Practice Only প্লেয়ার। আপনি মেইন ম্যাচের কোনো স্কোয়াড বা তথ্য দেখতে পারবেন না।")
    else:
        col1, col2 = st.columns(2)
        with col1:
            num_players = st.number_input("Starting Player Count", 4, 11, 11)
            day_mode = st.selectbox("Preparation Mode", ["Saturday (Match Day Prep)", "Non-Saturday (Practice Prep)"])
        with col2:
            opp_tactics = st.text_area("Opponent Tactics Input", "High press defensive style.")

        if st.button("Generate & Publish Squad"):
            # ব্লক থাকা প্লেয়ার কোনোভাবেই স্কোয়াডে যুক্ত হবে না
            active = [
                u for u, r in db["ratings"].items() 
                if r.get("attendance", True) and not db["users"][u].get("is_blocked", False)
            ]
            
            # শনিবারের মেইন ম্যাচে 'Practice Only' প্লেয়ারদের স্কোয়াড থেকে বাদ দেওয়া
            if "Saturday" in day_mode:
                active = [u for u in active if not db["users"][u].get("is_practice_only", False)]

            ranked = sorted(active, key=lambda x: calculate_effective_rating(x, db), reverse=True)
            fmt, pos_map = generate_dynamic_formation(num_players)
            
            if "Saturday" in day_mode:
                starters = ranked[:num_players]
                subs = ranked[num_players:]
                squad_text = f"📢 **MATCH DAY SQUAD ({fmt})**\n\n"
                squad_text += "**Starters:**\n" + "\n".join([f"- #{db['users'][p]['jersey_number']} {db['users'][p]['jersey_name']} ({calculate_effective_rating(p, db)})" for p in starters]) + "\n\n"
                squad_text += "**Substitutes:**\n" + "\n".join([f"- {i+1}st Sub: {db['users'][p]['jersey_name']}" for i, p in enumerate(subs)]) + "\n\n"
                squad_text += f"**Tactical Focus:** Countering opponent's tactic ({opp_tactics})."
            else:
                team_a = ranked[0::2]
                team_b = ranked[1::2]
                squad_text = f"📢 **PRACTICE TEAMS (BALANCED AGGREGATE)**\n\n"
                squad_text += "**Team A:** " + ", ".join([db["users"][p]["jersey_name"] for p in team_a]) + "\n\n"
                squad_text += "**Team B:** " + ", ".join([db["users"][p]["jersey_name"] for p in team_b])

            can_post = st.session_state.user and db["users"][st.session_state.user]["role"] in ["Admin", "Superadmin"]
            if can_post:
                is_main_notice = "Saturday" in day_mode
                db["notices"].append({
                    "author": f"AI Squad ({st.session_state.user})", 
                    "content": squad_text, 
                    "date": str(datetime.date.today()),
                    "is_main_match": is_main_notice
                })
                save_db(db)
                st.success("Squad directly posted to Official Notice Board!")
            else:
                st.info("Generated Squad preview (Only Admins/Superadmins can publish directly):")
                
            st.markdown(squad_text)

# ------------------------------------------
# TAB 4: DUAL AI COMMUNICATION PORTAL
# ------------------------------------------
with tab_ai:
    st.subheader("🤖 Dual AI Communication System")
    col_f, col_p = st.columns(2)
    
    with col_f:
        st.markdown(f"### ⚽ Public Football AI")
        st.caption("Public AI: Answers posted automatically to Notice Board.")
        f_q = st.text_input("Ask Football AI a tactical question:")
        if st.button("Ask Football AI"):
            if f_q:
                ans = f"Tactical Advice: Maintain compact lines and shift quickly during turnovers."
                db["notices"].append({
                    "author": f"Football AI Q&A ({st.session_state.user or 'Guest'})", 
                    "content": f"**Q:** {f_q}\n\n**A:** {ans}", 
                    "date": str(datetime.date.today()),
                    "is_main_match": False
                })
                save_db(db)
                st.success("Answer posted to Notice Board!")
                st.rerun()

    with col_p:
        if st.session_state.user:
            ai_name = db["users"][st.session_state.user]["personal_ai_name"]
            st.markdown(f"### 🤖 Personal AI (`{ai_name}`)")
            st.caption("Private AI: Strictly confidential to your account.")
            p_q = st.text_input("Ask Personal AI private advice:")
            if st.button("Ask Personal AI"):
                if p_q:
                    if st.session_state.user not in db["ai_chats"]:
                        db["ai_chats"][st.session_state.user] = []
                    db["ai_chats"][st.session_state.user].append({
                        "q": p_q, 
                        "a": "Personal Strategy: Focus on off-the-ball movement and early vision."
                    })
                    save_db(db)
                    st.rerun()
                    
            if st.session_state.user in db["ai_chats"]:
                for c in reversed(db["ai_chats"][st.session_state.user]):
                    st.markdown(f"**You:** {c['q']}")
                    st.markdown(f"**{ai_name}:** {c['a']}")
                    st.divider()

# ------------------------------------------
# TAB 5: NOTICE BOARD & MOTM VOTING
# ------------------------------------------
with tab_notice:
    st.subheader("📢 Official Notice Board")
    
    # Announcement posting
    if st.session_state.user and db["users"][st.session_state.user]["role"] in ["Admin", "Superadmin"]:
        with st.expander("📌 Post New Announcement (Admin / Superadmin Only)"):
            n_text = st.text_area("Announcement Message:")
            is_main_announcement = st.checkbox("Mark as Main Match Notice (Hide from Practice Only Players)")
            if st.button("Publish Announcement"):
                if n_text:
                    db["notices"].append({
                        "author": f"{db['users'][st.session_state.user]['role']} ({st.session_state.user})",
                        "content": n_text,
                        "date": str(datetime.date.today()),
                        "is_main_match": is_main_announcement
                    })
                    save_db(db)
                    st.success("Notice published!")
                    st.rerun()

    st.markdown("#### 🏆 Sunday Man of the Match (MOTM) Poll")
    
    # ব্লকড ও পারফেক্ট লিস্ট ফিল্টার
    active_nominees = [d["full_name"] for u, d in db["users"].items() if not d.get("is_blocked", False)]
    motm_pick = st.selectbox("Select MOTM Nominee:", active_nominees)
    
    if st.button("Submit MOTM Vote"):
        if st.session_state.user:
            db["motm_votes"][st.session_state.user] = motm_pick
            save_db(db)
            st.success("Vote registered.")
            
    if st.session_state.user and db["users"][st.session_state.user]["role"] in ["Admin", "Superadmin"]:
        if st.button("Finalize & Publish MOTM Winner"):
            if db["motm_votes"]:
                winner_fullname = max(set(db["motm_votes"].values()), key=list(db["motm_votes"].values()).count)
                
                # Full Name থেকে Username বের করে MOTM হিস্টোরিতে সেভ
                winner_username = None
                for u, d in db["users"].items():
                    if d["full_name"] == winner_fullname:
                        winner_username = u
                        break
                
                if winner_username:
                    if "motm_history" not in db:
                        db["motm_history"] = []
                    db["motm_history"].append(winner_username)

                db["notices"].append({
                    "author": "Football AI", 
                    "content": f"🏆 **SUNDAY MOTM WINNER:** {winner_fullname}", 
                    "date": str(datetime.date.today()),
                    "is_main_match": False
                })
                db["motm_votes"] = {} # রিসেট ভোট
                save_db(db)
                st.rerun()

    st.divider()
    
    # নোটিশ রেন্ডার করা (Practice Only ইউজার মেইন ম্যাচের নোটিশ পাবে না)
    for n in reversed(db["notices"]):
        if is_cur_practice_only and n.get("is_main_match", False):
            continue # হাইড করা হলো
        st.markdown(f"**[{n['date']}] {n['author']}**")
        st.markdown(f"{n['content']}")
        st.divider()

# ------------------------------------------
# TAB 6: WHATSAPP-STYLE GROUP CHAT
# ------------------------------------------
with tab_chat:
    st.subheader("💬 Club House Group Chat")
    
    chat_container = st.container()
    with chat_container:
        for m in db["chat_messages"]:
            # ব্লক থাকা কোনো ইউজারের পুরানো বা বর্তমান মেসেজ প্রদর্শিত হবে না
            if not db["users"].get(m["user"], {}).get("is_blocked", False):
                is_me = m["user"] == st.session_state.user
                css_class = "chat-bubble-me" if is_me else "chat-bubble-other"
                st.markdown(f"""
                    <div class="{css_class}">
                        <small><b>{m['user']}</b></small><br>{m['text']}
                    </div>
                """, unsafe_allow_html=True)
            
    if st.session_state.user:
        msg_in = st.text_input("Type a message...", key="c_in")
        if st.button("Send Message"):
            if msg_in:
                db["chat_messages"].append({"user": st.session_state.user, "text": msg_in})
                save_db(db)
                st.rerun()

# ------------------------------------------
# TAB 7: ADMIN & SUPERADMIN CONTROL PANEL
# ------------------------------------------
with tab_admin:
    if not st.session_state.user or db["users"][st.session_state.user]["role"] not in ["Admin", "Superadmin"]:
        st.warning("⚠️ Access Restricted to Admins and Superadmin (s.a).")
    else:
        role = db["users"][st.session_state.user]["role"]
        
        # Superadmin exclusive options
        if role == "Superadmin":
            st.markdown("### 👑 Superadmin (s.a) Dynamic Controls")
            
            # ১. প্রমোশন এবং ডিমোশন
            st.markdown("#### Promote/Demote Admin")
            target_u = st.selectbox("Select User for Promotion/Demotion", list(db["users"].keys()))
            c_sa1, c_sa2 = st.columns(2)
            with c_sa1:
                if st.button("Promote to Admin"):
                    db["users"][target_u]["role"] = "Admin"
                    save_db(db)
                    st.success(f"{target_u} promoted to Admin.")
            with c_sa2:
                if st.button("Revoke Admin Role"):
                    db["users"][target_u]["role"] = "Player"
                    save_db(db)
                    st.success(f"{target_u} demoted to Player.")

            st.divider()
            
            # ২. পজিশন সেট করার অধিকার (কেবলমাত্র Superadmin পারবে)
            st.markdown("#### 🎯 Assign Player Position (s.a Only)")
            pos_target = st.selectbox("Select Player for Position Change", list(db["users"].keys()), key="sa_pos_tgt")
            new_position = st.selectbox("Assign New Position", ["Goalkeeper", "Defender", "Midfielder", "Striker"], key="sa_pos_val")
            if st.button("Update Position"):
                db["users"][pos_target]["preferred_position"] = new_position
                save_db(db)
                st.success(f"Position updated for {pos_target} -> {new_position}")

            st.divider()

            # ৩. Practice Only প্লেয়ার নির্ধারণ
            st.markdown("#### 🏃 Practice Only Mode Restriction (s.a Only)")
            prac_target = st.selectbox("Select Player for Practice Status", list(db["users"].keys()), key="sa_prac_tgt")
            is_prac_val = st.checkbox("Practice Only Player (Main Match hidden)", value=db["users"][prac_target].get("is_practice_only", False))
            if st.button("Save Practice Status"):
                db["users"][prac_target]["is_practice_only"] = is_prac_val
                save_db(db)
                st.success(f"Updated Practice Only status for {prac_target}")

            st.divider()
            
            # ৪. MASTER REFRESH BUTTON (ইউজার অ্যাকাউন্ট রেখে বাকি সব ডিলিট করবে)
            st.markdown("### 🧹 MASTER REFRESH (Data Cleanup)")
            st.caption("🚨 এই বাটনে ক্লিক করলে সমস্ত Chat Messages, AI Chats, Notices, Ratings, MOTM Votes/History মুছে একদম পরিষ্কার হবে। প্লেয়ারদের ID ও রেজিস্টার্ড তথ্য অক্ষত থাকবে।")
            if st.button("🔥 EXECUTE MASTER REFRESH"):
                db["chat_messages"] = []
                db["ai_chats"] = {}
                db["notices"] = []
                db["motm_votes"] = {}
                db["motm_history"] = []
                
                # সমস্ত প্লেয়ারের ম্যাচ স্কোর রিসেট
                for u in db["ratings"]:
                    db["ratings"][u] = {
                        "base_rating": 6.0, "foul_score": 0.0, "attendance": True,
                        "goals": 0, "assists": 0, "conceded": 0, "is_substitute": False,
                        "evaluations_received": {}
                    }
                save_db(db)
                st.warning("Master Refresh Complete! ID এবং ইউজার সুরক্ষিত আছে, বাকি সব ডেটা মুছে পরিষ্কার করে দেওয়া হয়েছে।")
                st.rerun()

        st.divider()
        st.markdown("### ⚙️ General Club Maintenance")
        
        # ব্র্যান্ডিং আপডেট
        st.markdown("#### App Branding & Club Photo")
        new_app_name = st.text_input("Change Club Name", value=db["app_config"]["app_name"])
        uploaded_photo = st.file_uploader("Upload Club Photo / Logo", type=["png", "jpg", "jpeg"])
        if st.button("Update Branding"):
            db["app_config"]["app_name"] = new_app_name
            if uploaded_photo:
                path = f"assets/{uploaded_photo.name}"
                if not os.path.exists("assets"):
                    os.makedirs("assets")
                with open(path, "wb") as f:
                    f.write(uploaded_photo.getbuffer())
                db["app_config"]["photo_path"] = path
            save_db(db)
            st.success("Branding updated successfully.")
            st.rerun()

        st.divider()

        # ব্লক ও আনব্লক প্যানেল
        st.markdown("#### Block / Unblock Player")
        b_target = st.selectbox("Select User to Block/Unblock", list(db["users"].keys()), key="b_tgt")
        b_reason = st.text_input("Reason for Action")
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            if st.button("Block User"):
                db["users"][b_target]["is_blocked"] = True
                db["users"][b_target]["block_reason"] = b_reason
                # ব্লক হওয়া প্লেয়ারের পুরানো মেসেজ মুছে দেওয়া
                db["chat_messages"] = [m for m in db["chat_messages"] if m["user"] != b_target]
                save_db(db)
                st.error(f"User {b_target} is BLOCKED.")
                st.rerun()
        with c_b2:
            if st.button("Unblock User"):
                db["users"][b_target]["is_blocked"] = False
                db["users"][b_target]["block_reason"] = ""
                save_db(db)
                st.success(f"User {b_target} has been UNBLOCKED.")
                st.rerun()

        st.divider()

        # অ্যাটেনডেন্স পরিবর্তন
        st.markdown("#### Attendance Management")
        p_target = st.selectbox("Target Player", list(db["users"].keys()), key="p_tgt")
        p_att = st.checkbox("Attendance Status (Present)", value=True)
        if st.button("Save Attendance"):
            db["ratings"][p_target]["attendance"] = p_att
            save_db(db)
            st.success("Attendance details updated.")

        st.divider()

        # ৫. একাধিক প্লেয়ারের মেইন ম্যাচের গোল ও কনসিড একবারে এন্ট্রি দেওয়ার সুবিধা
        st.markdown("#### ⚽ Record Main Match Stats (Multiple Players)")
        selected_match_players = st.multiselect("Select Match Players", [u for u in db["users"].keys() if not db["users"][u].get("is_blocked", False)])
        
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            g = st.number_input("Goals to add", 0, 10, 0)
        with col_g2:
            a = st.number_input("Assists to add", 0, 10, 0)
        with col_g3:
            c = st.number_input("Goals Conceded to add", 0, 20, 0)
            
        if st.button("Record Match Stats for Selected Players"):
            if selected_match_players:
                for p in selected_match_players:
                    db["ratings"][p]["goals"] += g
                    db["ratings"][p]["assists"] += a
                    db["ratings"][p]["conceded"] += c
                save_db(db)
                st.success(f"Successfully recorded stats for {len(selected_match_players)} player(s)!")
            else:
                st.warning("অনুগ্রহ করে অন্তত একজন প্লেয়ার সিলেক্ট করুন।")=======================
# 1. DATABASE PERSISTENCE LAYER & SETUP
# ==========================================
def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(DATA_FILE):
        default_data = {
            "app_config": {
                "app_name": "ASMB United Football Club",
                "photo_path": None,
                "daily_bg_color": "#F4F6F9"
            },
            "users": {},
            "ratings": {},
            "notices": [],
            "chat_messages": [],
            "ai_chats": {},
            "motm_votes": {}
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4, ensure_ascii=False)

def load_db():
    init_db()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# 2. BUSINESS LOGIC & ALGORITHMS
# ==========================================
def calculate_effective_rating(username, db):
    r = db["ratings"].get(username, {})
    u = db["users"].get(username, {})
    if not r or not r.get("attendance", True):
        return 0.0
    
    evals = r.get("evaluations_received", {})
    if evals:
        base = sum(evals.values()) / len(evals)
    else:
        base = r.get("base_rating", 6.0)
        
    fouls = r.get("foul_score", 0.0)
    goals = r.get("goals", 0)
    assists = r.get("assists", 0)
    conceded = r.get("conceded", 0)
    pos = u.get("preferred_position", "Midfielder")
    penalty = u.get("rating_penalty", 0.0)
    
    conceded_weights = {"Goalkeeper": -2.0, "Defender": -1.75, "Midfielder": -1.5, "Striker": -1.5}
    conceded_penalty = conceded * conceded_weights.get(pos, -1.5)
    
    performance = base - fouls + (goals * 1.0) + (assists * 0.5) + conceded_penalty - penalty
    return round(max(0.0, min(10.0, performance)), 2)

def evaluate_block_validity(reason):
    valid_keywords = ["abuse", "foul", "absent", "toxic", "rule", "cheating", "conduct", "violation"]
    return any(word in reason.lower() for word in valid_keywords)

def generate_dynamic_formation(player_count):
    if player_count >= 11:
        return "4-3-3", {"Goalkeeper": 1, "Defender": 4, "Midfielder": 3, "Striker": 3}
    elif player_count >= 9:
        return "3-3-2", {"Goalkeeper": 1, "Defender": 3, "Midfielder": 3, "Striker": 2}
    elif player_count >= 7:
        return "2-3-1", {"Goalkeeper": 1, "Defender": 2, "Midfielder": 3, "Striker": 1}
    else:
        return "1-2-1", {"Goalkeeper": 1, "Defender": 1, "Midfielder": 2, "Striker": 1}

# ==========================================
# 3. PAGE INITIALIZATION & HIGH-CONTRAST THEME
# ==========================================
st.set_page_config(page_title="ASMB United FC", layout="wide", page_icon="⚽")
db = load_db()

# Dynamic Light Theme Engine
bg_colors = ["#F4F6F9", "#EBF3FA", "#F0F4F8", "#EFEFF4", "#F5F5F7"]
today_str = str(datetime.date.today())
random.seed(today_str)
daily_bg = random.choice(bg_colors)

st.markdown(f"""
    <style>
    .stApp {{ 
        background-color: {daily_bg} !important; 
        color: #111111 !important;
    }}
    h1, h2, h3, h4, h5, h6, p, label, span, div {{
        color: #111111 !important;
    }}
    div.stButton > button {{
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid #000000;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }}
    div.stButton > button:hover {{
        background-color: #333333 !important;
        color: #FFFFFF !important;
        border-color: #333333;
    }}
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
        border-radius: 6px;
    }}
    .chat-bubble-me {{
        background-color: #DCF8C6;
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 6px;
        text-align: right;
    }}
    .chat-bubble-other {{
        background-color: #FFFFFF;
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 6px;
        border: 1px solid #E0E0E0;
    }}
    </style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None

# ==========================================
# 4. AUTHENTICATION & LOGIN/REGISTRATION PORTAL
# ==========================================
def auth_section():
    st.sidebar.title("⚽ ASMB Access Portal")
    if st.session_state.user is None:
        tab1, tab2 = st.sidebar.tabs(["🔑 Login", "📝 Register"])
        
        with tab1:
            u_log = st.text_input("Username", key="l_user")
            p_log = st.text_input("Password", type="password", key="l_pass")
            if st.button("Sign In", use_container_width=True):
                if u_log in db["users"] and db["users"][u_log]["password_hash"] == hash_pass(p_log):
                    st.session_state.user = u_log
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
                    
        with tab2:
            is_first = len(db["users"]) == 0
            if is_first:
                st.info("⭐ First registration becomes Superadmin (s.a)!")
            else:
                st.caption("Player Registration Portal")
                
            u_reg = st.text_input("New Username", key="r_user")
            p_reg = st.text_input("New Password", type="password", key="r_pass")
            full_n = st.text_input("Full Name")
            j_num = st.number_input("Jersey Number", min_value=1, max_value=99, step=1, value=10)
            j_name = st.text_input("Jersey Name")
            ai_nam = st.text_input("Personal AI Name", value="TacticsBot")
            
            if u_reg in db["users"]:
                st.warning("Username already taken!")
                
            if st.button("Register Account", use_container_width=True):
                if u_reg and p_reg and u_reg not in db["users"]:
                    role = "Superadmin" if is_first else "Player"
                    pos = "Midfielder" if is_first else "Unassigned"
                    
                    db["users"][u_reg] = {
                        "password_hash": hash_pass(p_reg),
                        "full_name": full_n if full_n else u_reg,
                        "jersey_number": j_num,
                        "jersey_name": j_name if j_name else u_reg,
                        "preferred_position": pos,
                        "personal_ai_name": ai_nam,
                        "role": role,
                        "is_blocked": False,
                        "block_reason": "",
                        "rating_penalty": 0.0,
                        "has_appealed": False
                    }
                    db["ratings"][u_reg] = {
                        "base_rating": 6.0, "foul_score": 0.0, "attendance": True,
                        "goals": 0, "assists": 0, "conceded": 0, "is_substitute": False,
                        "evaluations_received": {}
                    }
                    save_db(db)
                    st.success("Registration successful! Please login.")
    else:
        u_data = db["users"][st.session_state.user]
        st.sidebar.markdown(f"**User:** {u_data['full_name']}")
        st.sidebar.markdown(f"**Role:** `{u_data['role']}`")
        st.sidebar.markdown(f"**Personal AI:** {u_data['personal_ai_name']}")
        st.sidebar.divider()
        
        # Self-Profile Edit Option
        with st.sidebar.expander("⚙️ Edit Profile Info"):
            new_fn = st.text_input("Full Name", value=u_data['full_name'])
            new_jn = st.text_input("Jersey Name", value=u_data['jersey_name'])
            new_num = st.number_input("Jersey #", 1, 99, int(u_data['jersey_number']))
            new_ai = st.text_input("AI Bot Name", value=u_data['personal_ai_name'])
            
            if st.button("Save Profile"):
                db["users"][st.session_state.user]["full_name"] = new_fn
                db["users"][st.session_state.user]["jersey_name"] = new_jn
                db["users"][st.session_state.user]["jersey_number"] = new_num
                db["users"][st.session_state.user]["personal_ai_name"] = new_ai
                save_db(db)
                st.success("Profile Updated!")
                st.rerun()

        if st.sidebar.button("Log Out", use_container_width=True):
            st.session_state.user = None
            st.rerun()

auth_section()

# ==========================================
# 5. BLOCKED USER AUDIT OVERRIDE
# ==========================================
if st.session_state.user and db["users"][st.session_state.user]["is_blocked"]:
    st.error("⛔ Account Status: Blocked for Fair-Play Violation")
    u_data = db["users"][st.session_state.user]
    
    st.subheader("✉️ One-Time Appeal to Superadmin")
    if not u_data.get("has_appealed", False):
        appeal_msg = st.text_area("Write your final appeal message:")
        if st.button("Send Appeal"):
            db["notices"].append({
                "author": f"APPEAL ({st.session_state.user})",
                "content": appeal_msg,
                "date": str(datetime.date.today())
            })
            db["users"][st.session_state.user]["has_appealed"] = True
            save_db(db)
            st.success("Appeal transmitted directly to Superadmin.")
            st.rerun()
    else:
        st.info("You have already submitted your single allowed appeal.")

    st.subheader("🚩 Fair-Play Audit Request")
    if st.button("Run AI Block Audit"):
        blocker_reason = u_data.get("block_reason", "")
        if not evaluate_block_validity(blocker_reason):
            db["users"][st.session_state.user]["is_blocked"] = False
            save_db(db)
            st.success("AI Audit: Block reason unjustified! You are unblocked.")
            st.rerun()
        else:
            st.error("AI Audit: Block confirmed as justified.")
    st.stop()

# ==========================================
# 6. HEADER BRANDING & LOGO
# ==========================================
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if db["app_config"].get("photo_path") and os.path.exists(db["app_config"]["photo_path"]):
        st.image(db["app_config"]["photo_path"], width=90)
    else:
        st.title("⚽")
with col_title:
    st.title(db["app_config"]["app_name"])

st.divider()

# ==========================================
# 7. MAIN NAVIGATION TABS
# ==========================================
tab_dir, tab_rate, tab_squad, tab_ai, tab_notice, tab_chat, tab_admin = st.tabs([
    "📋 Directory", "⭐ Rating Panel", "⚽ Squad Generator", 
    "🤖 Football & Personal AI", "📢 Notice Board", "💬 Club Chat", "👑 Admin Controls"
])

# ------------------------------------------
# TAB 1: PUBLIC PLAYER DIRECTORY
# ------------------------------------------
with tab_dir:
    st.subheader("📋 Public Player Roster & Position List")
    roster = []
    is_admin = st.session_state.user and db["users"][st.session_state.user]["role"] in ["Admin", "Superadmin"]
    
    # Rating-wise descending sorting
    sorted_users = sorted(db["users"].keys(), key=lambda x: calculate_effective_rating(x, db), reverse=True)
    
    for u in sorted_users:
        d = db["users"][u]
        eff = calculate_effective_rating(u, db)
        is_star = eff > 8.5
        roster.append({
            "Jersey #": f"#{d['jersey_number']}",
            "Full Name": d["full_name"],
            "Display Name": d["jersey_name"],
            "Position": d["preferred_position"],
            "Role": d["role"],
            "Status": "⭐ Star Player" if is_star else "Standard",
            "Effective Rating": eff if is_admin else "Hidden (Admin Only)"
        })
    st.dataframe(pd.DataFrame(roster), use_container_width=True)

# ------------------------------------------
# TAB 2: PEER RATING & METRIC CORRECTION PANEL
# ------------------------------------------
with tab_rate:
    st.subheader("⭐ Peer Rating & Entry Corrections")
    if not st.session_state.user:
        st.warning("Please log in to rate teammates.")
    else:
        st.markdown("#### Rate Teammates")
        other_players = [u for u in db["users"].keys() if u != st.session_state.user]
        if other_players:
            target_p = st.selectbox("Select Player to Rate", other_players)
            given_r = st.slider("Rating Score (0.0 - 10.0)", 0.0, 10.0, 7.0, step=0.1)
            given_f = st.slider("Foul Score Penalty (0.0 - 10.0)", 0.0, 10.0, 0.0, step=0.1)
            
            if st.button("Submit Peer Rating"):
                db["ratings"][target_p]["evaluations_received"][st.session_state.user] = given_r
                db["ratings"][target_p]["foul_score"] = given_f
                save_db(db)
                st.success(f"Evaluation submitted for {target_p}.")
        
        st.divider()
        st.markdown("#### ✏️ Self Base Metric Correction")
        my_r = db["ratings"][st.session_state.user]
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            corr_r = st.number_input("Base Rating", 0.0, 10.0, float(my_r.get("base_rating", 6.0)), step=0.1)
        with col_c2:
            corr_f = st.number_input("Foul Score", 0.0, 10.0, float(my_r.get("foul_score", 0.0)), step=0.1)
            
        if st.button("Apply Metric Correction"):
            db["ratings"][st.session_state.user]["base_rating"] = corr_r
            db["ratings"][st.session_state.user]["foul_score"] = corr_f
            save_db(db)
            st.success("Metrics updated successfully.")

# ------------------------------------------
# TAB 3: AI SQUAD GENERATOR & POSTING
# ------------------------------------------
with tab_squad:
    st.subheader("⚽ Automated AI Squad Generator")
    col1, col2 = st.columns(2)
    with col1:
        num_players = st.number_input("Starting Player Count", 4, 11, 11)
        day_mode = st.selectbox("Preparation Mode", ["Saturday (Match Day Prep)", "Non-Saturday (Practice Prep)"])
    with col2:
        opp_tactics = st.text_area("Opponent Tactics Input", "High press defensive style.")

    if st.button("Generate & Publish Squad"):
        active = [u for u, r in db["ratings"].items() if r.get("attendance", True) and not db["users"][u]["is_blocked"]]
        ranked = sorted(active, key=lambda x: calculate_effective_rating(x, db), reverse=True)
        fmt, pos_map = generate_dynamic_formation(num_players)
        
        if "Saturday" in day_mode:
            starters = ranked[:num_players]
            subs = ranked[num_players:]
            squad_text = f"📢 **MATCH DAY SQUAD ({fmt})**\n\n"
            squad_text += "**Starters:**\n" + "\n".join([f"- #{db['users'][p]['jersey_number']} {db['users'][p]['jersey_name']} ({calculate_effective_rating(p, db)})" for p in starters]) + "\n\n"
            squad_text += "**Substitutes:**\n" + "\n".join([f"- {i+1}st Sub: {db['users'][p]['jersey_name']}" for i, p in enumerate(subs)]) + "\n\n"
            squad_text += f"**Tactical Focus:** Countering opponent's tactic ({opp_tactics})."
        else:
            team_a = ranked[0::2]
            team_b = ranked[1::2]
            squad_text = f"📢 **PRACTICE TEAMS (BALANCED AGGREGATE)**\n\n"
            squad_text += "**Team A:** " + ", ".join([db["users"][p]["jersey_name"] for p in team_a]) + "\n\n"
            squad_text += "**Team B:** " + ", ".join([db["users"][p]["jersey_name"] for p in team_b])

        # Auto-post to Notice Board if Superadmin/Admin or AI
        can_post = st.session_state.user and db["users"][st.session_state.user]["role"] in ["Admin", "Superadmin"]
        if can_post:
            db["notices"].append({"author": f"AI Squad ({st.session_state.user})", "content": squad_text, "date": str(datetime.date.today())})
            save_db(db)
            st.success("Squad directly posted to Official Notice Board!")
        else:
            st.info("Generated Squad preview (Only Admins/Superadmins can publish directly):")
            
        st.markdown(squad_text)

# ------------------------------------------
# TAB 4: DUAL AI COMMUNICATION PORTAL
# ------------------------------------------
with tab_ai:
    st.subheader("🤖 Dual AI Communication System")
    col_f, col_p = st.columns(2)
    
    with col_f:
        st.markdown(f"### ⚽ Public Football AI")
        st.caption("Public AI: Answers posted automatically to Notice Board.")
        f_q = st.text_input("Ask Football AI a tactical question:")
        if st.button("Ask Football AI"):
            if f_q:
                ans = f"Tactical Advice: Maintain compact lines and shift quickly during turnovers."
                db["notices"].append({
                    "author": f"Football AI Q&A ({st.session_state.user or 'Guest'})", 
                    "content": f"**Q:** {f_q}\n\n**A:** {ans}", 
                    "date": str(datetime.date.today())
                })
                save_db(db)
                st.success("Answer posted to Notice Board!")
                st.rerun()

    with col_p:
        if st.session_state.user:
            ai_name = db["users"][st.session_state.user]["personal_ai_name"]
            st.markdown(f"### 🤖 Personal AI (`{ai_name}`)")
            st.caption("Private AI: Strictly confidential to your account.")
            p_q = st.text_input("Ask Personal AI private advice:")
            if st.button("Ask Personal AI"):
                if p_q:
                    if st.session_state.user not in db["ai_chats"]:
                        db["ai_chats"][st.session_state.user] = []
                    db["ai_chats"][st.session_state.user].append({
                        "q": p_q, 
                        "a": "Personal Strategy: Focus on off-the-ball movement and early vision."
                    })
                    save_db(db)
                    st.rerun()
                    
            if st.session_state.user in db["ai_chats"]:
                for c in reversed(db["ai_chats"][st.session_state.user]):
                    st.markdown(f"**You:** {c['q']}")
                    st.markdown(f"**{ai_name}:** {c['a']}")
                    st.divider()

# ------------------------------------------
# TAB 5: NOTICE BOARD & MOTM VOTING
# ------------------------------------------
with tab_notice:
    st.subheader("📢 Official Notice Board")
    
    # Notice Posting Panel for Admin & Superadmin
    if st.session_state.user and db["users"][st.session_state.user]["role"] in ["Admin", "Superadmin"]:
        with st.expander("📌 Post New Announcement (Admin / Superadmin Only)"):
            n_text = st.text_area("Announcement Message:")
            if st.button("Publish Announcement"):
                if n_text:
                    db["notices"].append({
                        "author": f"{db['users'][st.session_state.user]['role']} ({st.session_state.user})",
                        "content": n_text,
                        "date": str(datetime.date.today())
                    })
                    save_db(db)
                    st.success("Notice published!")
                    st.rerun()

    st.markdown("#### 🏆 Sunday Man of the Match (MOTM) Poll")
    motm_pick = st.selectbox("Select MOTM Nominee:", [d["full_name"] for d in db["users"].values()])
    if st.button("Submit MOTM Vote"):
        if st.session_state.user:
            db["motm_votes"][st.session_state.user] = motm_pick
            save_db(db)
            st.success("Vote registered.")
            
    if st.session_state.user and db["users"][st.session_state.user]["role"] in ["Admin", "Superadmin"]:
        if st.button("Finalize & Publish MOTM Winner"):
            if db["motm_votes"]:
                winner = max(set(db["motm_votes"].values()), key=list(db["motm_votes"].values()).count)
                db["notices"].append({
                    "author": "Football AI", 
                    "content": f"🏆 **SUNDAY MOTM WINNER:** {winner}", 
                    "date": str(datetime.date.today())
                })
                save_db(db)
                st.rerun()

    st.divider()
    for n in reversed(db["notices"]):
        st.markdown(f"**[{n['date']}] {n['author']}**")
        st.markdown(f"{n['content']}")
        st.divider()

# ------------------------------------------
# TAB 6: WHATSAPP-STYLE GROUP CHAT
# ------------------------------------------
with tab_chat:
    st.subheader("💬 Club House Group Chat")
    
    # Render Message Stream
    chat_container = st.container()
    with chat_container:
        for m in db["chat_messages"]:
            # Check if user is blocked
            if not db["users"].get(m["user"], {}).get("is_blocked", False):
                is_me = m["user"] == st.session_state.user
                css_class = "chat-bubble-me" if is_me else "chat-bubble-other"
                st.markdown(f"""
                    <div class="{css_class}">
                        <small><b>{m['user']}</b></small><br>{m['text']}
                    </div>
                """, unsafe_allow_html=True)
            
    if st.session_state.user:
        msg_in = st.text_input("Type a message...", key="c_in")
        if st.button("Send Message"):
            if msg_in:
                db["chat_messages"].append({"user": st.session_state.user, "text": msg_in})
                save_db(db)
                st.rerun()

# ------------------------------------------
# TAB 7: ADMIN & SUPERADMIN CONTROL PANEL
# ------------------------------------------
with tab_admin:
    if not st.session_state.user or db["users"][st.session_state.user]["role"] not in ["Admin", "Superadmin"]:
        st.warning("⚠️ Access Restricted to Admins (a) and Superadmin (s.a).")
    else:
        role = db["users"][st.session_state.user]["role"]
        
        if role == "Superadmin":
            st.markdown("### 👑 Superadmin (s.a) Control Center")
            target_u = st.selectbox("Select User for Promotion/Demotion", list(db["users"].keys()))
            c_sa1, c_sa2 = st.columns(2)
            with c_sa1:
                if st.button("Promote to Admin"):
                    db["users"][target_u]["role"] = "Admin"
                    save_db(db)
                    st.success(f"{target_u} promoted to Admin.")
            with c_sa2:
                if st.button("Revoke Admin Role"):
                    db["users"][target_u]["role"] = "Player"
                    save_db(db)
                    st.success(f"{target_u} demoted to Player.")

            st.divider()
            st.markdown("### 🧹 Master Reset (Data Cleanup)")
            st.caption("Resets all chats, private AI records, and notices. User credentials remain intact.")
            if st.button("EXECUTE MASTER RESET"):
                db["chat_messages"] = []
                db["ai_chats"] = {}
                db["notices"] = []
                db["motm_votes"] = {}
                save_db(db)
                st.warning("Master Reset Executed. All chat logs and notice board entries wiped!")
                st.rerun()

        st.divider()
        st.markdown("### ⚙️ Club Maintenance & Settings")
        
        st.markdown("#### App Branding & Club Photo")
        new_app_name = st.text_input("Change Club Name", value=db["app_config"]["app_name"])
        uploaded_photo = st.file_uploader("Upload Club Photo / Logo", type=["png", "jpg", "jpeg"])
        if st.button("Update Branding"):
            db["app_config"]["app_name"] = new_app_name
            if uploaded_photo:
                path = f"assets/{uploaded_photo.name}"
                if not os.path.exists("assets"):
                    os.makedirs("assets")
                with open(path, "wb") as f:
                    f.write(uploaded_photo.getbuffer())
                db["app_config"]["photo_path"] = path
            save_db(db)
            st.success("Branding and logo updated successfully.")
            st.rerun()

        st.markdown("#### Block User & Purge Chat")
        b_target = st.selectbox("Select User to Block", list(db["users"].keys()), key="b_tgt")
        b_reason = st.text_input("Reason for Blocking")
        if st.button("Block User"):
            db["users"][b_target]["is_blocked"] = True
            db["users"][b_target]["block_reason"] = b_reason
            db["chat_messages"] = [m for m in db["chat_messages"] if m["user"] != b_target]
            save_db(db)
            st.error(f"User {b_target} blocked and chat history purged.")

        st.markdown("#### Assign Position & Attendance")
        p_target = st.selectbox("Target Player", list(db["users"].keys()), key="p_tgt")
        p_pos = st.selectbox("Assign Position", ["Goalkeeper", "Defender", "Midfielder", "Striker"])
        p_att = st.checkbox("Attendance Status (Present)", value=True)
        if st.button("Save Position & Attendance"):
            db["users"][p_target]["preferred_position"] = p_pos
            db["ratings"][p_target]["attendance"] = p_att
            save_db(db)
            st.success("Player details updated.")

        st.markdown("#### Record Match Performance Stats")
        m_target = st.selectbox("Match Player", list(db["users"].keys()), key="m_tgt")
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            g = st.number_input("Goals", 0, 10, 0)
        with col_g2:
            a = st.number_input("Assists", 0, 10, 0)
        with col_g3:
            c = st.number_input("Goals Conceded", 0, 20, 0)
        if st.button("Record Match Stats"):
            db["ratings"][m_target]["goals"] += g
            db["ratings"][m_target]["assists"] += a
            db["ratings"][m_target]["conceded"] += c
            save_db(db)
            st.success("Match statistics recorded.")
