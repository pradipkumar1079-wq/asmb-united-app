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
# 0. PAGE CONFIGURATION (MUST BE FIRST)
# ==========================================
st.set_page_config(
    page_title="ASMB United Football Club",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# PERMANENT MEMORY FILE ENGINE (JSON STORAGE)
# ==========================================
DB_FILE = "asmb_football_club_data.json"


def load_data_from_file():
  """ফাইল থেকে ডাটা লোড করার লজিক"""
  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

        # ১ নম্বর রেজিস্টার্ড প্লেয়ারকে নিশ্চিতভাবে Superadmin রাখা
        if data and "users" in data and isinstance(data["users"], dict):
          users_dict = data["users"]
          if len(users_dict) > 0:
            first_username = list(users_dict.keys())[0]
            users_dict[first_username]["role"] = "Superadmin"

        return data
    except Exception as e:
      st.error(f"Error loading database file: {e}")
      pass
  return None


def save_data_to_file():
  """পরবর্তী সমস্ত নতুন আইডি এবং তথ্য স্থায়ীভাবে সংরক্ষণের ফাংশন"""
  users_data = st.session_state.get("users", {})

  # প্রথম রেজিস্টার্ড মেম্বার যেন সবসময় Superadmin থাকে
  if users_data and isinstance(users_data, dict) and len(users_data) > 0:
    first_user = list(users_data.keys())[0]
    users_data[first_user]["role"] = "Superadmin"

  data_to_save = {
      "app_settings": st.session_state.get("app_settings", {}),
      "users": users_data,
      "ratings_db": {
          f"{k[0]}|||{k[1]}": v
          for k, v in st.session_state.get("ratings_db", {}).items()
      },
      "player_stats": st.session_state.get("player_stats", {}),
      "group_chat": st.session_state.get("group_chat", []),
      "football_ai_chats": st.session_state.get("football_ai_chats", []),
      "personal_ai_chats": st.session_state.get("personal_ai_chats", {}),
      "notice_board": st.session_state.get("notice_board", []),
      "motm_votes": st.session_state.get("motm_votes", {}),
      "injured_players": list(st.session_state.get("injured_players", set())),
      "match_settings": st.session_state.get("match_settings", {}),
      "block_appeals": st.session_state.get("block_appeals", {}),
      "match_availability_poll": st.session_state.get(
          "match_availability_poll", {}
      ),
  }
  with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(data_to_save, f, indent=4, ensure_ascii=False)


# ==========================================
# SUPER ADMIN (s.a) ID DELETE & ROLE MANAGEMENT ENGINE
# ==========================================


def delete_single_user_by_sa(username_to_delete):
  """সুপার অ্যাডমিন (s.a) দ্বারা নির্দিষ্ট আইডি স্থায়ীভাবে মুছে ফেলার লজিক"""
  if (
      "users" in st.session_state
      and username_to_delete in st.session_state["users"]
  ):
    del st.session_state["users"][username_to_delete]

    if (
        "player_stats" in st.session_state
        and username_to_delete in st.session_state["player_stats"]
    ):
      del st.session_state["player_stats"][username_to_delete]

    if (
        "injured_players" in st.session_state
        and username_to_delete in st.session_state["injured_players"]
    ):
      if isinstance(st.session_state["injured_players"], set):
        st.session_state["injured_players"].discard(username_to_delete)
      elif isinstance(st.session_state["injured_players"], list):
        if username_to_delete in st.session_state["injured_players"]:
          st.session_state["injured_players"].remove(username_to_delete)

    save_data_to_file()
    return True
  return False


def clear_all_data_by_sa():
  """Super Admin এক ক্লিকে আগের সকল রেজিস্টার্ড আইডি মুছে ফেলবেন"""
  st.session_state["users"] = {}
  st.session_state["player_stats"] = {}
  st.session_state["injured_players"] = set()
  st.session_state["ratings_db"] = {}
  st.session_state["group_chat"] = []
  st.session_state["motm_votes"] = {}
  st.session_state["match_availability_poll"] = {}

  save_data_to_file()


def render_sa_id_management_panel():
  """Super Admin (S.A) ইউজার কন্ট্রোল ও রোলে প্রমোট করার প্যানেল"""
  current_user = st.session_state.get("authenticated_user")

  st.markdown("### 🔑 Super Admin (S.A) ID & Role Control Center")

  users = st.session_state.get("users", {})

  if not users:
    st.info("বর্তমানে ডাটাবেজে কোনো নিবন্ধিত ইউজার বা আইডি নেই।")
    return

  st.write(f"📊 **মোট নিবন্ধিত আইডি সংখ্যা:** {len(users)}")

  # 👑 ১. অ্যাডমিন বানানোর অপশন (Make Admin)
  st.markdown("#### 👑 কাউকে Admin বা Role চেঞ্জ করুন")
  other_users = [u for u in users.keys() if u != current_user]

  if other_users:
    target_user_role = st.selectbox(
        "যাকে অ্যাডমিন বানাতে চান বেছে নিন:",
        other_users,
        key="sa_make_admin_select",
    )
    new_role = st.selectbox(
        "নতুন রোল বেছে নিন:",
        ["Player", "Admin"],
        key="sa_role_choice",
    )

    if st.button("🔄 রোল আপডেট করুন"):
      st.session_state.users[target_user_role]["role"] = new_role
      save_data_to_file()
      st.success(f"@{target_user_role} কে সফলভাবে {new_role} করা হয়েছে!")
      st.rerun()

  st.markdown("---")

  # 🗑️ ২. নির্দিষ্ট আইডি ডিলিট করার অপশন
  st.markdown("#### 🗑️ নির্দিষ্ট আইডি ডিলিট করুন")
  user_list = list(users.keys())

  selected_user = st.selectbox(
      "যেই রেজিস্টার্ড আইডি ডিলিট করতে চান বেছে নিন:",
      user_list,
      key="sa_user_select",
  )

  if st.button("❌ নির্বাচিত আইডি ডিলিট করুন", type="primary"):
    if selected_user == current_user:
      st.error("আপনি বর্তমান লগইন করা নিজ আইডি ডিলিট করতে পারবেন না!")
    else:
      if delete_single_user_by_sa(selected_user):
        st.success(f"আইডি '{selected_user}' সফলভাবে ডিলিট করা হয়েছে!")
        st.rerun()
      else:
        st.error("আইডি ডিলিট করতে সমস্যা হয়েছে।")

  # 🚨 ৩. সমস্ত আইডি একবারে রিমুভ করার সুবিধা
  st.markdown("---")
  with st.expander(
      "⚠️ [Super Admin Only] সমস্ত পুরাতন আইডি একবারে রিমুভ করুন"
  ):
    st.warning("এই বাটনে চাপ দিলে সকল ইউজার আইডি মুছে যাবে।")
    if st.button("🚨 সকল পুরাতন আইডি ক্লিন করুন", key="clear_all_sa_btn"):
      clear_all_data_by_sa()
      st.success("সকল নিবন্ধিত আইডি মুছে ডাটাবেজ খালি করা হয়েছে!")
      st.rerun()


# ==========================================
# INITIALIZE SESSION & DATABASE (PURGE OLD DATA)
# ==========================================
def init_db():
  if "db_initialized" not in st.session_state:
    # পুরনো সমস্ত সংরক্ষিত আইডি এবং ডাটা ফাইল থেকে সম্পূর্ণ মুছে নতুন করে শুরু করা হচ্ছে
    if os.path.exists(DB_FILE):
      try:
        os.remove(DB_FILE)
      except Exception:
        pass

    st.session_state.app_settings = {
        "app_name": "ASMB United Football Club",
        "bg_color": "#00D2FF",
        "max_register_limit": 50,
        "club_photo_b64": None,
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
        "goals_conceded": 0,
    }
    st.session_state.block_appeals = {}
    st.session_state.match_availability_poll = {}

    save_data_to_file()
    st.session_state.db_initialized = True

  if "users" in st.session_state and isinstance(st.session_state.users, dict):
    if len(st.session_state.users) > 0:
      first_username = list(st.session_state.users.keys())[0]
      st.session_state.users[first_username]["role"] = "Superadmin"


init_db()


# ==========================================
# 1. DYNAMIC COLOR ENGINE & CSS INJECTION
# ==========================================
def get_daily_theme_colors():
  men_favorite_bg_colors = [
      "#0F172A",
      "#1E3A8A",
      "#064E3B",
      "#18181B",
      "#4C1D95",
      "#1E293B",
      "#450A0A",
  ]
  day_idx = datetime.datetime.now().day % len(men_favorite_bg_colors)
  bg = men_favorite_bg_colors[day_idx]

  txt = "#000000"  # শিরোনাম সহ সকল সাধারণ টেক্সট কালার কালো নিশ্চিতকরণ

  return bg, txt


bg_color, title_text_color = get_daily_theme_colors()
st.session_state.app_settings["bg_color"] = bg_color

# CSS Injection: সমস্ত লেখা ও শিরোনাম কালো (#000000) করা হয়েছে
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg_color} !important;
    }}
    /* সমস্ত টেক্সট, হেডার, লেবেল এবং স্প্যান কালো করা হলো */
    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp span, .stApp label, .stApp div {{
        color: #000000 !important;
        font-weight: 600;
    }}
    .daily-club-title {{
        color: #000000 !important;
        font-size: 2.3rem !important;
        font-weight: 900 !important;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
    }}
   /* বাটনের ব্যাকগ্রাউন্ড সাদা, টেক্সট কালো এবং আউটলাইন কালো করার স্টাইল */
    div.stButton > button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #000000 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: all 0.2s ease !important;
    }
    /* মাউস হোভার করলে বাটনের ব্যাকগ্রাউন্ড হালকা গ্রে হবে */
    div.stButton > button:hover {
        background-color: #E5E5E5 !important; 
        color: #000000 !important;
        border-color: #000000 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 2. HELPER CALCULATORS & BUSINESS LOGIC
# ==========================================
def get_active_unblocked_users():
  return {
      u: data
      for u, data in st.session_state.users.items()
      if data.get("status") == "Active" and not data.get("blocked", False)
  }


def compute_player_rating(username):
  if username not in st.session_state.users:
    return 0.0

  user_ratings = [
      data["rating"]
      for (rater, target), data in st.session_state.ratings_db.items()
      if target == username
  ]
  user_fouling = [
      data["fouls"]
      for (rater, target), data in st.session_state.ratings_db.items()
      if target == username
  ]

  base_rating = (
      (sum(user_ratings) / len(user_ratings)) if user_ratings else 6.0
  )
  avg_fouls = (sum(user_fouling) / len(user_fouling)) if user_fouling else 0.0

  stats = st.session_state.player_stats.get(
      username,
      {
          "goals": 0,
          "assists": 0,
          "conceded_penalty": 0.0,
          "attendance": "Present",
          "rating_penalty": 0.0,
          "gk_saves": 0,
      },
  )

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

  net_rating = (
      base_rating
      + goals_bonus
      + assists_bonus
      + gk_saves_bonus
      - foul_penalty
      - conceded_penalty
      - stats.get("rating_penalty", 0.0)
  )

  if stats.get("attendance") == "Absent":
    net_rating -= 1.0

  return max(0.0, min(10.0, round(net_rating, 2)))


def get_highest_motm_player():
  if not st.session_state.get("motm_votes"):
    return None
  votes_list = list(st.session_state.motm_votes.values())
  if not votes_list:
    return None
  valid_votes = [v for v in votes_list if v in st.session_state.users]
  if not valid_votes:
    return None
  return max(set(valid_votes), key=valid_votes.count)


def update_star_players():
  top_motm_player = get_highest_motm_player()
  for uname, udata in st.session_state.users.items():
    if udata.get("status") == "Blocked" or udata.get("blocked", False):
      udata["is_star"] = False
      continue

    rating = compute_player_rating(uname)
    if rating >= 8.5 or (top_motm_player and uname == top_motm_player):
      udata["is_star"] = True
    else:
      udata["is_star"] = False

  save_data_to_file()


def check_and_publish_attendance_notice():
  active_users = get_active_unblocked_users()
  poll_data = st.session_state.get("match_availability_poll", {})

  all_answered = all(u in poll_data for u in active_users.keys())
  if all_answered and len(active_users) > 0:
    if not st.session_state.get("attendance_published_today", False):
      present_list = [
          f"• {active_users[u].get('full_name', u)} (@{u})"
          for u, ans in poll_data.items()
          if ans == "Yes" and u in active_users
      ]
      absent_list = [
          f"• {active_users[u].get('full_name', u)} (@{u})"
          for u, ans in poll_data.items()
          if ans == "No" and u in active_users
      ]

      notice_text = (
          f"### 📋 Matchday Attendance Summary ({datetime.date.today()})\n\n"
      )
      notice_text += (
          f"**✅ Present ({len(present_list)}):**\n"
          + ("\n".join(present_list) if present_list else "None")
          + "\n\n"
      )
      notice_text += (
          f"**❌ Absent ({len(absent_list)}):**\n"
          + ("\n".join(absent_list) if absent_list else "None")
      )

      st.session_state.notice_board.append({
          "id": len(st.session_state.notice_board) + 1,
          "author": "System Admin",
          "title": f"Official Attendance Summary - {datetime.date.today()}",
          "content": notice_text,
          "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
          "comments": [],
      })
      st.session_state.attendance_published_today = True

      save_data_to_file()


# ==========================================
# 3. AUTHENTICATION & FORGET PASSWORD SYSTEM
# ==========================================
if "authenticated_user" not in st.session_state:
  st.session_state.authenticated_user = None


def login_register_surface():
  st.markdown(
      f'<h1 class="daily-club-title">⚽'
      f' {st.session_state.app_settings.get("app_name", "Football Club")}</h1>',
      unsafe_allow_html=True,
  )

  if st.session_state.app_settings.get("club_photo_b64"):
    try:
      img_bytes = base64.b64decode(
          st.session_state.app_settings["club_photo_b64"]
      )
      st.image(Image.open(io.BytesIO(img_bytes)), use_container_width=True)
    except Exception:
      pass

  tab1, tab2, tab3 = st.tabs(["🔒 Login", "📝 Register", "🔑 Forget Password"])

  # TAB 1: LOGIN SURFACE
  with tab1:
    st.subheader("Login to Dashboard")
    login_username = st.text_input("Username", key="login_uname").strip()
    login_password = st.text_input(
        "Password", type="password", key="login_pass"
    )

    if st.button("Login", key="btn_login"):
      if login_username in st.session_state.users:
        user = st.session_state.users[login_username]
        if user.get("blocked", False) or user.get("status") == "Blocked":
          st.error(
              "⛔ Your account is blocked! Reason:"
              f" {user.get('block_reason', 'Contact Admin')}"
          )
        elif user.get("password") == login_password:
          st.session_state.authenticated_user = login_username
          st.success(
              f"Welcome back, {user.get('full_name', login_username)}!"
          )
          st.rerun()
        else:
          st.error("Invalid password. Please try again.")
      else:
        st.error("Username does not exist. Please register first.")

  # TAB 2: REGISTER SURFACE
  with tab2:
    st.subheader("Club Registration Form")
    active_count = len(get_active_unblocked_users())
    max_limit = st.session_state.app_settings.get("max_register_limit", 50)

    st.info(f"👥 **Registered Active Members:** {active_count} / {max_limit}")

    if active_count >= max_limit:
      st.error("⛔ Registration limit reached! Controlled by Admin.")
    else:
      reg_username = st.text_input(
          "Username (Unique ID)*", key="reg_uname"
      ).strip()
      reg_password = st.text_input(
          "Password*", type="password", key="reg_pass"
      )
      reg_sec_key = st.text_input(
          "Security Key (Required for Reset Password)*",
          key="reg_sec_key",
          type="password",
      ).strip()
      reg_full_name = st.text_input("Full Name*", key="reg_fullname").strip()
      reg_jersey_num = st.number_input(
          "Jersey Number*", min_value=1, max_value=99, step=1
      )
      reg_jersey_name = st.text_input(
          "Jersey Player Name*", key="reg_jname"
      ).strip()

      reg_photo_file = st.file_uploader(
          "Upload Photo (Optional)", type=["jpg", "png", "jpeg"]
      )
      reg_photo_b64 = None
      if reg_photo_file:
        reg_photo_b64 = base64.b64encode(reg_photo_file.read()).decode("utf-8")

      reg_personal_ai = st.text_input(
          "Personal AI Custom Name*", value="Jarvis", key="reg_pai"
      ).strip()

      # ১ নম্বর রেজিস্টার্ড ইউজার স্বয়ংক্রিয়ভাবে Superadmin হবে
      is_first_user = len(st.session_state.users) == 0
      if is_first_user:
        st.info("ℹ️ First user automatically granted Superadmin (S.A) role.")
        reg_position = st.selectbox(
            "Assign Initial Position (Superadmin Exclusive)",
            ["GK", "CB", "LB", "RB", "CM", "CAM", "RW", "LW", "ST"],
        )
      else:
        st.warning(
            "🔒 Position assignment is strictly disabled during registration."
            " S.A/Admin will set your position later."
        )
        reg_position = "Unassigned"

      if st.button("Register Account", key="btn_reg"):
        if (
            not reg_username
            or not reg_password
            or not reg_full_name
            or not reg_jersey_name
            or not reg_personal_ai
            or not reg_sec_key
        ):
          st.error("Please fill in all required fields!")
        elif reg_username in st.session_state.users:
          st.error(
              "⚠️ Username already exists! Please try logging in or use another"
              " Username."
          )
        else:
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
              "is_star": False,
          }

          if "player_stats" not in st.session_state:
            st.session_state.player_stats = {}

          st.session_state.player_stats[reg_username] = {
              "goals": 0,
              "assists": 0,
              "conceded_penalty": 0.0,
              "attendance": "Present",
              "rating_penalty": 0.0,
              "gk_saves": 0,
          }

          # পারমানেন্ট সেভ
          save_data_to_file()
          st.success(
              "Registration successful! Your ID is saved permanently. Please"
              " go to Login tab."
          )

  # TAB 3: FORGET PASSWORD
  with tab3:
    st.subheader("🔑 Forget Password Reset")
    fp_uname = st.text_input("Enter Username:", key="fp_uname").strip()
    fp_sec_key = st.text_input(
        "Enter Security Key:", key="fp_sec_key", type="password"
    ).strip()
    fp_new_pass = st.text_input(
        "Enter New Password:", key="fp_new_pass", type="password"
    ).strip()

    if st.button("Reset Password", key="btn_fp_reset"):
      if not fp_uname or not fp_sec_key or not fp_new_pass:
        st.error(
            "Please fill in all fields (Username, Security Key, New Password)!"
        )
      elif fp_uname in st.session_state.users:
        u = st.session_state.users[fp_uname]
        stored_sec_key = str(u.get("sec_key", "")).strip()

        if stored_sec_key and stored_sec_key == fp_sec_key:
          u["password"] = fp_new_pass
          save_data_to_file()
          st.success(
              "Password successfully updated! Please login with your new"
              " password."
          )
        elif not stored_sec_key:
          st.error("Security Key not set for this user. Contact Admin!")
        else:
          st.error("Incorrect Security Key!")
      else:
        st.error("Username not found!")


