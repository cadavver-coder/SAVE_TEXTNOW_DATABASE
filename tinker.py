import sqlite3
import json
from datetime import datetime
import os
import customtkinter as ctk
from tkinter import messagebox
import requests

DB_FOLDER = "db"
os.makedirs(DB_FOLDER, exist_ok=True)

# 🔧 CONFIG TELEGRAM
TELEGRAM_TOKEN = "8332118305:AAG8BhFYK2-HIHB2KNoSnxZDJkQ5KuWbB-I"
CHAT_ID = "-4773949780"


def get_conn(db_name):
    """Creează conexiunea și tabela dacă nu există"""
    path = os.path.join(DB_FOLDER, db_name)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            user_agent TEXT,
            proxy TEXT,
            cookies_json TEXT,
            email_username TEXT,
            password TEXT,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    return conn, path


def list_databases():
    """Returnează lista bazelor de date .db"""
    return [f for f in os.listdir(DB_FOLDER) if f.endswith(".db")]


def send_to_telegram(file_path):
    """Trimite fișierul DB pe Telegram, cu mesaj opțional și loader"""
    if not os.path.exists(file_path):
        messagebox.showerror("Eroare", "Fișierul nu există!")
        return False

    if TELEGRAM_TOKEN.startswith("AICI") or CHAT_ID.startswith("AICI"):
        messagebox.showwarning("Configurare necesară", "Setează tokenul și chat_id în cod!")
        return False

    # 🪄 Popup pentru mesaj personal
    popup = ctk.CTkToplevel()
    popup.title("Mesaj Telegram")
    popup.geometry("400x200")
    popup.grab_set()  # face fereastra modală

    ctk.CTkLabel(popup, text="Adaugă un mesaj la trimiterea în Telegram:", font=("Arial", 14)).pack(pady=10)
    msg_entry = ctk.CTkEntry(popup, width=350, placeholder_text="Ex: Backup automat 10 octombrie")
    msg_entry.pack(pady=10)

    def send_now():
        """Trimite efectiv fișierul și mesajul"""
        notice = msg_entry.get().strip()
        popup.destroy()

        # 🌙 Fereastră loader
        loader = ctk.CTkToplevel()
        loader.title("Se trimite...")
        loader.geometry("300x150")
        loader.grab_set()
        ctk.CTkLabel(loader, text="Se trimite fișierul către Telegram... ⏳", font=("Arial", 13)).pack(pady=20)

        progress = ctk.CTkProgressBar(loader, mode="indeterminate", width=220)
        progress.pack(pady=10)
        progress.start()

        loader.update()

        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
            with open(file_path, "rb") as f:
                data = {"chat_id": CHAT_ID}
                files = {"document": f}
                if notice:
                    data["caption"] = notice
                response = requests.post(url, data=data, files=files)

            loader.destroy()

            if response.status_code == 200:
                messagebox.showinfo("Succes", f"{os.path.basename(file_path)} trimis pe Telegram ✅")
            else:
                messagebox.showerror("Eroare", f"Eroare Telegram ({response.status_code}): {response.text}")

        except Exception as e:
            loader.destroy()
            messagebox.showerror("Eroare", str(e))

    ctk.CTkButton(popup, text="Trimite acum 🚀", command=send_now).pack(pady=10)
    ctk.CTkButton(popup, text="Anulează", fg_color="gray", hover_color="#555", command=popup.destroy).pack()



def delete_database(file_name, parent_frame=None):
    path = os.path.join(DB_FOLDER, file_name)
    if os.path.exists(path):
        os.remove(path)
        messagebox.showinfo("Succes", f"{file_name} a fost șters.")
        if parent_frame:
            parent_frame.destroy()  # ștergem rândul din UI
    else:
        messagebox.showerror("Eroare", "Fișierul nu există.")


