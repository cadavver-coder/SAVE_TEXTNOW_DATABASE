from flask import Flask, request, render_template, jsonify
from flask import send_from_directory, abort
from werkzeug.utils import safe_join


import sqlite3
import json
from datetime import datetime
import os

app = Flask(__name__)
# DB_FILE = "users.db"
FILES = 'db'

def get_conn(DB_FILE):
    try:
        conn = sqlite3.connect(f'{FILES}/{DB_FILE}')
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
        return conn
    except Exception as e:
        return False
        
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/insert", methods=["POST"])
def insert():
    try:
        data = request.json
        database_file = data.get("database", "").strip()
        username = data.get("username", "").strip()
        user_agent = data.get("user_agent", "").strip()
        proxy = data.get("proxy", "").strip()
        email = data.get("email_username", "").strip()
        password = data.get("password", "")
        cookies_raw = data.get("cookies_json", "")

        if not username:
            return jsonify({"error": "Username este obligatoriu."}), 400

        try:
            cookies_obj = json.loads(cookies_raw)
            textnow_cookies = {
                c["name"]: c["value"]
                for c in cookies_obj
                if "textnow.com" in c["domain"]
            }
            cookies_json = json.dumps(textnow_cookies, ensure_ascii=False)
        except Exception as e:
            return jsonify({"error": f"Cookies JSON invalid: {e}"}), 400

        created_at = datetime.utcnow().isoformat() + "Z"

        conn = get_conn(database_file)
        print(conn)
        conn.execute("""
            INSERT INTO users (username, user_agent, proxy, cookies_json, email_username, password, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, user_agent, proxy, cookies_json, email, password, created_at))
        conn.commit()
        conn.close()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/last", methods=["GET"])
def last():
    # primește numele bazei de date din query string
    database_file = request.args.get("db", "default.db")  # "default.db" ca fallback

    conn = get_conn(database_file)
    
    cur = conn.execute("""
    SELECT id, username, user_agent, proxy, cookies_json, email_username, password, created_at
    FROM users ORDER BY id DESC LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"data": None})
    
    return jsonify({
        "data": {
            "id": row[0],
            "username": row[1],
            "user_agent": row[2],
            "proxy": row[3],
            "cookies_json": row[4],
            "email_username": row[5],
            "password": row[6],
            "created_at": row[7]
        }
    })


@app.route("/all", methods=["GET"])
def all_records():
    # primește numele bazei de date din query string
    database_file = request.args.get("db", "default.db")

    conn = get_conn(database_file)
    cur = conn.execute("""
    SELECT id, username, user_agent, proxy, cookies_json, email_username, password, created_at
    FROM users ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()

    data = []
    if len(rows) > 0:
        for row in rows:
            data.append({
                "id": row[0],
                "username": row[1],
                "user_agent": row[2],
                "proxy": row[3],
                "cookies_json": row[4],
                "email_username": row[5],
                "password": row[6],
                "created_at": row[7]
            })

        return jsonify({"data": data})
    else:
        return jsonify({"error": f"Database empty"}), 400
        

@app.route("/conn", methods=["POST"])
def conx():
    try:
        data = request.json
        database_sql = data.get("database_sql", "").strip()
        if not database_sql:
            return jsonify({"error": "example.db este obligatoriu."}), 400
        else:
            resp = get_conn(database_sql)
            if resp:
                return jsonify({"success": True})
            else:
                return jsonify({"error": f"Database not created"}), 400
    except Exception as e:
        print(e)



@app.route("/download/<path:db_name>")
def download_db(db_name):
    # Construim calea completă
    db_path = safe_join("db", db_name)  # db_name poate fi "121/mydb.db"

    # Verificăm dacă fișierul există
    if not os.path.isfile(db_path):
        abort(404, description="Database not found")

    # Trimitem fișierul pentru download
    directory = os.path.dirname(db_path)
    filename = os.path.basename(db_path)
    return send_from_directory(directory, filename, as_attachment=True)


def list_databases(folder=FILES):
    """Returnează lista fișierelor .db din folder"""
    try:
        files = os.listdir(folder)
        
        db_files = [f.rstrip() for f in files if f != 'null']

        return db_files
    except FileNotFoundError:
        return []
    
    
@app.route("/databases", methods=["GET"])
def databases():
    db_files = list_databases()
    return jsonify({"count": len(db_files), "databases": db_files})
    
    
    
    
    
@app.route("/delete_database", methods=["POST"])
def delete_database():
    data = request.get_json()
    filename = data.get("filename")

    if not filename:
        return jsonify({"error": "Missing filename"}), 400

    file_path = os.path.join(FILES, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        os.remove(file_path)
        return jsonify({"success": True, "message": f"{filename} deleted successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
    
if __name__ == "__main__":
    app.run(debug=True)