# অথেন্টিকেশন সেশন গার্ড
if not st.session_state.authenticated_user:
  login_register_surface()
  st.stop()

# ==========================================
# MANDATORY SECURITY KEY POP-UP FOR EXISTING USERS
# ==========================================
curr_username = st.session_state.authenticated_user
curr_user = st.session_state.users.get(curr_username, {})

if "sec_key" not in curr_user or not str(curr_user.get("sec_key", "")).strip():
  st.warning(
      "🔑 **Security Key Mandatory Update:** আপনার অ্যাকাউন্টে কোনো Security Key"
      " সেট করা নেই। পরবর্তীতে পাসওয়ার্ড রিসেটের সুবিধার জন্য একটি গোপন সিকিউরিটি"
      " কী সেট করুন।"
  )

  legacy_key = st.text_input(
      "Set Security Key (Required)*", type="password", key="pop_sec_key"
  ).strip()

  if st.button("Save & Proceed to App", key="btn_save_pop_key"):
    if legacy_key:
      curr_user["sec_key"] = legacy_key
      st.session_state.users[curr_username] = curr_user

      save_data_to_file()
      st.success("✅ Security Key successfully saved! Redirecting...")
      st.rerun()
    else:
      st.error("⚠️ Security Key cannot be left empty. Please enter a key.")

  st.stop()

# ==========================================
# SATURDAY-ONLY MATCHDAY PRE-POLL DIALOG
# ==========================================
if "match_availability_poll" not in st.session_state:
  st.session_state.match_availability_poll = {}

if "player_stats" not in st.session_state:
  st.session_state.player_stats = {}

is_saturday = datetime.datetime.now().weekday() == 5

if (
    is_saturday
    and curr_user.get("status") == "Active"
    and curr_username not in st.session_state.match_availability_poll
):

  st.info(
      "📅 **Saturday Pre-Match Poll:** আগামীকাল রবিবারের (Sunday Matchday) ম্যাচে"
      " কি তুই খেলবি?"
  )
  col_p1, col_p2 = st.columns(2)

  with col_p1:
    if st.button(
        "✅ Yes, I will attend", key="poll_yes", use_container_width=True
    ):
      st.session_state.match_availability_poll[curr_username] = "Yes"

      if curr_username not in st.session_state.player_stats:
        st.session_state.player_stats[curr_username] = {}
      st.session_state.player_stats[curr_username]["attendance"] = "Present"

      save_data_to_file()
      if "check_and_publish_attendance_notice" in globals():
        check_and_publish_attendance_notice()

      st.rerun()

  with col_p2:
    if st.button(
        "❌ No, I cannot attend", key="poll_no", use_container_width=True
    ):
      st.session_state.match_availability_poll[curr_username] = "No"

      if curr_username not in st.session_state.player_stats:
        st.session_state.player_stats[curr_username] = {}
      st.session_state.player_stats[curr_username]["attendance"] = "Absent"

      save_data_to_file()
      if "check_and_publish_attendance_notice" in globals():
        check_and_publish_attendance_notice()

      st.rerun()

# 👑 সুপার অ্যাডমিন প্যানেল রেন্ডার করার জন্য শর্ত (যদি সে S.A বা Admin হয়)
if curr_user.get("role") in ["Superadmin", "Admin"]:
  with st.sidebar.expander("👑 S.A & Admin Panel"):
    render_sa_id_management_panel()      
        