# ---------- APP GUI ------------
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TextNow User Manager v.0.0.1")
        self.geometry("800x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Titlu
        ctk.CTkLabel(
            self, 
            text="TextNow Database", 
            font=("Arial", 24, "bold"), 
            text_color="#8654f3"  # poți pune orice culoare: "red", "blue", "#ff0000" etc.
        ).pack(pady=30)

        # ---------- Selectare DB ----------
        db_frame = ctk.CTkFrame(self, corner_radius=10)
        db_frame.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(db_frame, text="Database name:", width=130).pack(side="left", padx=10)
        self.db_name = ctk.CTkEntry(db_frame, width=250, placeholder_text="ex: clienti.db")
        self.db_name.pack(side="left", padx=5)
        self.connect_button = ctk.CTkButton(db_frame, text="Creează / Conectează", command=self.connect_db)
        self.connect_button.pack(side="left", padx=10)
        ctk.CTkButton(db_frame, text="📁 Listează baze de date", command=self.show_db_list).pack(side="left", padx=10)
        self.db_status = ctk.CTkLabel(db_frame, text="Nicio bază conectată", text_color="orange")
        self.db_status.pack(side="left", padx=10)

        # ---------- Formular ----------
        form = ctk.CTkFrame(self, corner_radius=12)
        form.pack(padx=20, pady=10, fill="both", expand=False)

        self.username = self._add_entry(form, "Username")
        self.user_agent = self._add_entry(form, "User Agent")
        self.proxy = self._add_entry(form, "Proxy")
        self.email_username = self._add_entry(form, "Email / Username")
        self.password = self._add_entry(form, "Password", show="*")
        self.cookies_json = self._add_entry(form, "Cookies JSON")

        # ---------- Butoane ----------
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=15)
        ctk.CTkButton(btn_frame, text="Adaugă utilizator", command=self.insert_user).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Ultimul utilizator", command=self.show_last).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Toți utilizatorii", command=self.show_all).pack(side="left", padx=10)

        # ---------- Output ----------
        self.output = ctk.CTkTextbox(self, height=220)
        self.output.pack(padx=20, pady=10, fill="both", expand=True)

        self.current_db = None

    # -------------------------------
    def _add_entry(self, parent, label_text, show=None):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(frame, text=label_text, width=120).pack(side="left", padx=5)
        entry = ctk.CTkEntry(frame, show=show, width=400)
        entry.pack(side="left", padx=5)
        return entry

    # -------------------------------
    def connect_db(self):
        name = self.db_name.get().strip()
        if not name:
            messagebox.showwarning("Eroare", "Introdu un nume pentru baza de date.")
            return
        if not name.endswith(".db"):
            name += ".db"
        conn, path = get_conn(name)
        conn.close()
        self.current_db = name

        # ✅ Schimbare status label
        self.db_status.configure(text=f"Connected!", text_color="lightgreen")

        # ✅ Schimbare button color și text
        self.connect_button.configure(text="Connected!", fg_color="green", hover_color="#4CAF50")

        messagebox.showinfo("Succes", f"Baza de date '{name}' este pregătită!")

    # -------------------------------
    def insert_user(self):
        if not self.current_db:
            messagebox.showwarning("Eroare", "Selectează mai întâi o bază de date.")
            return
        try:
            username = self.username.get().strip()
            if not username:
                messagebox.showwarning("Eroare", "Username este obligatoriu.")
                return

            cookies_raw = self.cookies_json.get().strip()
            try:
                cookies_obj = json.loads(cookies_raw) if cookies_raw else {}
            except Exception as e:
                messagebox.showerror("Eroare", f"Cookies JSON invalid: {e}")
                return

            conn, _ = get_conn(self.current_db)
            conn.execute("""
                INSERT INTO users (username, user_agent, proxy, cookies_json, email_username, password, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                username,
                self.user_agent.get().strip(),
                self.proxy.get().strip(),
                json.dumps(cookies_obj, ensure_ascii=False),
                self.email_username.get().strip(),
                self.password.get().strip(),
                datetime.utcnow().isoformat() + "Z"
            ))
            conn.commit()
            conn.close()
            messagebox.showinfo("Succes", "Utilizator adăugat cu succes!")
        except Exception as e:
            messagebox.showerror("Eroare", str(e))

    # -------------------------------
    def show_last(self):
        if not self.current_db:
            messagebox.showwarning("Eroare", "Selectează mai întâi o bază de date.")
            return
        conn, _ = get_conn(self.current_db)
        cur = conn.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()

        self.output.delete("1.0", "end")
        if row:
            keys = ["ID", "Username", "User Agent", "Proxy", "Cookies", "Email", "Password", "Creat"]
            for i, key in enumerate(keys):
                self.output.insert("end", f"{key}: {row[i]}\n")
        else:
            self.output.insert("end", "Niciun utilizator găsit.")

    # -------------------------------
    def show_all(self):
        if not self.current_db:
            messagebox.showwarning("Eroare", "Selectează mai întâi o bază de date.")
            return
        conn, _ = get_conn(self.current_db)
        cur = conn.execute("SELECT id, username, email_username, created_at FROM users ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()

        self.output.delete("1.0", "end")
        if rows:
            for row in rows:
                self.output.insert("end", f"#{row[0]} | {row[1]} ({row[2]}) - {row[3]}\n")
        else:
            self.output.insert("end", "Baza de date este goală.")

    # -------------------------------
    def show_db_list(self):
        dbs = list_databases()
        if not dbs:
            messagebox.showinfo("Info", "Nu există baze de date în folderul 'db'.")
            return

        win = ctk.CTkToplevel(self)
        win.title("Lista bazelor de date")
        win.geometry("700x400")

        ctk.CTkLabel(win, text="Baze de date găsite:", font=("Arial", 18, "bold")).pack(pady=10)

        for db_file in dbs:
            frame = ctk.CTkFrame(win, corner_radius=10)
            frame.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(frame, text=db_file, width=200).pack(side="left", padx=10)
            ctk.CTkButton(frame, text="🗑️ Șterge", fg_color="red", hover_color="#a00",
                        command=lambda f=db_file, fr=frame: delete_database(f, fr)).pack(side="right", padx=5)
            ctk.CTkButton(frame, text="📤 Trimite Telegram",
                        command=lambda f=db_file: send_to_telegram(os.path.join(DB_FOLDER, f))).pack(side="right", padx=5)


if __name__ == "__main__":
    app = App()
    app.mainloop()
