import streamlit as st
import pandas as pd
import json
import os
import datetime
import hashlib
import random
from PIL import Image

DATA_FILE = "data/club_store.json"

# --- DATABASE PERSISTENCE LAYER ---
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
            "motm_votes": {},
            "last_published_squad": []
        }
        with open(DATA_FILE, "w") as f:
            json.dump(default_data, f, indent=4)

def load_db():
    init_db()
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
        if "last_published_squad" not in data:
            data["last_published_squad"] = []
        return data

def save_db(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- BUSINESS LOGIC & ALGORITHMS (AI RATING ENGINE) ---
def calculate_effective_rating(username, db):
    r = db["ratings"].get(username, {})
    u = db["users"].get(username, {})
    
    # Blocked or Absent players get 0 rating
    if not r or not r.get("attendance", True) or u.get("is_blocked", False):
        return 0.0
    
    # Calculate average peer rating received
    evals = r.get("evaluations_received", {})
    if evals:
        base = sum(evals.values()) / len(evals)
    else:
        base = r.get("base_rating", 6.0)
        
    fouls = r.get("foul_score", 0.0)
    
    # Combined Main Match & Practice Match Stats for AI Rating Calculation
    goals = r.get("goals", 0) + r.get("practice_goals", 0)
    assists = r.get("assists", 0) + r.get("practice_assists", 0)
    conceded = r.get("conceded", 0) + r.get("practice_conceded", 0)
    
    pos = u.get("preferred_position", "Midfielder")
    penalty = u.get("rating_penalty", 0.0)
    
    # Conceded Goals Penalty (GK: -2.0, Def: -1.75, Mid/Fwd: -1.5)
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

# --- INITIALIZATION & LIGHT HIGH-CONTRAST THEME ---
st.set_page_config(page_title="ASMB United FC", layout="wide")
db = load_db()

# Daily Light Background Theme Engine (High-Contrast Text)
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
        border-radius: 6px;
        font-weight: bold;
    }}
    div.stButton > button:hover {{
        background-color: #333333 !important;
        color: #FFFFFF !important;
    }}
    .stTextInput>div>div>input, .stSelectbox>div>div>div {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
    }}
    </style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None

# --- AUTHENTICATION & LOGIN/REGISTRATION ---
def auth_section():
    st.sidebar.title("ASMB Access Portal")
    if st.session_state.user is None:
        tab1, tab2 = st.sidebar.tabs(["Login", "Register"])
        
        with tab1:
            u_log = st.text_input("Username", key="l_user")
            p_log = st.text_input("Password", type="password", key="l_pass")
            if st.button("Sign In"):
                if u_log in db["users"] and db["users"][u_log]["password_hash"] == hash_pass(p_log):
                    st.session_state.user = u_log
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
                    
        with tab2:
            is_first = len(db["users"]) == 0
            st.info("First registration becomes Superadmin!" if is_first else "Player Registration Portal")
            u_reg = st.text_input("New Username", key="r_user")
            p_reg = st.text_input("New Password", type="password", key="r_pass")
            full_n = st.text_input("Full Name")
            j_num = st.number_input("Jersey Number", min_value=1, max_value=99, step=1)
            j_name = st.text_input("Jersey Name")
            ai_nam = st.text_input("Personal AI Name", value="TacticsBot")
            
            if u_reg in db["users"]:
                st.warning("Username already taken! Redirecting to login...")
                
            if st.button("Register Account"):
                if u_reg and p_reg and u_reg not in db["users"]:
                    role = "Superadmin" if is_first else "Player"
                    pos = "Unassigned" if not is_first else "Midfielder"
                    
                    db["users"][u_reg] = {
                        "password_hash": hash_pass(p_reg),
                        "full_name": full_n,
                        "jersey_number": j_num,
                        "jersey_name": j_name,
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
                        "goals": 0, "assists": 0, "conceded": 0,
                        "practice_goals": 0, "practice_assists": 0, "practice_conceded": 0,
                        "is_substitute": False, "evaluations_received": {}
                    }
                    save_db(db)
                    st.success("Registration successful! Proceed to Login.")
    else:
        u_data = db["users"][st.session_state.user]
        st.sidebar.markdown(f"**User:** {u_data['full_name']} (`{u_data['role']}`)")
        st.sidebar.markdown(f"**Personal AI:** {u_data['personal_ai_name']}")
        if st.sidebar.button("Log Out"):
            st.session_state.user = None
            st.rerun()