# ==========================================
# 4. SIDEBAR & NAVIGATION
# ==========================================
# স্টার প্লেয়ার আপডেট ফাংশন কল (ফাংশনটি গ্লোবালি সংজ্ঞায়িত থাকতে হবে)
if "update_star_players" in globals():
    update_star_players()

# অ্যাপের নাম ফেচ করা (নিরাপদ পদ্ধতি)
app_name = st.session_state.app_settings.get("app_name", "Football Club")

st.sidebar.markdown(f'<h2 class="daily-club-title">{app_name}</h2>', unsafe_allow_html=True)

# ইউজারের তথ্য প্রদর্শন
full_name = curr_user.get("full_name", "Unknown User")
role = curr_user.get("role", "Player")
position = curr_user.get("position", "Unassigned")

st.sidebar.markdown(f"**User:** {full_name} (`@{curr_username}`)")
st.sidebar.markdown(f"**Role:** `{role}` | **Position:** `{position}`")

# ব্লকড ইউজার ওয়ার্নিং
if curr_user.get("status") == "Blocked":
    st.sidebar.error("🚨 ACCOUNT BLOCKED")

# লগআউট বাটন
if st.sidebar.button("Logout", key="btn_logout", use_container_width=True):
    st.session_state.authenticated_user = None
    st.rerun()

st.sidebar.divider()

# নেভিগেশন মেনু লজিক
if curr_user.get("status") == "Blocked":
    # ইউজার ব্লকড থাকলে মেনুর বদলে শুধু একটি নির্দিষ্ট ড্যাশবোর্ডে ফোর্স করা হবে
    st.sidebar.warning("Your access is restricted.")
    nav_choice = "🚩 Blocked Dashboard / Appeals"
else:
    # অ্যাক্টিভ ইউজারদের জন্য মেনু অপশন
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
    
    # অ্যাডমিন প্যানেল শুধুমাত্র Superadmin এবং Admin-দের জন্য
    if role in ["Superadmin", "Admin"]:
        options.append("⚙️ Admin Control Panel")
        
    nav_choice = st.sidebar.radio("Navigation Menu", options)
    
# ==========================================
# 5. BLOCKED USER SURFACE
# ==========================================
# ডিকশনারি সেফটি ইনিশিয়ালাইজেশন
if "block_appeals" not in st.session_state:
    st.session_state.block_appeals = {}

# ইউজার স্ট্যাটাস ব্লকড কি না চেক
if curr_user.get("status") == "Blocked":
    st.error("🚨 Your account is BLOCKED by management.")
    
    # ব্লক করার কারণ প্রদর্শন
    block_reason = curr_user.get('block_reason', 'Policy Violation / Management Decision')
    st.info(f"**Reason for Block:** {block_reason}")
    
    st.divider()
    st.subheader("📩 Submit Appeal to Superadmin")
    
    # ইতিমধ্যে অ্যাপিল জমা দেওয়া হয়েছে কি না চেক
    if curr_username in st.session_state.block_appeals:
        submitted_appeal = st.session_state.block_appeals[curr_username]
        st.warning("⏳ **Appeal Status:** Under Review by Superadmin/Management.")
        st.markdown(f"**Your Submitted Appeal:**\n> *\"{submitted_appeal}\"*")
        st.caption("Please wait until an administrator reviews your request.")
    else:
        st.write("If you believe this decision was made in error, you can submit a appeal statement below.")
        appeal_text = st.text_area("Write your explanation/appeal to Superadmin:", key="text_appeal_reason")
        
        if st.button("Submit Final Appeal", key="btn_appeal", use_container_width=True):
            if appeal_text.strip():
                # সেশনে এবং ফাইলে অ্যাপিল সেভ
                st.session_state.block_appeals[curr_username] = appeal_text.strip()
                save_data_to_file()
                
                st.success("✅ Your appeal has been submitted successfully!")
                st.rerun()
            else:
                st.error("⚠️ Appeal text cannot be empty. Please write a valid reason before submitting.")
                
    # ব্লকড ইউজারের জন্য পরবর্তী অংশ লোড হওয়া বন্ধ রাখা
    st.stop()

# ==========================================
# 6. NOTICE BOARD & COMMENTS (WITH POLL & SQUAD DISPLAY)
# ==========================================
if nav_choice == "📌 Notice Board & News":
  st.header("📌 Official Notice Board")

  # সেশন স্টেট থেকে নোটিশ বোর্ড সেফলি চেক করা
  notice_list = st.session_state.get("notice_board", [])

  if not notice_list:
    st.info("No notices posted yet.")
  else:
    # নতুন নোটিশ আগে দেখানোর জন্য রিভার্স করে লুপ চালানো হচ্ছে
    for idx, notice in enumerate(reversed(notice_list)):
      # সেফলি নোটিশের মেটাডেটা ফেচ করা
      notice_id = notice.get("id", f"idx_{idx}")
      title = notice.get("title", "Untitled Notice")
      timestamp = notice.get("timestamp", "N/A")
      author = notice.get("author", "Admin")

      with st.expander(
          f"📢 {title} - {timestamp} (By: {author})", expanded=(idx == 0)
      ):
        st.markdown(notice.get("content", ""))

        # ------------------------------------------
        # ⚽ Published Squad Display (Auto Player Image & Name)
        # ------------------------------------------
        squad_players = notice.get("squad_players", [])
        if squad_players and isinstance(squad_players, list):
          st.markdown("---")
          st.markdown("### ⚽ Match Day Squad")

          all_users = st.session_state.get("users", {})
          cols = st.columns(2)  # ২ কলামের গ্রিডে দেখাবে

          for p_idx, u_name in enumerate(squad_players):
            player_info = all_users.get(u_name, {})
            p_name = player_info.get("full_name", u_name)
            p_img = (
                player_info.get("profile_pic_url")
                or player_info.get("image")
                or "default_logo.png"
            )

            with cols[p_idx % 2]:
              with st.container():
                c1, c2 = st.columns([1, 3])
                with c1:
                  st.image(p_img, width=60)
                with c2:
                  st.markdown(f"**{p_name}**")
                  st.caption(f"@{u_name}")
                st.divider()

        # ------------------------------------------
        # 📊 Poll Voting Section
        # ------------------------------------------
        poll_options = notice.get("poll_options", [])
        if poll_options:
          st.markdown("---")
          st.markdown("#### 🗳️ Cast Your Vote")

          # সেফলি পোল ভোট ডিকশনারি সেটআপ {username: selected_option}
          if "poll_votes" not in notice or not isinstance(
              notice["poll_votes"], dict
          ):
            notice["poll_votes"] = {}

          votes = notice["poll_votes"]

          # বর্তমান ইউজারের পূর্বের ভোট চেক করা
          current_vote = votes.get(st.session_state.authenticated_user)
          default_index = (
              poll_options.index(current_vote)
              if current_vote in poll_options
              else 0
          )

          selected_option = st.radio(
              "Select an option:",
              options=poll_options,
              index=default_index,
              key=f"poll_select_{notice_id}_{idx}",
          )

          if st.button(
              "Submit Vote", key=f"btn_vote_{notice_id}_{idx}", type="primary"
          ):
            votes[st.session_state.authenticated_user] = selected_option
            save_data_to_file()
            st.success(f"✅ Vote for '{selected_option}' submitted!")
            st.rerun()

          # 📈 Live Results Display
          st.markdown("##### 📊 Live Poll Results")
          total_votes = len(votes)
          if total_votes > 0:
            for opt in poll_options:
              count = list(votes.values()).count(opt)
              pct = (count / total_votes) * 100
              st.write(f"**{opt}** — {count} vote(s) ({pct:.1f}%)")
              st.progress(pct / 100.0)
          else:
            st.info("No votes cast yet. Be the first to vote!")

        # ------------------------------------------
        # 🗑️ Superadmin / Admin Delete Section
        # ------------------------------------------
        if curr_user.get("role") in ["Superadmin", "Admin"]:
          st.markdown("---")
          if st.button(
              "🗑️ Delete This Notice",
              key=f"del_notice_{notice_id}_{idx}",
              type="secondary",
          ):
            st.session_state.notice_board = [
                n
                for n in st.session_state.notice_board
                if n.get("id") != notice_id
            ]
            save_data_to_file()
            st.success("Notice deleted successfully!")
            st.rerun()

        # ------------------------------------------
        # 💬 Comments Section
        # ------------------------------------------
        st.markdown("---")
        st.markdown("##### 💬 Comments")

        if "comments" not in notice or not isinstance(
            notice["comments"], list
        ):
          notice["comments"] = []

        comments = notice["comments"]
        if comments:
          for c in comments:
            st.caption(f"**{c.get('user', 'Anonymous')}:** {c.get('text', '')}")
        else:
          st.caption("No comments yet.")

        comment_input = st.text_input(
            "Add a comment:", key=f"cmt_input_{notice_id}_{idx}"
        )
        if st.button("Post Comment", key=f"btn_cmt_{notice_id}_{idx}"):
          if comment_input.strip():
            notice["comments"].append({
                "user": curr_user.get("full_name", curr_username),
                "text": comment_input.strip(),
            })
            save_data_to_file()
            st.rerun()
            
# ==========================================
# 7. PLAYER DIRECTORY & SPECIAL ROSTERS (WITH SERIAL NUMBERS)
# ==========================================
elif nav_choice == "👥 Player Directory & Roster":
  st.header("👥 Player Directory & Roster")
  tab1, tab2, tab3 = st.tabs(
      ["📋 Public Directory", "⭐ Star Players List", "🏥 Injured Players List"]
  )

  # একটিভ প্লেয়ারদের তালিকা ফেচ করা
  active_users = (
      get_active_unblocked_users()
      if "get_active_unblocked_users" in globals()
      else st.session_state.users
  )

  # ------------------------------------------
  # TAB 1: PUBLIC DIRECTORY
  # ------------------------------------------
  with tab1:
    dir_data = []
    # serial number সহ তালিকা তৈরি
    for idx, (u, d) in enumerate(active_users.items(), 1):
      dir_data.append({
          "#": idx,
          "Username": u,
          "Full Name": d.get("full_name", "N/A"),
          "Jersey #": d.get("jersey_num", "N/A"),
          "Jersey Name": d.get("jersey_name", "N/A"),
          "Position": d.get("position", "Unassigned"),
          "Role": d.get("role", "Player"),
      })

    if dir_data:
      import pandas as pd

      df = pd.DataFrame(dir_data)
      # Table-এর ডিফল্ট 0 ইনডেক্স লুকিয়ে # কলামটিকে সূচক হিসেবে ব্যবহার করা
      st.dataframe(df.set_index("#"), use_container_width=True)
    else:
      st.info("No active players found.")

  # ------------------------------------------
  # TAB 2: STAR PLAYERS LIST
  # ------------------------------------------
  with tab2:
    star_players = [
        u for u, d in active_users.items() if d.get("is_star", False)
    ]
    if not star_players:
      st.info("No star players at the moment.")
    else:
      # ১, ২, ৩ সিরিয়াল নম্বর দিয়ে স্টার প্লেয়ার প্রদর্শন
      for idx, sp in enumerate(star_players, 1):
        u = active_users[sp]
        # রেটিং হিসাব করার ফাংশন নিরাপদে কল করা
        if "compute_player_rating" in globals():
          r = compute_player_rating(sp)
        else:
          r = "N/A"

        full_name = u.get("full_name", sp)
        position = u.get("position", "Unassigned")
        st.success(
            f"{idx}. 🌟 **{full_name}** (`@{sp}`) - Position: {position} |"
            f" Rating: **{r}**"
        )

  # ------------------------------------------
  # TAB 3: INJURED PLAYERS LIST
  # ------------------------------------------
  with tab3:
    injured_list = st.session_state.get("injured_players", [])
    if not injured_list:
      st.info("No injured players listed.")
    else:
      # ১, ২, ৩ নম্বর দিয়ে ইনজুরড প্লেয়ার প্রদর্শন
      count = 1
      for ip in injured_list:
        if ip in active_users:
          u = active_users[ip]
          full_name = u.get("full_name", ip)
          position = u.get("position", "Unassigned")
          st.warning(
              f"{count}. 🩹 **{full_name}** (`@{ip}`) - Position: {position}"
          )
          count += 1

      if count == 1:
        st.info("No active injured players found.")
                    
