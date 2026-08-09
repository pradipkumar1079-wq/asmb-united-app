import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

DB_FILE = "club_data.json"

class ClubApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Club Management System")
        self.root.geometry("850x650")
        self.root.configure(bg="#f4f6f9")

        # Database structure initialization
        self.db = {
            "users": [],
            "notices": [],
            "chats": [],
            "ai_chats": [],
            "match_stats": {"goals": [], "conceded": [], "last_motm": ""}
        }
        self.current_user = None
        self.load_data()

        # Custom ttk Styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('.', font=('Segoe UI', 10), background="#f4f6f9")
        self.style.configure('TNotebook.Tab', padding=[12, 6], font=('Segoe UI', 10, 'bold'))
        self.style.configure('Header.TLabel', font=('Segoe UI', 14, 'bold'), background="#f4f6f9")

        # Main Containers
        self.auth_frame = ttk.Frame(self.root, padding="20")
        self.main_frame = ttk.Frame(self.root, padding="10")

        self.setup_auth_ui()
        self.setup_main_ui()

        # Show Auth Screen initially
        self.auth_frame.pack(expand=True, fill="both")

    # ==================== DATA PERSISTENCE ====================
    def load_data(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    self.db = json.load(f)
            except Exception as e:
                print("Error loading database:", e)

    def save_data(self):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(self.db, f, indent=4, ensure_ascii=False)

    def calculate_star_players(self):
        # Top 5 players with highest MOTM count get Star Player status
        for u in self.db["users"]:
            u["is_star"] = False

        active_users = [u for u in self.db["users"] if not u.get("is_blocked", False) and u.get("motm_count", 0) > 0]
        sorted_users = sorted(active_users, key=lambda x: x.get("motm_count", 0), reverse=True)[:5]
        
        star_ids = [u["id"] for u in sorted_users]
        for u in self.db["users"]:
            if u["id"] in star_ids:
                u["is_star"] = True
        self.save_data()

    # ==================== AUTH UI & LOGIC ====================
    def setup_auth_ui(self):
        ttk.Label(self.auth_frame, text="Club Management Login / Register", style='Header.TLabel').pack(pady=15)

        form = ttk.Frame(self.auth_frame)
        form.pack(pady=10)

        ttk.Label(form, text="User ID / Username:").grid(row=0, column=0, sticky="w", pady=5)
        self.username_ent = ttk.Entry(form, width=30)
        self.username_ent.grid(row=0, column=1, pady=5)

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="w", pady=5)
        self.password_ent = ttk.Entry(form, width=30, show="*")
        self.password_ent.grid(row=1, column=1, pady=5)

        btn_frame = ttk.Frame(self.auth_frame)
        btn_frame.pack(pady=15)

        ttk.Button(btn_frame, text="Login", command=self.login).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Register", command=self.register).pack(side="left", padx=5)

    def register(self):
        username = self.username_ent.get().strip()
        password = self.password_ent.get().strip()

        if not username or not password:
            messagebox.showwarning("Warning", "All fields are required!")
            return

        if any(u['username'] == username for u in self.db['users']):
            messagebox.showerror("Error", "User ID already exists!")
            return

        # Check if first user -> S.A automatically
        is_first = len(self.db['users']) == 0
        role = 's.a' if is_first else 'user'

        new_user = {
            "id": len(self.db['users']) + 1,
            "username": username,
            "password": password,
            "role": role,
            "is_blocked": False,
            "position": "Unassigned",
            "motm_count": 0,
            "practice_only": False,
            "is_star": False
        }

        self.db['users'].append(new_user)
        self.save_data()
        messagebox.showinfo("Success", f"Registration successful!\nRole Assigned: {role.upper()}")
        self.username_ent.delete(0, tk.END)
        self.password_ent.delete(0, tk.END)

    def login(self):
        username = self.username_ent.get().strip()
        password = self.password_ent.get().strip()

        user = next((u for u in self.db['users'] if u['username'] == username and u['password'] == password), None)

        if not user:
            messagebox.showerror("Error", "Invalid Username or Password!")
            return

        if user.get("is_blocked", False):
            messagebox.showerror("Blocked", "Your account is BLOCKED! You cannot login without S.A/Admin permission.")
            return

        self.current_user = user
        self.calculate_star_players()
        
        self.auth_frame.pack_forget()
        self.main_frame.pack(expand=True, fill="both")
        self.refresh_dashboard()

    def logout(self):
        self.current_user = None
        self.main_frame.pack_forget()
        self.auth_frame.pack(expand=True, fill="both")
        self.username_ent.delete(0, tk.END)
        self.password_ent.delete(0, tk.END)

    # ==================== MAIN DASHBOARD UI & LOGIC ====================
    def setup_main_ui(self):
        # User Header Profile Bar
        self.profile_bar = ttk.Frame(self.main_frame, padding="5")
        self.profile_bar.pack(fill="x", pady=5)

        self.user_info_lbl = ttk.Label(self.profile_bar, text="", font=('Segoe UI', 10, 'bold'))
        self.user_info_lbl.pack(side="left")

        ttk.Button(self.profile_bar, text="Logout", command=self.logout).pack(side="right")

        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(expand=True, fill="both", pady=5)

        # Tab 1: Notice
        self.tab_notice = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_notice, text="Notices")
        self.setup_notice_tab()

        # Tab 2: Player List & Squad
        self.tab_players = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_players, text="Player List")
        self.setup_players_tab()

        # Tab 3: Group Chat
        self.tab_chat = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_chat, text="Group Chat")
        self.setup_chat_tab()

        # Tab 4: AI Chat
        self.tab_ai = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_ai, text="AI Chat")
        self.setup_ai_tab()

        # Tab 5: Main Match
        self.tab_match = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_match, text="Main Match")
        self.setup_match_tab()

        # Tab 6: Admin Panel
        self.tab_admin = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_admin, text="Admin Panel")
        self.setup_admin_tab()

    def refresh_dashboard(self):
        # Update User Info Text
        u = self.current_user
        star_str = "⭐ [STAR PLAYER]" if u.get("is_star") else ""
        practice_str = "[Practice Only]" if u.get("practice_only") else ""
        self.user_info_lbl.config(
            text=f"User: {u['username']} | Role: {u['role'].upper()} | Position: {u['position']} {star_str} {practice_str}"
        )

        # Practice Match Only Player Restriction
        if u.get("practice_only", False):
            self.notebook.hide(self.tab_match)
        else:
            self.notebook.add(self.tab_match, text="Main Match")

        # Admin Tab Visibility
        if u['role'] in ['s.a', 'a']:
            self.notebook.add(self.tab_admin, text="Admin Panel")
        else:
            self.notebook.hide(self.tab_admin)

        # S.A / Admin Notice Form Visibility
        if u['role'] in ['s.a', 'a']:
            self.notice_post_frame.pack(fill="x", pady=10)
        else:
            self.notice_post_frame.pack_forget()

        # S.A Master Reset & Match Control Visibility
        if u['role'] == 's.a':
            self.sa_master_frame.pack(fill="x", pady=5)
            self.sa_match_controls.pack(fill="both", expand=True, pady=10)
        else:
            self.sa_master_frame.pack_forget()
            self.sa_match_controls.pack_forget()

        self.render_notices()
        self.render_player_list()
        self.render_chats()
        self.render_admin_panel()
        self.populate_match_options()

    # ==================== NOTICES ====================
    def setup_notice_tab(self):
        self.notice_listbox = tk.Text(self.tab_notice, height=15, state="disabled", font=('Segoe UI', 10))
        self.notice_listbox.pack(fill="both", expand=True, pady=5)

        self.notice_post_frame = ttk.LabelFrame(self.tab_notice, text="Post Notice (S.A / Admin Only)", padding="10")
        self.notice_txt = ttk.Entry(self.notice_post_frame, width=50)
        self.notice_txt.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(self.notice_post_frame, text="Post", command=self.post_notice).pack(side="right")

    def post_notice(self):
        text = self.notice_txt.get().strip()
        if not text:
            return
        notice_data = {
            "author": self.current_user['username'],
            "role": self.current_user['role'],
            "text": text,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.db['notices'].append(notice_data)
        self.save_data()
        self.notice_txt.delete(0, tk.END)
        self.render_notices()

    def render_notices(self):
        self.notice_listbox.config(state="normal")
        self.notice_listbox.delete("1.0", tk.END)
        for n in reversed(self.db['notices']):
            self.notice_listbox.insert(tk.END, f"[{n['date']}] {n['author']} ({n['role'].upper()}):\n{n['text']}\n" + "-"*50 + "\n")
        self.notice_listbox.config(state="disabled")

    # ==================== PLAYER LIST ====================
    def setup_players_tab(self):
        ttk.Label(self.tab_players, text="Active Players & Squad List (Blocked Players Excluded)", font=('Segoe UI', 11, 'bold')).pack(anchor="w", pady=5)
        self.player_text = tk.Text(self.tab_players, height=20, state="disabled")
        self.player_text.pack(fill="both", expand=True)

    def render_player_list(self):
        self.player_text.config(state="normal")
        self.player_text.delete("1.0", tk.END)
        active_players = [u for u in self.db['users'] if not u.get('is_blocked', False)]

        for u in active_players:
            star_tag = " ⭐ [STAR PLAYER]" if u.get("is_star") else ""
            practice_tag = " [Practice Only]" if u.get("practice_only") else ""
            line = f"• {u['username']} | Role: {u['role'].upper()} | Position: {u['position']} | MOTM: {u.get('motm_count', 0)}{star_tag}{practice_tag}\n"
            self.player_text.insert(tk.END, line)
        self.player_text.config(state="disabled")

    # ==================== CHATS ====================
    def setup_chat_tab(self):
        self.chat_display = tk.Text(self.tab_chat, height=15, state="disabled")
        self.chat_display.pack(fill="both", expand=True, pady=5)

        input_frame = ttk.Frame(self.tab_chat)
        input_frame.pack(fill="x", pady=5)
        self.chat_entry = ttk.Entry(input_frame)
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(input_frame, text="Send", command=self.send_chat).pack(side="right")

    def send_chat(self):
        msg = self.chat_entry.get().strip()
        if not msg:
            return
        self.db['chats'].append({"user": self.current_user['username'], "msg": msg})
        self.save_data()
        self.chat_entry.delete(0, tk.END)
        self.render_chats()

    def setup_ai_tab(self):
        self.ai_display = tk.Text(self.tab_ai, height=15, state="disabled")
        self.ai_display.pack(fill="both", expand=True, pady=5)

        input_frame = ttk.Frame(self.tab_ai)
        input_frame.pack(fill="x", pady=5)
        self.ai_entry = ttk.Entry(input_frame)
        self.ai_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(input_frame, text="Ask AI", command=self.send_ai_chat).pack(side="right")

    def send_ai_chat(self):
        msg = self.ai_entry.get().strip()
        if not msg:
            return
        reply = f"AI: Thanks for your query regarding '{msg}'. (AI cannot set star players or positions)."
        self.db['ai_chats'].append({"user": self.current_user['username'], "msg": msg, "reply": reply})
        self.save_data()
        self.ai_entry.delete(0, tk.END)
        self.render_chats()

    def render_chats(self):
        # Group Chat
        self.chat_display.config(state="normal")
        self.chat_display.delete("1.0", tk.END)
        for c in self.db['chats']:
            self.chat_display.insert(tk.END, f"{c['user']}: {c['msg']}\n")
        self.chat_display.config(state="disabled")

        # AI Chat
        self.ai_display.config(state="normal")
        self.ai_display.delete("1.0", tk.END)
        for c in self.db['ai_chats']:
            self.ai_display.insert(tk.END, f"You: {c['msg']}\n{c['reply']}\n" + "-"*40 + "\n")
        self.ai_display.config(state="disabled")

    # ==================== MAIN MATCH ====================
    def setup_match_tab(self):
        self.match_info_lbl = ttk.Label(self.tab_match, text="Main Match Overview", font=('Segoe UI', 12, 'bold'))
        self.match_info_lbl.pack(anchor="w", pady=5)

        self.match_stats_display = tk.Text(self.tab_match, height=5, state="disabled")
        self.match_stats_display.pack(fill="x", pady=5)

        # S.A Only Match Editing Frame
        self.sa_match_controls = ttk.LabelFrame(self.tab_match, text="Update Main Match Stats (S.A Only)", padding="10")

        grid_frame = ttk.Frame(self.sa_match_controls)
        grid_frame.pack(fill="x", expand=True)

        ttk.Label(grid_frame, text="Select Goal Scorers (Multiple):").grid(row=0, column=0, sticky="w")
        self.goals_box = tk.Listbox(grid_frame, selectmode=tk.MULTIPLE, height=5, exportselection=False)
        self.goals_box.grid(row=1, column=0, padx=5, pady=5)

        ttk.Label(grid_frame, text="Select Goal Conceded (Multiple):").grid(row=0, column=1, sticky="w")
        self.conceded_box = tk.Listbox(grid_frame, selectmode=tk.MULTIPLE, height=5, exportselection=False)
        self.conceded_box.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(grid_frame, text="Select MOTM:").grid(row=0, column=2, sticky="w")
        self.motm_box = tk.Listbox(grid_frame, selectmode=tk.SINGLE, height=5, exportselection=False)
        self.motm_box.grid(row=1, column=2, padx=5, pady=5)

        ttk.Button(self.sa_match_controls, text="Save Match Stats", command=self.save_match_stats).pack(pady=10)

    def populate_match_options(self):
        active_players = [u for u in self.db['users'] if not u.get('is_blocked', False) and not u.get('practice_only', False)]

        self.goals_box.delete(0, tk.END)
        self.conceded_box.delete(0, tk.END)
        self.motm_box.delete(0, tk.END)

        for u in active_players:
            self.goals_box.insert(tk.END, u['username'])
            self.conceded_box.insert(tk.END, u['username'])
            self.motm_box.insert(tk.END, u['username'])

        # Display Current Stats
        self.match_stats_display.config(state="normal")
        self.match_stats_display.delete("1.0", tk.END)
        stats = self.db['match_stats']
        goals = ", ".join(stats.get("goals", [])) or "None"
        conceded = ", ".join(stats.get("conceded", [])) or "None"
        last_motm = stats.get("last_motm", "None")
        self.match_stats_display.insert(tk.END, f"Goal Scorers: {goals}\nGoal Conceded Players: {conceded}\nLast Match MOTM: {last_motm}")
        self.match_stats_display.config(state="disabled")

    def save_match_stats(self):
        if self.current_user['role'] != 's.a':
            messagebox.showerror("Error", "Only S.A can edit match stats!")
            return

        selected_goals = [self.goals_box.get(i) for i in self.goals_box.curselection()]
        selected_conceded = [self.conceded_box.get(i) for i in self.conceded_box.curselection()]
        selected_motm_idx = self.motm_box.curselection()

        self.db['match_stats']['goals'] = selected_goals
        self.db['match_stats']['conceded'] = selected_conceded

        if selected_motm_idx:
            motm_username = self.motm_box.get(selected_motm_idx[0])
            self.db['match_stats']['last_motm'] = motm_username
            user = next((u for u in self.db['users'] if u['username'] == motm_username), None)
            if user:
                user['motm_count'] = user.get('motm_count', 0) + 1

        self.calculate_star_players()
        self.save_data()
        messagebox.showinfo("Success", "Match statistics updated successfully!")
        self.refresh_dashboard()

    # ==================== ADMIN PANEL ====================
    def setup_admin_tab(self):
        # Master Refresh Frame (S.A Only)
        self.sa_master_frame = ttk.LabelFrame(self.tab_admin, text="S.A Master Controls", padding="10")
        ttk.Button(self.sa_master_frame, text="MASTER REFRESH (Clear Notice, Chat & AI Chat)", command=self.master_reset).pack(fill="x")

        # Player Controls List
        ttk.Label(self.tab_admin, text="Manage Players (Position, Role & Block Status)", font=('Segoe UI', 11, 'bold')).pack(anchor="w", pady=10)
        
        # Scrollable Frame for Admin User Management
        canvas = tk.Canvas(self.tab_admin, borderwidth=0, background="#f4f6f9")
        scrollbar = ttk.Scrollbar(self.tab_admin, orient="vertical", command=canvas.yview)
        self.scroll_admin_frame = ttk.Frame(canvas, padding="5")

        self.scroll_admin_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_admin_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def render_admin_panel(self):
        for widget in self.scroll_admin_frame.winfo_children():
            widget.destroy()

        for u in self.db['users']:
            f = ttk.LabelFrame(self.scroll_admin_frame, text=f"{u['username']} ({u['role'].upper()})", padding="10")
            f.pack(fill="x", expand=True, pady=5)

            # Position Edit (S.A Only)
            pos_frame = ttk.Frame(f)
            pos_frame.pack(fill="x", pady=2)
            ttk.Label(pos_frame, text="Position:").pack(side="left")
            pos_ent = ttk.Entry(pos_frame, width=15)
            pos_ent.insert(0, u.get("position", "Unassigned"))
            pos_ent.pack(side="left", padx=5)

            if self.current_user['role'] == 's.a':
                ttk.Button(pos_frame, text="Save Position", command=lambda uid=u['id'], ent=pos_ent: self.save_position(uid, ent.get())).pack(side="left")
            else:
                pos_ent.config(state="disabled")

            # Practice Only & Role Controls (S.A Only)
            if self.current_user['role'] == 's.a':
                ctl_frame = ttk.Frame(f)
                ctl_frame.pack(fill="x", pady=5)

                p_var = tk.BooleanVar(value=u.get("practice_only", False))
                p_chk = ttk.Checkbutton(ctl_frame, text="Practice Match Only Player", variable=p_var, command=lambda uid=u['id'], v=p_var: self.toggle_practice(uid, v.get()))
                p_chk.pack(side="left", padx=5)

                ttk.Label(ctl_frame, text="Role:").pack(side="left", padx=(10, 2))
                role_cb = ttk.Combobox(ctl_frame, values=["user", "a", "s.a"], width=7, state="readonly")
                role_cb.set(u['role'])
                role_cb.pack(side="left")
                role_cb.bind("<<ComboboxSelected>>", lambda e, uid=u['id'], cb=role_cb: self.change_role(uid, cb.get()))

            # Block / Unblock Button (S.A & Admin)
            block_btn_txt = "Unblock Player" if u.get("is_blocked") else "Block Player"
            ttk.Button(f, text=block_btn_txt, command=lambda uid=u['id']: self.toggle_block(uid)).pack(anchor="e", pady=5)

    def save_position(self, user_id, new_pos):
        user = next((u for u in self.db['users'] if u['id'] == user_id), None)
        if user:
            user['position'] = new_pos.strip() or "Unassigned"
            self.save_data()
            messagebox.showinfo("Success", "Position updated successfully!")
            self.refresh_dashboard()

    def toggle_practice(self, user_id, status):
        user = next((u for u in self.db['users'] if u['id'] == user_id), None)
        if user:
            user['practice_only'] = status
            self.save_data()

    def change_role(self, user_id, new_role):
        user = next((u for u in self.db['users'] if u['id'] == user_id), None)
        if user:
            user['role'] = new_role
            self.save_data()
            messagebox.showinfo("Success", f"User role updated to {new_role.upper()}!")
            self.refresh_dashboard()

    def toggle_block(self, user_id):
        user = next((u for u in self.db['users'] if u['id'] == user_id), None)
        if user:
            user['is_blocked'] = not user.get('is_blocked', False)
            self.save_data()
            status = "Blocked" if user['is_blocked'] else "Unblocked"
            messagebox.showinfo("Success", f"User {user['username']} is now {status}!")
            self.refresh_dashboard()

    # Master Reset (Delete notices, chat, ai_chat WITHOUT deleting User IDs)
    def master_reset(self):
        if self.current_user['role'] != 's.a':
            return
        if messagebox.askyesno("Master Refresh", "Are you sure? This will delete ALL Notices, Group Chats, and AI Chats without deleting User IDs!"):
            self.db['notices'] = []
            self.db['chats'] = []
            self.db['ai_chats'] = []
            self.save_data()
            messagebox.showinfo("Complete", "Master Reset finished! All notices and chats are cleared.")
            self.refresh_dashboard()

if __name__ == "__main__":
    root = tk.Tk()
    app = ClubApp(root)
    root.mainloop()