auth_section()

# --- BLOCKED USER INTERFACE OVERRIDE ---
if st.session_state.user and db["users"][st.session_state.user].get("is_blocked", False):
    st.error("⛔ Account Status: Blocked")
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

    st.subheader("🚩 Report / Flag User for Fair-Play Violation")
    if st.button("Run AI Block Audit"):
        blocker_reason = u_data.get("block_reason", "")
        if not evaluate_block_validity(blocker_reason):
            db["users"][st.session_state.user]["is_blocked"] = False
            for u, d in db["users"].items():
                if d["role"] in ["Admin", "Superadmin"]:
                    db["users"][u]["rating_penalty"] += 5.0
                    break
            save_db(db)
            st.success("AI Audit: Block reason unjustified! You are unblocked. Blocker penalized -5.0 points.")
            st.rerun()
        else:
            st.error("AI Audit: Block confirmed as justified.")
    st.stop()

# Helper function to get active unblocked users
def get_active_users():
    return {u: d for u, d in db["users"].items() if not d.get("is_blocked", False)}

# --- HEADER BRANDING DISPLAY ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if db["app_config"].get("photo_path") and os.path.exists(db["app_config"]["photo_path"]):
        st.image(db["app_config"]["photo_path"], width=100)
with col_title:
    st.title(db["app_config"]["app_name"])

# --- NAVIGATION TABS ---
tab_dir, tab_rate, tab_squad, tab_ai, tab_notice, tab_chat, tab_admin = st.tabs([
    "📋 Directory", "⭐ Rating Panel", "⚽ Squad Generator", 
    "🤖 Football & Personal AI", "📢 Notice Board", "💬 Chat", "👑 Admin Controls"
])

# 1. PUBLIC PLAYER DIRECTORY (BLOCKED USERS REMOVED)
with tab_dir:
    st.subheader("Public Player Roster")
    roster = []
    active_users = get_active_users()
    for u, d in active_users.items():
        eff = calculate_effective_rating(u, db)
        is_star = eff > 8.5
        is_admin = st.session_state.user and db["users"][st.session_state.user]["role"] in ["Admin", "Superadmin"]
        roster.append({
            "Jersey #": f"#{d['jersey_number']}",
            "Full Name": d["full_name"],
            "Display Name": d["jersey_name"],
            "Position": d["preferred_position"],
            "Status": "⭐ Star Player" if is_star else "Standard",
            "Effective Rating": eff if is_admin else "Hidden"
        })
    st.table(pd.DataFrame(roster))

# 2. RATING & CORRECTION PANEL (BLOCKED USERS REMOVED)
with tab_rate:
    st.subheader("Peer Rating & Entry Corrections")
    if not st.session_state.user:
        st.warning("Log in to submit player ratings.")
    else:
        st.markdown("#### Rate Teammates")
        active_users = get_active_users()
        other_players = [u for u in active_users.keys() if u != st.session_state.user]
        if other_players:
            target_p = st.selectbox("Select Player to Rate", other_players)
            given_r = st.slider("Rating (0.0 - 10.0)", 0.0, 10.0, 7.0, step=0.1)
            given_f = st.slider("Foul Score (0.0 - 10.0)", 0.0, 10.0, 0.0, step=0.1)
            
            if st.button("Submit Peer Rating"):
                db["ratings"][target_p]["evaluations_received"][st.session_state.user] = given_r
                db["ratings"][target_p]["foul_score"] = given_f
                save_db(db)
                st.success(f"Evaluation recorded for {target_p}.")
        
        st.divider()
        st.markdown("#### ✏️ Rating & Foul Correction Override Panel")
        my_r = db["ratings"][st.session_state.user]
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            corr_r = st.number_input("Correct Base Rating", 0.0, 10.0, float(my_r.get("base_rating", 6.0)), step=0.1)
        with col_c2:
            corr_f = st.number_input("Correct Foul Score", 0.0, 10.0, float(my_r.get("foul_score", 0.0)), step=0.1)
        if st.button("Apply Correction"):
            db["ratings"][st.session_state.user]["base_rating"] = corr_r
            db["ratings"][st.session_state.user]["foul_score"] = corr_f
            save_db(db)
            st.success("Metrics updated.")