# ==========================================
# 8. MEMBER PHOTO GALLERY
# ==========================================
elif nav_choice == "🖼️ Member Photo Gallery":
  st.header("🖼️ Member Photo Gallery")

  # একটিভ ইউজারদের ডাটা ফেচ করা
  active_users = (
      get_active_unblocked_users()
      if "get_active_unblocked_users" in globals()
      else st.session_state.get("users", {})
  )

  # যাদের প্রোফাইল ছবি (photo_b64) রয়েছে তাদের ফিল্টার করা
  photo_users = [
      u for u, data in active_users.items() if data.get("photo_b64")
  ]

  if not photo_users:
    st.info("No member profile photos available.")
  else:
    # ৩টি কলামের গ্রিড তৈরি
    cols = st.columns(3)
    for idx, u in enumerate(photo_users):
      udata = active_users[u]
      full_name = udata.get("full_name", u)
      b64_str = udata.get("photo_b64")

      with cols[idx % 3]:
        try:
          # Base64 থেকে বাইটসে রূপান্তর এবং ইমেজ ওপেন
          img_bytes = base64.b64decode(b64_str)
          image = Image.open(io.BytesIO(img_bytes))

          # ছবি প্রদর্শনী
          st.image(image, use_container_width=True)
          st.caption(f"👤 **{full_name}** (`@{u}`)")
        except Exception as e:
          # কোনো কারণে ছবি লোড না হতে পারলে এরর হ্যান্ডলিং
          st.error(f"Could not load photo for @{u}")
            
# ==========================================
# 9. SQUAD GENERATION & TACTICS (WITH RATINGS IN PUBLISHED NOTICE)
# ==========================================
elif nav_choice == "⚽ Squad Generation & Tactics":
  st.header("⚽ Tactical Squad Generator")

  user_role = curr_user.get("role", "Player") if "curr_user" in locals() else "Player"

  if user_role not in ["Superadmin", "Admin"]:
    st.warning("🔒 Only Superadmin/Admin can generate squads.")

  day_sel = st.selectbox(
      "Operation Mode",
      ["Saturday Match Squad", "Practice Day Split (Mon-Thu)"],
  )

  active_users = (
      get_active_unblocked_users()
      if "get_active_unblocked_users" in globals()
      else st.session_state.get("users", {})
  )
  max_avail = len(active_users)

  # হেলপার ফাংশন: নিরাপদে রেটিং গণনা
  def safe_compute_rating(u_id):
    if "compute_player_rating" in globals():
      try:
        return compute_player_rating(u_id)
      except Exception:
        return 0.0
    return 0.0

  # ---------------------------------------------------------
  # MODE 1: SATURDAY MATCH SQUAD
  # ---------------------------------------------------------
  if day_sel == "Saturday Match Squad":
    if user_role in ["Superadmin", "Admin"]:
      col_s1, col_s2 = st.columns(2)
      with col_s1:
        target_count = st.number_input(
            "🔢 Select Field Squad Size (Starters):",
            min_value=1,
            max_value=max_avail if max_avail > 0 else 20,
            value=min(10, max_avail if max_avail > 0 else 10),
            step=1,
        )
      with col_s2:
        fmt_mode = st.radio(
            "📐 Formation Input:",
            ["🤖 AI Auto-Select", "✍️ Manual Custom"],
            horizontal=True,
        )
        if fmt_mode == "✍️ Manual Custom":
          custom_formation = st.text_input(
              "Enter Formation (e.g., 4-3-2 or 3-2-1):", value="4-3-2"
          )
        else:
          custom_formation = "AI Adaptive Formation"
    else:
      target_count = st.session_state.get("match_settings", {}).get(
          "asmb_player_count", 10
      )
      custom_formation = "Adaptive Formation"
      st.info(
          f"Target Squad Size: **{target_count} Field Players + GK**"
      )

    if user_role in ["Superadmin", "Admin"] and st.button(
        "Generate Match Squad", key="btn_gen_sq", type="primary"
    ):
      injured = st.session_state.get("injured_players", [])
      player_stats = st.session_state.get("player_stats", {})

      available = [
          u
          for u in active_users.keys()
          if u not in injured
          and player_stats.get(u, {}).get("attendance") != "Absent"
      ]

      # 1. Separate Goalkeepers (GK) & Field Players strictly
      gk_candidates = [
          u for u in available if active_users[u].get("position") == "GK"
      ]
      field_candidates = [
          u for u in available if active_users[u].get("position") != "GK"
      ]

      gk_player = None
      if gk_candidates:
        gk_candidates_sorted = sorted(
            gk_candidates, key=lambda x: safe_compute_rating(x), reverse=True
        )
        gk_player = gk_candidates_sorted[0]
      elif available:
        # Fallback: আসল GK না থাকলে কম রেটিংয়ের প্লেয়ারকে GK করা হবে
        sorted_all = sorted(
            available, key=lambda x: safe_compute_rating(x)
        )
        gk_player = sorted_all[0]
        field_candidates = [u for u in available if u != gk_player]

      gk_rating = safe_compute_rating(gk_player) if gk_player else "N/A"
      gk_full_name = active_users.get(gk_player, {}).get(
          "full_name", gk_player
      )
      gk_name = (
          f"{gk_full_name} (`@{gk_player}`) [Rating: {gk_rating}]"
          if gk_player
          else "No GK Assigned"
      )

      # 2. Select top field players by rating
      field_sorted = sorted(
          field_candidates, key=lambda x: safe_compute_rating(x), reverse=True
      )
      starters_field = field_sorted[:target_count]
      subs = field_sorted[target_count:]

      # 3. DYNAMIC POSITION ASSIGNMENT
      def categorize_pos(pos):
        pos = str(pos).upper()
        if any(d in pos for d in ["CB", "LB", "RB", "DEF"]):
          return "DEF"
        if any(a in pos for a in ["ST", "RW", "LW", "CAM", "ATT", "CF"]):
          return "ATT"
        return "MID"

      # Group players into categories
      squad_by_cat = {"DEF": [], "MID": [], "ATT": []}
      for p_uname in starters_field:
        p_data = active_users.get(p_uname, {})
        p_pos = p_data.get("position", "CM")
        p_rating = safe_compute_rating(p_uname)
        p_fullname = p_data.get("full_name", p_uname)
        cat = categorize_pos(p_pos)
        squad_by_cat[cat].append(
            (p_uname, f"{p_fullname} (`@{p_uname}`)", p_pos, p_rating)
        )

      chosen_formation = (
          custom_formation
          if fmt_mode == "✍️ Manual Custom"
          else (
              f"Adaptive"
              f" ({len(squad_by_cat['DEF'])}-{len(squad_by_cat['MID'])}-{len(squad_by_cat['ATT'])})"
          )
      )

      # Display Lineup
      st.markdown("### 🏆 Starting Lineup & Tactical Setup")
      st.info(
          f"🎯 **Tactical Formation:** `{chosen_formation}` | **Field"
          f" Starters:** {len(starters_field)} Players"
      )
      st.success(f"🧤 **Main Goalkeeper (GK):** {gk_name}")

      # Dynamic Visual Layout
      st.markdown("#### 🏟️ Pitch Position Setup:")
      pitch_code = f"[ 🧤 GK: {gk_name} ]\n"
      pitch_code += "=" * 65 + "\n"

      for zone, label in [
          ("DEF", "Defenders"),
          ("MID", "Midfielders"),
          ("ATT", "Forwards/Attackers"),
      ]:
        players_in_zone = squad_by_cat[zone]
        if players_in_zone:
          line = f"| {label} ({len(players_in_zone)}): "
          line += " | ".join([
              f"{p[1]} [{p[2]}] (Rating: {p[3]})" for p in players_in_zone
          ])
          pitch_code += line + "\n"
          pitch_code += "-" * 65 + "\n"

      st.code(pitch_code, language="text")

      # Notice Text Generation (With Ratings)
      notice_text = f"### ⚽ Match Squad Announcement ({datetime.date.today()})\n"
      notice_text += f"**Formation:** {chosen_formation}\n"
      notice_text += f"**🧤 GK:** {gk_name}\n\n"
      notice_text += f"**🏟️ Starting Field Lineup ({len(starters_field)} Players):**\n"

      for zone in ["DEF", "MID", "ATT"]:
        for p in squad_by_cat[zone]:
          line = f"* **[{p[2]}]**: {p[1]} - Rating: **{p[3]}**"
          st.markdown(line)
          notice_text += f"{line}\n"

      # 4. Substitution Schedule (With Ratings)
      st.markdown("---")
      st.markdown("### 🔄 Substitution Schedule (10:15 AM - 11:00 AM)")
      notice_text += "\n**🔄 Substitution Schedule:**\n"

      if subs:
        start_time = datetime.datetime.strptime("10:15", "%H:%M")
        match_duration = 45
        interval = match_duration // (len(subs) + 1)
        starters_to_replace = list(reversed(starters_field))

        for idx, sub_p in enumerate(subs):
          sub_time = start_time + datetime.timedelta(
              minutes=interval * (idx + 1)
          )
          time_str = sub_time.strftime("%I:%M %p")

          sub_user = active_users.get(sub_p, {})
          sub_rating = safe_compute_rating(sub_p)
          sub_fname = sub_user.get("full_name", sub_p)

          replaced_p = starters_to_replace[idx % len(starters_to_replace)]
          replaced_user = active_users.get(replaced_p, {})
          replaced_rating = safe_compute_rating(replaced_p)
          replaced_fname = replaced_user.get("full_name", replaced_p)

          sub_msg = (
              f"⏰ **সময় {time_str}:** "
              f"মাঠে নামবেন ➡️ **{sub_fname}** (`@{sub_p}` | Rating:"
              f" **{sub_rating}**) | মাঠ ছাড়বেন ⬅️ **{replaced_fname}**"
              f" (`@{replaced_p}` | Rating: **{replaced_rating}**)"
          )
          st.warning(sub_msg)
          notice_text += f"* {sub_msg}\n"
      else:
        st.info(
            "ℹ️ No substitute players available. Starting lineup will play"
            " full match."
        )
        notice_text += "* No substitutes available.\n"

      if "notice_board" not in st.session_state:
        st.session_state.notice_board = []

      st.session_state.notice_board.append({
          "id": len(st.session_state.notice_board) + 1,
          "author": "Football AI Generator",
          "title": (
              f"Match Squad Lineup ({len(starters_field)} Players + GK)"
          ),
          "content": notice_text,
          "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
          "comments": [],
      })

      if "match_settings" not in st.session_state:
        st.session_state.match_settings = {}
      st.session_state.match_settings["asmb_player_count"] = target_count

      if "save_data_to_file" in globals():
        save_data_to_file()

      st.success("✅ Match Squad successfully published to Notice Board!")

  # ---------------------------------------------------------
  # MODE 2: PRACTICE DAY SPLIT
  # ---------------------------------------------------------
  elif day_sel == "Practice Day Split (Mon-Thu)":
    st.subheader("🏃 Practice Match Balanced Team Generator")

    if user_role in ["Superadmin", "Admin"]:
      col_p1, col_p2 = st.columns(2)
      with col_p1:
        p_fmt_mode = st.radio(
            "📐 Practice Formation:",
            ["🤖 AI Auto-Select", "✍️ Manual Custom"],
            horizontal=True,
            key="p_fmt_radio",
        )
      with col_p2:
        if p_fmt_mode == "✍️ Manual Custom":
          practice_formation = st.text_input(
              "Enter Formation:",
              value="Balanced Practice Formation",
              key="input_practice_fmt",
          )
        else:
          practice_formation = "AI Adaptive Balanced Formation"

      if st.button(
          "Generate & Publish Balanced Teams",
          key="btn_gen_practice",
          type="primary",
      ):
        injured = st.session_state.get("injured_players", [])
        player_stats = st.session_state.get("player_stats", {})

        available = [
            u
            for u in active_users.keys()
            if u not in injured
            and player_stats.get(u, {}).get("attendance") != "Absent"
        ]

        if len(available) < 2:
          st.error(
              "Need at least 2 active players to generate practice teams."
          )
        else:
          sorted_players = sorted(
              available, key=lambda x: safe_compute_rating(x), reverse=True
          )

          team_tp = []
          team_el = []

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

          tp_ratings = [safe_compute_rating(p) for p in team_tp]
          el_ratings = [safe_compute_rating(p) for p in team_el]

          avg_tp = (
              round(sum(tp_ratings) / len(tp_ratings), 2)
              if tp_ratings
              else 0.0
          )
          avg_el = (
              round(sum(el_ratings) / len(el_ratings), 2)
              if el_ratings
              else 0.0
          )

          st.session_state["last_practice_teams"] = {
              "team_tp": team_tp,
              "team_el": team_el,
              "avg_tp": avg_tp,
              "avg_el": avg_el,
              "formation": practice_formation,
          }

          # Notice Text Generation (With Player Ratings)
          notice_text = (
              f"### 🏃 Practice Match Teams - {datetime.date.today()}\n"
          )
          notice_text += f"**Formation:** {practice_formation}\n\n"
          notice_text += (
              f"**🐯 🐅 Tigers & Panthers ({len(team_tp)} Players | Avg Rating:"
              f" {avg_tp}):**\n"
          )
          for idx, p in enumerate(team_tp, 1):
            u = active_users.get(p, {})
            r = safe_compute_rating(p)
            notice_text += f"{idx}. {u.get('full_name', p)} (`@{p}`) - Pos: `{u.get('position', 'N/A')}` | Rating: **{r}**\n"

          notice_text += (
              f"\n**🦅 🦁 Eagles & Lions ({len(team_el)} Players | Avg Rating:"
              f" {avg_el}):**\n"
          )
          for idx, p in enumerate(team_el, 1):
            u = active_users.get(p, {})
            r = safe_compute_rating(p)
            notice_text += f"{idx}. {u.get('full_name', p)} (`@{p}`) - Pos: `{u.get('position', 'N/A')}` | Rating: **{r}**\n"

          if "notice_board" not in st.session_state:
            st.session_state.notice_board = []

          st.session_state.notice_board.append({
              "id": len(st.session_state.notice_board) + 1,
              "author": "Football AI Generator",
              "title": f"Practice Match Split ({len(available)} Players)",
              "content": notice_text,
              "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
              "comments": [],
          })

          if "save_data_to_file" in globals():
            save_data_to_file()

          st.success(
              "✅ Balanced practice teams generated & published to Notice"
              " Board!"
          )
          st.rerun()

      if "last_practice_teams" in st.session_state:
        p_data = st.session_state["last_practice_teams"]
        col_t1, col_t2 = st.columns(2)

        with col_t1:
          st.markdown(
              f"### 🐯 🐅 Tigers & Panthers ({len(p_data['team_tp'])} Players)"
          )
          st.caption(f"Average Team Rating: **{p_data['avg_tp']}**")
          for idx, p in enumerate(p_data["team_tp"], 1):
            u = active_users.get(p, {})
            r = safe_compute_rating(p)
            st.markdown(
                f"{idx}. **{u.get('full_name', p)}** (`@{p}`) - Pos:"
                f" `{u.get('position', 'N/A')}` | Rating: **{r}**"
            )

        with col_t2:
          st.markdown(
              f"### 🦅 🦁 Eagles & Lions ({len(p_data['team_el'])} Players)"
          )
          st.caption(f"Average Team Rating: **{p_data['avg_el']}**")
          for idx, p in enumerate(p_data["team_el"], 1):
            u = active_users.get(p, {})
            r = safe_compute_rating(p)
            st.markdown(
                f"{idx}. **{u.get('full_name', p)}** (`@{p}`) - Pos:"
                f" `{u.get('position', 'N/A')}` | Rating: **{r}**"
            )
                        
# ==========================================
# 10. RATINGS & RATING GUIDE
# ==========================================
elif nav_choice == "⭐ Teammate Ratings & Guide":
  st.header("⭐ Rate Teammates & Performance Guide")

  # ইউজারনেম সেফলি রিড করা
  active_curr_user = (
      curr_user.get("username")
      if "curr_user" in locals() and isinstance(curr_user, dict)
      else st.session_state.get("curr_username", "")
  )

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

  # একটিভ প্লেয়ার ফেচ করা
  active_users = (
      get_active_unblocked_users()
      if "get_active_unblocked_users" in globals()
      else st.session_state.get("users", {})
  )

  # নিজের নাম ছাড়া বাকি একটিভ প্লেয়ারদের তালিকা
  targets = [u for u in active_users.keys() if u != active_curr_user]

  if not targets:
    st.info("No other active teammates available to rate.")
  else:
    # সেশন স্টেটে ratings_db নিশ্চিত করা
    if "ratings_db" not in st.session_state:
      st.session_state.ratings_db = {}

    # প্লেয়ার সিলেকশন বক্স
    target = st.selectbox(
        "Select Teammate:",
        options=targets,
        format_func=lambda x: (
            f"{active_users[x].get('full_name', x)} (`@{x}`)"
        ),
    )

    # পূর্ববর্তী রেটিং ডাটা সেফলি লোড
    prev = st.session_state.ratings_db.get(
        (active_curr_user, target), {"rating": 6.0, "fouls": 0}
    )

    # ফর্ম হ্যান্ডলার
    with st.form(key=f"rating_form_{target}"):
      new_r = st.slider(
          "Rating (0.0 - 10.0)", 0.0, 10.0, float(prev.get("rating", 6.0)), 0.1
      )
      new_f = st.number_input(
          "Fouls (0 - 10)", 0, 10, int(prev.get("fouls", 0)), 1
      )

      submit_btn = st.form_submit_button(
          "💾 Save/Correct Rating", type="primary"
      )

      if submit_btn:
        st.session_state.ratings_db[(active_curr_user, target)] = {
            "rating": round(new_r, 2),
            "fouls": new_f,
        }

        if "save_data_to_file" in globals():
          save_data_to_file()

        target_name = active_users[target].get("full_name", target)
        st.success(f"✅ Rating for {target_name} saved successfully!")
        st.rerun()
          
# ==========================================
# 11. MANAGE PROFILE (EASY PIN & PASS CHANGE - SAFE & FIXED)
# ==========================================
elif nav_choice == "⚙️ Manage Profile":
  st.header("⚙️ Edit Profile")
  st.warning("🔒 Position can only be changed by Admin/Superadmin.")

  # সেফ কারেন্ট ইউজার রেফারেন্স
  if "curr_user" not in locals() or not isinstance(curr_user, dict):
    curr_user = st.session_state.get("curr_user", {})

  uname = curr_user.get("username", "")

  # -------------------------------------------------------------
  # 👤 SECTION 1: PERSONAL DETAILS
  # -------------------------------------------------------------
  st.subheader("👤 Personal Details")
  new_fn = st.text_input("Full Name:", value=curr_user.get("full_name", ""))

  try:
    default_jersey = int(curr_user.get("jersey_num", 1))
  except (ValueError, TypeError):
    default_jersey = 1

  new_jn = st.number_input("Jersey Number:", 1, 99, default_jersey)
  new_jname = st.text_input(
      "Jersey Player Name:", value=curr_user.get("jersey_name", "")
  )
  new_pai = st.text_input(
      "Personal AI Name:", value=curr_user.get("personal_ai_name", "")
  )

  pic = st.file_uploader("Update Profile Photo:", type=["jpg", "png", "jpeg"])

  if st.button("Save Profile Updates", key="btn_prof_save", type="primary"):
    curr_user["full_name"] = new_fn
    curr_user["jersey_num"] = new_jn
    curr_user["jersey_name"] = new_jname
    curr_user["personal_ai_name"] = new_pai

    if pic is not None:
      curr_user["photo_b64"] = base64.b64encode(pic.read()).decode("utf-8")

    # সেশন স্টেট এবং ইউজারের ডাটা সিঙ্ক
    if "users" in st.session_state and uname in st.session_state.users:
      st.session_state.users[uname] = curr_user
    st.session_state.curr_user = curr_user

    if "save_data_to_file" in globals():
      save_data_to_file()

    st.success("✅ Profile updated successfully!")
    st.rerun()

  st.divider()

  # -------------------------------------------------------------
  # 🔑 SECTION 2: EASY PASSWORD & PIN CHANGE
  # -------------------------------------------------------------
  st.subheader("🔑 Security & Account Settings")

  with st.expander("🛡️ Change Password / Security PIN", expanded=True):
    new_pass_input = st.text_input(
        "Set New Password (নতুন পাসওয়ার্ড):",
        value=curr_user.get("password", ""),
        type="password",
    )
    new_pin_input = st.text_input(
        "Set Security PIN (যেকোনো পিন):", value=str(curr_user.get("pin", ""))
    )

    if st.button(
        "💾 Save PIN & Password", key="btn_save_pin_pass", type="primary"
    ):
      updated = False

      # ১. পাসওয়ার্ড নিরাপদ আপডেট
      if new_pass_input.strip():
        curr_user["password"] = new_pass_input.strip()
        updated = True

      # ২. সিকিউরিটি পিন নিরাপদ আপডেট
      if new_pin_input.strip():
        curr_user["pin"] = new_pin_input.strip()
        updated = True

      if updated:
        # সেশন স্টেট ডাটা সিঙ্ক
        if "users" in st.session_state and uname in st.session_state.users:
          st.session_state.users[uname] = curr_user
        st.session_state.curr_user = curr_user

        if "save_data_to_file" in globals():
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

  # সেশন স্টেটে group_chat সেফলি ইনিশিয়ালাইজ করা
  if "group_chat" not in st.session_state:
    st.session_state.group_chat = []

  # ইউজারনেম ও নাম সেফলি হ্যান্ডেল করা
  user_fullname = (
      curr_user.get("full_name", "Unknown")
      if "curr_user" in locals() and isinstance(curr_user, dict)
      else "Unknown Player"
  )
  u_name = (
      curr_username
      if "curr_username" in locals()
      else st.session_state.get("curr_username", "user")
  )

  sender_label = f"{user_fullname} (`@{u_name}`)"

  # পূর্ববর্তী মেসেজগুলো প্রদর্শন
  if not st.session_state.group_chat:
    st.info("👋 No messages yet. Be the first to start the conversation!")
  else:
    for msg in st.session_state.group_chat:
      timestamp = msg.get("timestamp", "")
      sender = msg.get("sender", "Unknown")
      message = msg.get("message", "")

      # চ্যাট সুন্দরভাবে দেখানোর জন্য কাস্টম ফরম্যাট
      st.markdown(f"**[{timestamp}] {sender}:** {message}")

  st.divider()

  # মেসেজ পাঠানোর ইনপুট
  m = st.text_input("Type message...", key="chat_in")

  if st.button("Send Message", key="btn_chat_send", type="primary"):
    if m.strip():
      st.session_state.group_chat.append({
          "sender": sender_label,
          "message": m.strip(),
          "timestamp": datetime.datetime.now().strftime("%I:%M %p"),
      })

      if "save_data_to_file" in globals():
        save_data_to_file()

      st.rerun()
    else:
      st.warning("⚠️ Please type a message before sending.")
        # ==========================================