# 3. AI SQUAD GENERATOR (BLOCKED USERS EXCLUDED)
with tab_squad:
    st.subheader("Automated AI Squad & Formation Generator")
    col1, col2 = st.columns(2)
    with col1:
        num_players = st.number_input("Starting Player Count (Set by Admin)", 4, 11, 11)
        day_mode = st.selectbox("Preparation Mode", ["Saturday (Match Day Prep)", "Non-Saturday (Practice Prep)"])
    with col2:
        opp_tactics = st.text_area("Opponent Tactics Input", "High press defensive style.")

    if st.button("Generate & Publish Squad"):
        active_users = get_active_users()
        active = [u for u in active_users.keys() if db["ratings"][u].get("attendance", True)]
        ranked = sorted(active, key=lambda x: calculate_effective_rating(x, db), reverse=True)
        fmt, pos_map = generate_dynamic_formation(num_players)
        
        if "Saturday" in day_mode:
            starters = ranked[:num_players]
            subs = ranked[num_players:]
            db["last_published_squad"] = starters + subs
            squad_text = f"**MATCH SQUAD ({fmt})**\n\n"
            squad_text += "**Starters:** " + ", ".join([f"{db['users'][p]['jersey_name']} ({calculate_effective_rating(p, db)})" for p in starters]) + "\n\n"
            squad_text += "**Substitutes:** " + ", ".join([f"{i+1}st Sub: {db['users'][p]['jersey_name']}" for i, p in enumerate(subs)]) + "\n\n"
            squad_text += f"**Counter-Tactics:** Scaling structure to exploit opponent weak spots."
        else:
            team_a = ranked[0::2]
            team_b = ranked[1::2]
            db["last_published_squad"] = ranked
            squad_text = f"**PRACTICE TEAMS (BALANCED AGGREGATE)**\n\n"
            squad_text += "**Team A:** " + ", ".join([db["users"][p]["jersey_name"] for p in team_a]) + "\n\n"
            squad_text += "**Team B:** " + ", ".join([db["users"][p]["jersey_name"] for p in team_b])

        db["notices"].append({"author": "Football AI", "content": squad_text, "date": str(datetime.date.today())})
        save_db(db)
        st.success("Squad published directly to Notice Board!")
        st.markdown(squad_text)

# 4. FOOTBALL AI & PERSONAL AI DUAL SYSTEM
with tab_ai:
    st.subheader("Dual AI Communication Portal")
    col_f, col_p = st.columns(2)
    
    with col_f:
        st.markdown(f"### ⚽ Football AI (`{db['app_config']['app_name']}`)")
        st.caption("Public AI: All questions and answers are visible to everyone.")
        f_q = st.text_input("Ask Football AI a tactical question:")
        if st.button("Ask Football AI"):
            ans = f"Tactical Evaluation: Focus on positional balance and high-press transitions."
            db["notices"].append({"author": f"Football AI Q&A ({st.session_state.user})", "content": f"**Q:** {f_q}\n\n**A:** {ans}", "date": str(datetime.date.today())})
            save_db(db)
            st.rerun()

    with col_p:
        if st.session_state.user and not db["users"][st.session_state.user].get("is_blocked", False):
            ai_name = db["users"][st.session_state.user]["personal_ai_name"]
            st.markdown(f"### 🤖 Personal AI (`{ai_name}`)")
            st.caption("Private AI: Strictly confidential to your account.")
            p_q = st.text_input("Ask Personal AI private advice:")
            if st.button("Ask Personal AI"):
                if st.session_state.user not in db["ai_chats"]:
                    db["ai_chats"][st.session_state.user] = []
                db["ai_chats"][st.session_state.user].append({"q": p_q, "a": f"Personal Advice: Work on stamina and direct passing under press."})
                save_db(db)
                st.rerun()
                
            if st.session_state.user in db["ai_chats"]:
                for c in reversed(db["ai_chats"][st.session_state.user]):
                    st.write(f"**You:** {c['q']}")
                    st.write(f"**{ai_name}:** {c['a']}")
                    st.divider()