# 13. FOOTBALL AI (PUBLIC) - LOCAL KNOWLEDGE BASE
# ==========================================
elif nav_choice == "🤖 Football AI (Public)":
  st.header("🤖 Football AI (Public - Tactics Only)")

  # ১. সেশন স্টেট ডাটা সেফলি নিশ্চিতকরণ
  if "football_ai_chats" not in st.session_state:
    st.session_state.football_ai_chats = []
  if "personal_ai_chats" not in st.session_state:
    st.session_state.personal_ai_chats = {}

  # ২. ইউজার ডাটা সেফলি রিড করা
  user_fullname = (
      curr_user.get("full_name", "User")
      if "curr_user" in locals() and isinstance(curr_user, dict)
      else "User"
  )
  user_ai_name = (
      curr_user.get("personal_ai_name", "Personal AI")
      if "curr_user" in locals() and isinstance(curr_user, dict)
      else "Personal AI"
  )
  u_name = (
      curr_username
      if "curr_username" in locals()
      else st.session_state.get("curr_username", "user")
  )

  # ৩. চ্যাট হিস্ট্রি প্রদর্শন
  if not st.session_state.football_ai_chats:
    st.info("💡 Ask any tactical or football strategy questions here.")
  else:
    for chat in st.session_state.football_ai_chats:
      sender_name = chat.get("sender", "User")
      prompt_text = chat.get("prompt", "")
      response_text = chat.get("response", "")

      st.markdown(f"**👤 {sender_name}:** {prompt_text}")
      st.markdown(f"🤖 **Football AI:** {response_text}")
      st.divider()

  # ৪. প্রম্পট ইনপুট ও হ্যান্ডলিং
  p = st.text_input(
      "Ask Football AI regarding tactics/strategies:", key="fai_in"
  )

  if st.button("Ask Football AI", key="btn_fai", type="primary"):
    if p.strip():
      text = p.strip()
      text_lower = text.lower()
      resp = ""

      # Anti-link and Anti-Scraping Feature
      if (
          re.search(r"http[s]?://|www\.", text)
          or "link" in text_lower
          or ("feature" in text_lower and "app" in text_lower)
      ):
        resp = (
            "নিরাপত্তাজনিত কারণে অ্যাপের কোনো লিংক বা অভ্যন্তরীণ ফিচার ও"
            " আর্কিটেকচার বিশ্লেষণ বা প্রকাশ করা নিষিদ্ধ।"
        )

      # ফুটবলের বাইরের প্রশ্ন চেক
      elif any(
          k in text_lower
          for k in [
              "weather",
              "recipe",
              "math",
              "code",
              "movie",
              "song",
              "আবহাওয়া",
              "রান্না",
              "গণিত",
          ]
      ):
        resp = (
            "এটি ফুটবলের বাইরে প্রশ্ন। প্রশ্নটি স্বয়ংক্রিয়ভাবে আপনার"
            f" **Personal AI ({user_ai_name})** পেজে রিডাইরেক্ট করা হলো।"
        )

        st.session_state.personal_ai_chats.setdefault(u_name, []).append({
            "prompt": text,
            "response": (
                f"হ্যালো {user_fullname}! আপনার প্রশ্নটির উত্তর নিয়ে আমি কাজ"
                " করছি।"
            ),
            "timestamp": datetime.datetime.now().strftime("%I:%M %p"),
        })

      # ফুটবল ট্যাকটিক্স ও জ্ঞানভাণ্ডার (Local Knowledge Engine)
      else:
        # ১. ফর্মেশন সম্পর্কিত প্রশ্ন (4-3-3, 4-2-3-1, 3-5-2 ইত্যাদি)
        if any(f in text_lower for f in ["4-3-3", "433"]):
          resp = (
              "**4-3-3 Formation Analysis:** এটি একটি আক্রমণাত্মক"
              " ফর্মেশন। উইঙ্গারদের হাই-পজিশনিং এবং মিডফিল্ডের ত্রিভুজ পাসের"
              " (Triangle passing) মাধ্যমে পজেশন ধরে রাখতে সাহায্য করে। ডিফেন্সে"
              " হাই-প্রেসের জন্য এটি সেরা।"
          )
        elif any(f in text_lower for f in ["4-2-3-1", "4231"]):
          resp = (
              "**4-2-3-1 Formation Analysis:** আধুনিক ফুটবলের অন্যতম সুসংগঠিত"
              " স্ট্রাকচার। দুজন 'Double Pivot' ডিফেন্সিভ মিডফিল্ডার ব্যাকলাইনকে"
              " সুরক্ষা দেয় এবং নম্বর ১০ (CAM) প্লেয়ার আক্রমণের নিয়ন্ত্রণ নেয়।"
          )
        elif any(f in text_lower for f in ["3-5-2", "352", "5-3-2"]):
          resp = (
              "**3-5-2 / Wing-back Dynamics:** মিডফিল্ডের আধিপত্য এবং ওভারল্যাপিং"
              " উইং-ব্যাক দিয়ে প্রতিপক্ষের ওপর চাপ সৃষ্টি করে। ব্যাকলাইনে ৩ জন"
              " সেন্টার ব্যাক থাকায় সেন্ট্রাল ডিফেন্স খুব শক্ত থাকে।"
          )
        elif any(f in text_lower for f in ["4-4-2", "442"]):
          resp = (
              "**Classic 4-4-2:** এটি ট্র্যাডিশনাল ডিফেন্সিভ ব্লকিং এবং কাউন্টার"
              " অ্যাটাকের জন্য দারুণ। দুটি স্ট্রাইকার থাকার কারণে ডায়রেক্ট ফুটবল"
              " খেলতে সুবিধা হয়।"
          )

        # ২. ট্যাকটিক্যাল স্টাইল
        elif any(
            k in text_lower
            for k in ["tiki taka", "tikitaka", "tiki-taka", "টিকিটাকা"]
        ):
          resp = (
              "**Tiki-Taka Tactics:** সংক্ষিপ্ত পাস, দ্রুত পজিশন পরিবর্তন এবং"
              " বল পজেশন ধরে রাখার কৌশল। এর মূল লক্ষ্য হলো পাসিংয়ের মাধ্যমে"
              " প্রতিপক্ষের ডিফেন্সে ফাঁকা জায়গা (Space) তৈরি করা।"
          )
        elif any(
            k in text_lower
            for k in ["gegenpressing", "gegenpress", "গেগেনপ্রেসিং"]
        ):
          resp = (
              "**Gegenpressing (Counter-pressing):** বল হারানোর সাথে সাথে ৩-৫"
              " সেকেন্ডের মধ্যে প্রতিপক্ষকে চেপে ধরে বল পুনরুদ্ধার করার কৌশল।"
              " জার্মানি ও ইয়ুর্গেন ক্লপের দলের অন্যতম প্রধান হাতিয়ার।"
          )
        elif any(
            k in text_lower
            for k in [
                "counter attack",
                "counter-attack",
                "কাউন্টার",
                "fast attack",
            ]
        ):
          resp = (
              "**Counter-Attacking Strategy:** প্রতিপক্ষের আক্রমণ ভেঙে যাওয়ার"
              " সাথে সাথেই দ্রুত উইং দিয়ে দীর্ঘ ও দ্রুত পাসের মাধ্যমে আক্রমণ"
              " চালানো। কম সময়ের মধ্যে গোল করার সবচেয়ে কার্যকর কৌশল।"
          )
        elif any(
            k in text_lower
            for k in ["park the bus", "defensive", "ডিফেন্স", "ডিফেন্সিভ"]
        ):
          resp = (
              "**Low Block / Solid Defense:** নিজের পেনাল্টি বক্সের সামনে শক্ত"
              " প্রতিরক্ষামূলক লাইন তৈরি করে প্রতিপক্ষকে শট নেওয়া থেকে বিরত রাখা।"
              " এটি সাধারণত প্রতিপক্ষ দল শক্তিশালী হলে প্রয়োগ করা হয়।"
          )

        # ৩. প্লেয়ার রোল ও পজিশনিং
        elif any(
            k in text_lower
            for k in ["offside", "offside trap", "অফসাইড", "offside rule"]
        ):
          resp = (
              "**Offside Rule & Trap:** আক্রমণকারী খেলোয়াড় বল পাস করার মুহূর্তে"
              " প্রতিপক্ষের শেষ দুজন খেলোয়াড়ের (গোলরক্ষকসহ) সামনে থাকলে তা"
              " অফসাইড। ডিফেন্ডাররা একলাইনে উঠে প্রতিপক্ষকে অফসাইড ট্র্যাপে ফেলার"
              " কৌশল ব্যবহার করে।"
          )
        elif any(
            k in text_lower
            for k in [
                "inverted winger",
                "winger",
                "উইঙ্গার",
                "wing back",
                "wingback",
            ]
        ):
          resp = (
              "**Inverted Winger Dynamics:** ডানপায়ের প্লেয়ার বাম উইঙে বা"
              " বামপায়ের প্লেয়ার ডান উইঙে খেলে ইনসাইডে কাট-ইন (Cut-in) করে শট"
              " নিতে সাহায্য করে। ওভারল্যাপিং ফুলব্যাকদের জন্য জায়গা তৈরি করতে এটি"
              " দারুণ।"
          )
        elif any(
            k in text_lower
            for k in ["false 9", "false9", "ফোল্স নাইন", "false nine"]
        ):
          resp = (
              "**False 9 Role:** সেন্ট্রাল স্ট্রাইকার বক্সের ভেতর না থেকে"
              " মিডফিল্ডে নেমে আসে। এর ফলে প্রতিপক্ষের সেন্টার-ব্যাকরা বিভ্রান্ত"
              " হয় এবং উইঙ্গারদের জন্য বক্সে ঢোকার খালি জায়গা তৈরি হয়।"
          )

        # ৪. সাধারণ ফুটবল ট্যাকটিক্স (ডিফল্ট স্ট্র্যাটেজিক উত্তর)
        else:
          resp = (
              f"**'{text}' সম্পর্কিত ট্যাকটিক্যাল টিপস:**\n"
              "১. **Formational Line:** ফর্মেশন কমপ্যাক্ট রাখুন যেন সেন্ট্রাল স্পেস"
              " বন্ধ থাকে।\n"
              "২. **Pressing Zone:** মিড-ব্লকে প্রেস তৈরি করে বল পুনরুদ্ধার করুন।\n"
              "৩. **Transition:** দ্রুত উইং প্লেয়ারদের ব্যবহার করে কাউন্টার"
              " অ্যাটাকে যান।"
          )

      # চ্যাট হিস্ট্রিতে সেভ ও রান করা
      st.session_state.football_ai_chats.append({
          "sender": user_fullname,
          "prompt": text,
          "response": resp,
          "timestamp": datetime.datetime.now().strftime("%I:%M %p"),
      })

      if "save_data_to_file" in globals():
        save_data_to_file()

      st.rerun()
    else:
      st.warning("⚠️ Please enter a question first.")
        # ==========================================