# 5. NOTICE BOARD & SUNDAY MOTM (BLOCKED USERS EXCLUDED)
with tab_notice:
    st.subheader("Official Notice Board")
    
    st.markdown("#### 🏆 Sunday Man of the Match (MOTM) Poll")
    active_users = get_active_users()
    motm_pick = st.selectbox("Select MOTM Nominee:", [d["full_name"] for d in active_users.values()])
    if st.button("Submit MOTM Vote"):
        if st.session_state.user:
            db["motm_votes"][st.session_state.user] = motm_pick
            save_db(db)
            st.success("Vote registered.")
            
    if st.session_state.user and db["users"][st.session_state.user]["role"] in ["Admin", "Superadmin"]:
        if st.button("Finalize & Publish MOTM Winner"):
            if db["motm_votes"]:
                winner = max(set(db["motm_votes"].values()), key=list(db["motm_votes"].values()).count)
                db["notices"].append({"author": "Football AI", "content": f"🏆 **MOTM WINNER ({datetime.date.today()}):** {winner}", "date": str(datetime.date.today())})
                save_db(db)
                st.rerun()

    st.divider()
    for n in reversed(db["notices"]):
        st.markdown(f"**[{n['date']}] {n['author']}**")
        st.write(n["content"])
        st.divider()

# 6. WHATSAPP-STYLE GROUP CHAT (BLOCKED USERS EXCLUDED)
with tab_chat:
    st.subheader("Club House Group Chat")
    for m in db["chat_messages"]:
        if not db["users"].get(m["user"], {}).get("is_blocked", False):
            st.markdown(f"**{m['user']}**: {m['text']}")
            
    if st.session_state.user and not db["users"][st.session_state.user].get("is_blocked", False):
        msg_in = st.text_input("Type message...", key="c_in")
        if st.button("Send"):
            db["chat_messages"].append({"user": st.session_state.user, "text": msg_in})
            save_db(db)
            st.rerun()