# 14. PERSONAL AI & MOTM VOTING (LOCAL KNOWLEDGE ENGINE)
# ==========================================
elif nav_choice == "👤 Personal AI (Private)":
  # ১. ইউজার ডাটা সেফলি রিড করা
  user_obj = (
      curr_user
      if "curr_user" in locals() and isinstance(curr_user, dict)
      else st.session_state.get("curr_user", {})
  )
  u_name = (
      curr_username
      if "curr_username" in locals()
      else st.session_state.get("curr_username", "user")
  )

  pai_name = user_obj.get("personal_ai_name", "Personal AI")
  user_fullname = user_obj.get("full_name", "User")

  st.header(f"👤 {pai_name} (Private AI)")

  # ২. সেশন স্টেট ডাটা সেফলি নিশ্চিতকরণ
  if "personal_ai_chats" not in st.session_state:
    st.session_state.personal_ai_chats = {}
  if "motm_votes" not in st.session_state:
    st.session_state.motm_votes = {}

  user_pchats = st.session_state.personal_ai_chats.setdefault(u_name, [])

  # ৩. চ্যাট হিস্ট্রি প্রদর্শন
  if not user_pchats:
    st.info(f"👋 Hi {user_fullname}! Ask me anything you need help with.")
  else:
    for chat in user_pchats:
      prompt_text = chat.get("prompt", "")
      response_text = chat.get("response", "")

      st.markdown(f"**You:** {prompt_text}")
      st.markdown(f"🤖 **{pai_name}:** {response_text}")
      st.divider()

  # ৪. প্রম্পট ইনপুট ও হ্যান্ডলিং
  p = st.text_input(f"Ask {pai_name} anything:", key="pai_in")

  if st.button("Send", key="btn_pai", type="primary"):
    if p.strip():
      text = p.strip()
      text_lower = text.lower()
      resp = ""

      # Anti-link and Anti-Scraping Feature
      if re.search(r"http[s]?://|www\.", text) or (
          "link" in text_lower and "feature" in text_lower
      ):
        resp = (
            "দুঃখিত, কোনো অ্যাপ লিংক থেকে তথ্য বা ফিচার বিশ্লেষণ করা আমার জন্য"
            " নিষিদ্ধ।"
        )
      else:
        # --- LOCAL GENERAL INTEL ASSISTANT ---

        # ১. সাধারণ অভিবাদন ও কুশল বিনিময়
        if any(
            k in text_lower
            for k in [
                "hi",
                "hello",
                "কেমন আছ",
                "কেমন আছেন",
                "হ্যালো",
                "হাই",
                "assalamu alaikum",
                "সালাম",
            ]
        ):
          resp = (
              f"হ্যালো {user_fullname}! আমি আপনার পার্সোনাল অ্যাসিস্ট্যান্ট"
              f" **{pai_name}**। আমি আপনাকে যেকোনো সাধারণ প্রশ্ন, প্ল্যানিং বা"
              " পড়াশোনায় সাহায্য করতে পারি। বলুন, আজ কীভাবে সাহায্য করতে পারি?"
          )

        # ২. পরিচয় বা নাম সম্পর্কিত প্রশ্ন
        elif any(
            k in text_lower
            for k in [
                "who are you",
                "your name",
                "তোমার নাম",
                "তুমি কে",
                "পরিচয়",
            ]
        ):
          resp = (
              f"আমি **{pai_name}**, আপনার নিজস্ব স্মার্ট পার্সোনাল AI"
              " অ্যাসিস্ট্যান্ট। আপনার দৈনন্দিন কাজ, পরামর্শ এবং যেকোনো সাধারণ"
              " প্রশ্নের উত্তর দেওয়ার জন্য আমি প্রস্তুত।"
          )

        # ৩. সময়, রুটিন বা প্ল্যানিং
        elif any(
            k in text_lower
            for k in [
                "routine",
                "plan",
                "schedule",
                "রুটিন",
                "প্ল্যান",
                "সময়সূচী",
                "time management",
            ]
        ):
          resp = (
              f"প্রিয় {user_fullname}, একটি ভালো রুটিনের জন্য প্রতিদিনের কাজকে"
              " ৩টি ধাপে ভাগ করুন:\n"
              "১. **Most Important Tasks (MITs):** সকালে সবচেয়ে জরুরি ২টি কাজ শেষ"
              " করুন।\n"
              "২. **Pomodoro Focus:** ২৫ মিনিট মনোযোগ দিয়ে কাজ করে ৫ মিনিট বিরতি"
              " নিন।\n"
              "৩. **Review:** দিন শেষে ১০ মিনিট পুরো দিনের কাজের হিসাব করুন।"
          )

        # ৪. ফিটনেস ও স্বাস্থ্য টিপস
        elif any(
            k in text_lower
            for k in [
                "fitness",
                "diet",
                "exercise",
                "health",
                "স্বাস্থ্য",
                "ব্যায়াম",
                "খাবার",
                "ওজন",
            ]
        ):
          resp = (
              "**স্বাস্থ্যকর লাইফস্টাইল টিপস:**\n"
              "• **হাইড্রেটেড থাকুন:** প্রতিদিন অন্তত ২.৫ থেকে ৩ লিটার পানি পান"
              " করুন।\n"
              "• **নিয়মিত শরীরচর্চা:** প্রতিদিন অন্তত ২০-৩০ মিনিট হাঁটা বা হালকা"
              " ফ্রি-হ্যান্ড এক্সারসাইজ করুন।\n"
              "• **পরিমিত ঘুম:** রাতে ৭-৮ ঘণ্টা সুনিদ্রা নিশ্চিত করুন।"
          )

        # ৫. টেকনোলজি, স্টাডি বা কোডিং টিপস
        elif any(
            k in text_lower
            for k in [
                "study",
                "code",
                "programming",
                "python",
                "পড়াশোনা",
                "পড়াশোনা",
                "কৌশল",
            ]
        ):
          resp = (
              "**কার্যকর শেখার কৌশল (Feynman Technique):**\n"
              "১. যেকোনো বিষয় সহজ ভাষায় অন্য কাউকে বোঝানোর চেষ্টা করুন।\n"
              "২. যেখানে আটকে যাবেন, সেখানে মূল সোর্স বা বই দেখে কনসেপ্ট ক্লিয়ার"
              " করুন।\n"
              "৩. শেখার সাথে সাথে ছোট ছোট প্র্যাকটিক্যাল প্রজেক্ট তৈরি করুন।"
          )

        # ৬. মোটিভেশন ও মানসিক মানসিক উদ্দীপনা
        elif any(
            k in text_lower
            for k in [
                "motivation",
                "depressed",
                "sad",
                "সহায়তা",
                "হতাশ",
                "ধৈর্য",
                "ইনস্পায়ার",
            ]
        ):
          resp = (
              f"মনে রাখবেন {user_fullname}, সফলতা একদিনে আসে না। ছোট ছোট ধারাবাহিক"
              " চেষ্টাই একদিন বড় পরিবর্তন আনে। আজকের দিনটিকে নিজের সেরাটা দিয়ে"
              " কাজে লাগান!"
          )

        # ৭. অন্যান্য সাধারণ প্রশ্নের অল-রাউন্ড ব্যাকআপ
        else:
          resp = (
              f"হ্যালো {user_fullname}! আপনার প্রশ্ন: **'{text}'**।\n\n"
              f"আমি **{pai_name}**—আপনার এই প্রশ্নের বিষয়ে পরামর্শ হলো: যেকোনো"
              " কাজের সফলতা নির্ভর করে সঠিক পরিকল্পনা এবং ধারাবাহিক চেষ্টার ওপর।"
              " এ বিষয়ে আরও নির্দিষ্ট কোনো তথ্য জানতে চাইলে আমাকে নির্দ্বিধায়"
              " বলুন!"
          )

      user_pchats.append({
          "prompt": text,
          "response": resp,
          "timestamp": datetime.datetime.now().strftime("%I:%M %p"),
      })

      if "save_data_to_file" in globals():
        save_data_to_file()

      st.rerun()
    else:
      st.warning("⚠️ Please type a message before sending.")

  st.divider()

  # -------------------------------------------------------------
  # 🗳️ SUNDAY MOTM POLL
  # -------------------------------------------------------------
  st.subheader("🗳️ Sunday MOTM Poll")

  # একটিভ ইউজার সেফলি লোড
  if "get_active_unblocked_users" in globals():
    active_users = get_active_unblocked_users()
  else:
    active_users = st.session_state.get("users", {})

  if not active_users:
    st.info("No active users available for voting.")
  else:
    vote = st.selectbox(
        "Vote MOTM:",
        options=list(active_users.keys()),
        format_func=lambda x: (
            f"{active_users[x].get('full_name', x)} (`@{x}`)"
        ),
        key="motm_sel",
    )

    if st.button("Submit Vote", key="btn_motm"):
      st.session_state.motm_votes[u_name] = vote

      if "save_data_to_file" in globals():
        save_data_to_file()

      st.success(f"✅ Vote cast successfully for @{vote}!")
        