# 7. ADMIN CONTROL PANEL
with tab_admin:
    if not st.session_state.user or db["users"][st.session_state.user]["role"] not in ["Admin", "Superadmin"]:
        st.warning("Restricted to Admin / Superadmin access.")
    else:
        role = db["users"][st.session_state.user]["role"]
        active_users = get_active_users()
        
        if role == "Superadmin":
            st.markdown("### 👑 Superadmin Management & System Control")
            target_u = st.selectbox("Select User for Promotion/Demotion", list(db["users"].keys()))
            c_sa1, c_sa2 = st.columns(2)
            with c_sa1:
                if st.button("Promote to Admin"):
                    db["users"][target_u]["role"] = "Admin"
                    save_db(db)
                    st.success(f"{target_u} promoted.")
            with c_sa2:
                if st.button("Revoke Admin"):
                    db["users"][target_u]["role"] = "Player"
                    save_db(db)
                    st.success(f"{target_u} demoted.")

            st.divider()
            st.markdown("### 🧹 Master Reset")
            if st.button("EXECUTE MASTER REFRESH"):
                db["chat_messages"] = []
                db["ai_chats"] = {}
                db["notices"] = []
                save_db(db)
                st.warning("All public/private chats and notice records wiped. Player profiles retained.")

        st.divider()
        st.markdown("### ⚙️ Admin Maintenance")
        
        st.markdown("#### App Branding & Logo Update")
        new_app_name = st.text_input("Change Application Name", value=db["app_config"]["app_name"])
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
            st.success("Branding updated.")
            st.rerun()

        st.markdown("#### Block User & Purge History")
        b_target = st.selectbox("Select User to Block", list(db["users"].keys()), key="b_target")
        b_reason = st.text_input("Reason for Block Action")
        if st.button("Block User"):
            db["users"][b_target]["is_blocked"] = True
            db["users"][b_target]["block_reason"] = b_reason
            db["chat_messages"] = [m for m in db["chat_messages"] if m["user"] != b_target]
            save_db(db)
            st.error(f"User {b_target} blocked and chat history purged.")

        st.markdown("#### Assign Position & Attendance")
        p_target = st.selectbox("Target Player", list(active_users.keys()), key="p_tgt")
        p_pos = st.selectbox("Assign Position", ["Goalkeeper", "Defender", "Midfielder", "Striker"])
        p_att = st.checkbox("Attendance Status (Present)", value=True)
        if st.button("Save Position & Attendance"):
            db["users"][p_target]["preferred_position"] = p_pos
            db["ratings"][p_target]["attendance"] = p_att
            save_db(db)
            st.success("Player details updated.")

        st.divider()
        st.markdown("### ⚽ PRACTICE MATCH - GOALS, ASSISTS & CONCEDED STATS")
        st.caption("Practice match stats automatically update player AI overall ratings.")
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("##### 🟢 Team A Stats")
            p_scorers_a = st.multiselect("Goal Scorers (Team A):", options=list(active_users.keys()), key="p_sc_a")
            p_assisters_a = st.multiselect("Assists (Team A):", options=list(active_users.keys()), key="p_as_a")
            p_conceded_a = st.multiselect("Players Conceding Goals (Team A):", options=list(active_users.keys()), key="p_co_a")
        
        with col_p2:
            st.markdown("##### 🔵 Team B Stats")
            p_scorers_b = st.multiselect("Goal Scorers (Team B):", options=list(active_users.keys()), key="p_sc_b")
            p_assisters_b = st.multiselect("Assists (Team B):", options=list(active_users.keys()), key="p_as_b")
            p_conceded_b = st.multiselect("Players Conceding Goals (Team B):", options=list(active_users.keys()), key="p_co_b")

        if st.button("Record Practice Match Stats"):
            for u in p_scorers_a + p_scorers_b:
                db["ratings"][u]["practice_goals"] = db["ratings"][u].get("practice_goals", 0) + 1
            for u in p_assisters_a + p_assisters_b:
                db["ratings"][u]["practice_assists"] = db["ratings"][u].get("practice_assists", 0) + 1
            for u in p_conceded_a + p_conceded_b:
                db["ratings"][u]["practice_conceded"] = db["ratings"][u].get("practice_conceded", 0) + 1
            save_db(db)
            st.success("Practice match stats successfully added! AI ratings recalculated.")

        st.divider()
        st.markdown("### 🏆 MAIN MATCH DAY STATS (SQUAD FILTERED)")
        squad_members = db.get("last_published_squad", [])
        valid_squad_members = [u for u in squad_members if u in active_users]
        
        if not valid_squad_members:
            st.warning("No main match squad published yet! Publish squad from Squad Generator first.")
        else:
            st.info("Showing members present in published Match Squad:")
            st.write(", ".join([active_users[u]["jersey_name"] for u in valid_squad_members]))
            
            m_scorers = st.multiselect("Goal Scorers (Select multiple if applicable):", options=valid_squad_members, key="m_scorers")
            m_assisters = st.multiselect("Assist Providers (Select multiple):", options=valid_squad_members, key="m_assisters")
            m_conceded = st.multiselect("Goals Conceded Penalty (Select squad members/GKs/Defenders):", options=valid_squad_members, key="m_conceded")
            
            if st.button("Record Main Match Stats"):
                for u in m_scorers:
                    db["ratings"][u]["goals"] += 1
                for u in m_assisters:
                    db["ratings"][u]["assists"] += 1
                for u in m_conceded:
                    db["ratings"][u]["conceded"] += 1
                save_db(db)
                st.success("Main match statistics recorded and AI ratings updated!")