# ==========================================
# 15. ADMIN CONTROL PANEL (FIXED & ULTRA-SAFE)
# ==========================================
elif nav_choice == "⚙️ Admin Control Panel":
  st.header("⚙️ Admin Control Panel")

  # সেফ ইউজার ও রোল চেকিং
  admin_user = (
      curr_user
      if "curr_user" in locals() and isinstance(curr_user, dict)
      else st.session_state.get("curr_user", {})
  )
  user_role = admin_user.get("role", "Member")

  if user_role not in ["Superadmin", "Admin"]:
    st.error("🚫 Access Denied. Admin or Superadmin privileges required.")
    st.stop()

  # সেশন স্টেট কী-সমূহ ডাইনামিক ইনিশিয়ালাইজেশন
  if "app_settings" not in st.session_state:
    st.session_state.app_settings = {
        "app_name": "Club Manager",
        "max_register_limit": 50,
        "club_photo_b64": "",
    }
  if "users" not in st.session_state:
    st.session_state.users = {}
  if "match_settings" not in st.session_state:
    st.session_state.match_settings = {"goals_conceded": 0}
  if "player_stats" not in st.session_state:
    st.session_state.player_stats = {}
  if "injured_players" not in st.session_state:
    st.session_state.injured_players = []
  if "notice_board" not in st.session_state:
    st.session_state.notice_board = []

  t1, t2, t3, t4, t5, t6, t7 = st.tabs([
      "🎨 Branding & Limit",
      "👑 Roles & Password",
      "🚫 Block System",
      "📊 Match Stats & GK Saves",
      "📋 Player Attendance",
      "📢 Notice & Poll",
      "🧹 Master Reset",
  ])

  # -------------------------------------------------------------
  # TAB 1: BRANDING & LIMIT
  # -------------------------------------------------------------
  with t1:
    st.subheader("🎨 Club Branding & Registration Settings")
    st.session_state.app_settings["app_name"] = st.text_input(
        "App Name:",
        st.session_state.app_settings.get("app_name", "Club Manager"),
    )

    curr_limit = int(
        st.session_state.app_settings.get("max_register_limit", 50)
    )
    st.session_state.app_settings["max_register_limit"] = st.number_input(
        "Max Member Limit:", 1, 500, curr_limit
    )

    cpic = st.file_uploader(
        "Upload Club Logo/Photo:", type=["jpg", "png", "jpeg"]
    )
    if cpic:
      st.session_state.app_settings["club_photo_b64"] = base64.b64encode(
          cpic.read()
      ).decode("utf-8")

    if st.button("Save Settings", key="btn_save_brand", type="primary"):
      if "save_data_to_file" in globals():
        save_data_to_file()
      st.success("✅ Branding and settings updated!")

  # -------------------------------------------------------------
  # TAB 2: ROLES & PASSWORD
  # -------------------------------------------------------------
  with t2:
    st.subheader("👑 Assign Position & Forced Password Reset")
    user_list = list(st.session_state.users.keys())

    if not user_list:
      st.info("No registered users found.")
    else:
      target_u = st.selectbox("Select User:", user_list, key="adm_u_sel")
      pos_options = [
          "GK",
          "CB",
          "LB",
          "RB",
          "RCM",
          "LCM",
          "CAM",
          "RW",
          "LW",
          "ST",
      ]
      curr_pos = st.session_state.users[target_u].get("position", "CB")
      default_pos_idx = (
          pos_options.index(curr_pos) if curr_pos in pos_options else 0
      )

      new_pos = st.selectbox(
          "Assign Position:", pos_options, index=default_pos_idx
      )
      if st.button("Update Position", key="btn_adm_pos"):
        st.session_state.users[target_u]["position"] = new_pos
        if "save_data_to_file" in globals():
          save_data_to_file()
        st.success(f"✅ Position for @{target_u} updated to {new_pos}!")

      if user_role == "Superadmin":
        st.divider()
        st.markdown("### 🔑 Force Change User Password")
        new_pass = st.text_input(
            "Set New Password:", type="password", key="adm_fpass"
        )
        if st.button("Force Change Password", key="btn_fpass", type="primary"):
          if new_pass.strip():
            st.session_state.users[target_u]["password"] = new_pass.strip()
            if "save_data_to_file" in globals():
              save_data_to_file()
            st.success(f"✅ Password for @{target_u} changed successfully!")
          else:
            st.error("Password cannot be empty.")

  # -------------------------------------------------------------
  # TAB 3: BLOCK SYSTEM
  # -------------------------------------------------------------
  with t3:
    st.subheader("🚫 User Block / Unblock Management")
    user_list = list(st.session_state.users.keys())

    if not user_list:
      st.info("No users available to manage.")
    else:
      btarget = st.selectbox(
          "Target Player to Block/Unblock:", user_list, key="bsel"
      )
      breason = st.text_input("Reason for Block (Mandatory):", key="breas")

      col_b1, col_b2 = st.columns(2)
      with col_b1:
        if st.button("🚫 Block Player", key="btn_blk", type="primary"):
          if breason.strip():
            u = st.session_state.users[btarget]
            u["status"] = "Blocked"
            u["block_reason"] = breason.strip()
            if "save_data_to_file" in globals():
              save_data_to_file()
            st.warning(f"🚨 Player @{btarget} has been blocked.")
            st.rerun()
          else:
            st.error("⚠️ Block reason is mandatory!")

      with col_b2:
        if st.button("✅ Unblock Player", key="btn_unblk"):
          st.session_state.users[btarget]["status"] = "Active"
          st.session_state.users[btarget].pop("block_reason", None)
          if "save_data_to_file" in globals():
            save_data_to_file()
          st.success(f"✅ Player @{btarget} has been unblocked.")
          st.rerun()

    st.divider()
    st.subheader("📜 Blocked Players List & Last Messages")
    blocked_found = False

    for bu, bd in st.session_state.users.items():
      if bd.get("status") == "Blocked":
        blocked_found = True
        st.error(
            f"🚨 **{bd.get('full_name', bu)}** (`@{bu}`) — Reason:"
            f" {bd.get('block_reason', 'N/A')}"
        )

        # গত মেসেজ খুঁজে আনা
        user_msgs = [
            msg
            for msg in st.session_state.get("group_chat", [])
            if msg.get("sender", "").endswith(f"(@{bu})") or bu in msg.get("sender", "")
        ]

        if user_msgs:
          last_msg = user_msgs[-1]
          st.info(
              f"💬 **Last Message:** \"{last_msg.get('message', last_msg.get('text', ''))}\""
              f" — *(Sent at {last_msg.get('timestamp', 'N/A')})*"
          )
        else:
          st.caption("💬 No messages found from this user.")
        st.divider()

    if not blocked_found:
      st.info("No blocked players currently.")

  # -------------------------------------------------------------
  # TAB 4: MATCH STATS & GK SAVES
  # -------------------------------------------------------------
  with t4:
    st.subheader("⚽ Match Stats, GK Saves & Conceded Goals")
    curr_gc = int(st.session_state.match_settings.get("goals_conceded", 0))
    st.session_state.match_settings["goals_conceded"] = st.number_input(
        "Match Goals Conceded (Team):", 0, 20, curr_gc
    )

    user_list = list(st.session_state.users.keys())
    if not user_list:
      st.info("No users available for updating stats.")
    else:
      stat_u = st.selectbox("Select Player:", user_list, key="stat_u_sel")
      pstats = st.session_state.player_stats.setdefault(
          stat_u,
          {
              "goals": 0,
              "assists": 0,
              "conceded_penalty": 0.0,
              "attendance": "Present",
              "rating_penalty": 0.0,
              "gk_saves": 0,
          },
      )

      c1, c2, c3 = st.columns(3)
      with c1:
        pstats["goals"] = st.number_input(
            "Goals:", 0, 50, int(pstats.get("goals", 0))
        )
      with c2:
        pstats["assists"] = st.number_input(
            "Assists:", 0, 50, int(pstats.get("assists", 0))
        )
      with c3:
        pstats["gk_saves"] = st.number_input(
            "GK Saves:", 0, 50, int(pstats.get("gk_saves", 0))
        )

      if st.button("Save Stats", key="btn_sav_stats", type="primary"):
        if "save_data_to_file" in globals():
          save_data_to_file()
        st.success(f"✅ Match stats updated for @{stat_u}!")

  # -------------------------------------------------------------
  # TAB 5: PLAYER ATTENDANCE
  # -------------------------------------------------------------
  with t5:
    st.subheader("📋 Daily Player Attendance Sheet")
    st.caption(
        f"📅 Date: **{datetime.date.today().strftime('%B %d, %Y')}**"
    )

    active_users = (
        get_active_unblocked_users()
        if "get_active_unblocked_users" in globals()
        else {
            k: v
            for k, v in st.session_state.users.items()
            if v.get("status") != "Blocked"
        }
    )

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
            st.markdown(
                f"**{user_info.get('full_name', username)}** (`@{username}`)"
            )
          with col2:
            st.markdown(f"`{user_info.get('position', 'N/A')}`")
          with col3:
            current_status = (
                st.session_state.player_stats.get(username, {}).get(
                    "attendance", "Present"
                )
            )
            status_options = ["Present", "Absent", "Late", "Injured"]
            default_idx = (
                status_options.index(current_status)
                if current_status in status_options
                else 0
            )

            selected_status = st.radio(
                f"Att_{username}",
                options=status_options,
                index=default_idx,
                key=f"tab_att_radio_{username}",
                horizontal=True,
                label_visibility="collapsed",
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

          if "save_data_to_file" in globals():
            save_data_to_file()
          st.success("✅ Attendance updated successfully!")
          st.rerun()

  # -------------------------------------------------------------
  # TAB 6: NOTICE & POLL
  # -------------------------------------------------------------
  with t6:
    st.subheader("📌 Admin Announcement & Voting Tool")

    action_type = st.radio(
        "Select Action:",
        ["Create Notice", "Create Poll"],
        horizontal=True,
        key="admin_notice_poll_radio",
    )

    if action_type == "Create Notice":
      with st.form("admin_create_notice_form"):
        n_title = st.text_input("Notice Title:")
        n_content = st.text_area("Notice Details:")

        if st.form_submit_button("📢 Publish Notice", type="primary"):
          if n_title.strip() and n_content.strip():
            author_label = (
                f"{admin_user.get('full_name', 'Admin')} ({user_role})"
            )

            st.session_state.notice_board.append({
                "id": len(st.session_state.notice_board) + 1,
                "author": author_label,
                "title": n_title.strip(),
                "content": n_content.strip(),
                "is_poll": False,
                "timestamp": datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "comments": [],
            })
            if "save_data_to_file" in globals():
              save_data_to_file()
            st.success("✅ Notice successfully published to Notice Board!")
            st.rerun()
          else:
            st.error("Please fill in both title and content.")

    elif action_type == "Create Poll":
      with st.form("admin_create_poll_form"):
        p_question = st.text_input("Poll Question / Title:")
        p_options_raw = st.text_area(
            "Options (Enter each option on a new line):", value="Yes\nNo"
        )

        if st.form_submit_button("📊 Publish Poll", type="primary"):
          options = [
              opt.strip() for opt in p_options_raw.split("\n") if opt.strip()
          ]
          if p_question.strip() and len(options) >= 2:
            author_label = (
                f"{admin_user.get('full_name', 'Admin')} ({user_role})"
            )

            st.session_state.notice_board.append({
                "id": len(st.session_state.notice_board) + 1,
                "author": author_label,
                "title": f"📊 Poll: {p_question.strip()}",
                "content": p_question.strip(),
                "is_poll": True,
                "poll_options": options,
                "poll_votes": {},
                "timestamp": datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "comments": [],
            })
            if "save_data_to_file" in globals():
              save_data_to_file()
            st.success("✅ Poll successfully published to Notice Board!")
            st.rerun()
          else:
            st.error("Please provide a question and at least 2 options.")

  # -------------------------------------------------------------
  # TAB 7: MASTER RESET
  # -------------------------------------------------------------
  with t7:
    st.subheader("🧹 Master Reset Options")
    if user_role == "Superadmin":
      st.warning(
          "⚠️ Warning: Master Reset will clear all chat logs, public AI"
          " chats, and private AI conversations."
      )
      if st.button("🔥 EXECUTE MASTER RESET", key="btn_mr", type="primary"):
        st.session_state.group_chat = []
        st.session_state.football_ai_chats = []
        st.session_state.personal_ai_chats = {}

        if "save_data_to_file" in globals():
          save_data_to_file()

        st.success("✅ Master Reset completed successfully!")
        st.rerun()
    else:
      st.info("🔒 Master Reset option is strictly reserved for Superadmin only.")
