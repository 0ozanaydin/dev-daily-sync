from flask import Flask, request, jsonify, session
from flask_cors import CORS
import datetime
import time
from flask import Flask, request, jsonify, session, send_from_directory  # <-- send_from_directory'yi buraya ekle
from flask_cors import CORS

app = Flask(__name__)
CORS(app, supports_credentials=True) # Frontend'in bağlanabilmesi için
app.config['SECRET_KEY'] = 'cok-gizli-bir-anahtar-guvenlik-onemli-degil-dediniz'
# --- YENİ EKLENECEK KOD BURAYA ---
@app.route('/')
def serve_index():
    # '.' mevcut klasör, 'index.html' ise dosya adıdır
    return send_from_directory('.', 'index.html')
# -----------------------------------


# --- GEÇİCİ VERİTABANI (PROGRAM ÇALIŞTIKÇA HAFIZADA TUTULUR) ---
# Gerçek bir projede burası SQL veritabanı olmalıdır.
USERS = {
    "ozan": {"password": "123", "name": "Ozan Yılmaz"},
    "taha": {"password": "456", "name": "Taha Demir"}
}
DAILIES = [
    {
        "id": 1, 
        "user_name": "Ozan Yılmaz", 
        "title": "İlk Gün Raporu",
        "description": "Bugün <b>bold</b> ve <i>italik</i> yazı denemeleri yaptım. Backend bağlantısını kurdum.",
        "date": "2025-10-26",
        "hours_worked": 4,
        "screenshots": ["https://via.placeholder.com/800x600.png?text=SS+1"],
        "is_negative": False,
        "negative_reason": None
    }
]
TODOS = [
    {
        "id": 1,
        "task": "Login sayfasını tasarla",
        "assigned_to": "Taha Demir",
        "deadline": "2025-10-30",
        "is_completed": False,
        "images": []
    }
]
# -----------------------------------------------------------------

# KULLANICI İŞLEMLERİ (AUTH)
@app.route('/register', methods=['POST'])
def register():
    # Bu basit örnekte yeni kayıt almıyoruz, sadece varolanları kullanıyoruz.
    return jsonify({"error": "Register not implemented"}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username in USERS and USERS[username]['password'] == password:
        # Session (Oturum) başlat
        session['username'] = username
        session['full_name'] = USERS[username]['name']
        return jsonify({
            "message": "Login successful", 
            "user": {
                "username": username,
                "full_name": USERS[username]['name']
            }
        })
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({"message": "Logged out"})

@app.route('/check_session', methods=['GET'])
def check_session():
    if 'username' in session:
        return jsonify({
            "is_logged_in": True,
            "user": {
                "username": session['username'],
                "full_name": session['full_name']
            }
        })
    else:
        return jsonify({"is_logged_in": False})

# --- API İŞLEMLERİ ---

# DAILY API
@app.route('/api/dailies', methods=['GET'])
def get_dailies():
    # if 'username' not in session:
    #     return jsonify({"error": "Not authorized"}), 401
    
    # Gün ve haftaya göre gruplama
    # Bu kısım normalde SQL sorgusu ile yapılır, burada Python ile yapıyoruz.
    grouped_dailies = {}
    
    # Önce tarihe göre sırala (en yeni en üstte)
    sorted_dailies = sorted(DAILIES, key=lambda x: x['date'], reverse=True)
    
    for daily in sorted_dailies:
        date_obj = datetime.datetime.strptime(daily['date'], "%Y-%m-%d").date()
        
        # Haftalık gruplama
        # week_key = f"Hafta {date_obj.isocalendar()[1]} ({date_obj.year})"
        
        # Günlük gruplama
        day_key = date_obj.strftime("%d %B %Y, %A") # Örn: 27 Ekim 2025, Pazartesi
        
        if day_key not in grouped_dailies:
            grouped_dailies[day_key] = []
        
        grouped_dailies[day_key].append(daily)
        
    return jsonify(grouped_dailies)


@app.route('/api/dailies', methods=['POST'])
def add_daily():
    if 'username' not in session:
        return jsonify({"error": "Not authorized"}), 401
    
    data = request.json
    today_str = datetime.date.today().isoformat()
    
    new_daily = {
        "id": int(time.time()), # Basit bir ID
        "user_name": session['full_name'],
        "title": data.get('title'),
        "description": data.get('description'),
        "date": today_str,
        "hours_worked": data.get('hours_worked'),
        "screenshots": data.get('screenshots', []), # Dosya yükleme apayrı bir konu, şimdilik URL listesi
        "is_negative": data.get('is_negative', False),
        "negative_reason": data.get('negative_reason', None)
    }
    
    DAILIES.append(new_daily)
    return jsonify(new_daily), 201

# TODO API
@app.route('/api/todos', methods=['GET'])
def get_todos():
    # if 'username' not in session:
    #     return jsonify({"error": "Not authorized"}), 401
        
    # Deadline'a göre sırala
    today = datetime.date.today()
    
    def sort_key(todo):
        deadline = datetime.datetime.strptime(todo['deadline'], "%Y-%m-%d").date()
        days_left = (deadline - today).days
        
        if todo['is_completed']:
            return 1000000 # Tamamlananlar en sonda
        
        if days_left < 0:
            return -1000000 # Gecikenler en üstte
            
        return days_left # Yaklaşanlar üstte

    sorted_todos = sorted(TODOS, key=sort_key)
    
    # 'days_left' bilgisini ekle
    result_todos = []
    for todo in sorted_todos:
        deadline = datetime.datetime.strptime(todo['deadline'], "%Y-%m-%d").date()
        days_diff = (deadline - today).days
        
        if todo['is_completed']:
            todo['days_left_text'] = "Tamamlandı"
        elif days_diff < 0:
            todo['days_left_text'] = f"<b>{abs(days_diff)} gün geçti</b>"
        elif days_diff == 0:
            todo['days_left_text'] = "<b>Son Gün!</b>"
        else:
            todo['days_left_text'] = f"{days_diff} gün kaldı"
            
        result_todos.append(todo)

    return jsonify(result_todos)

@app.route('/api/todos', methods=['POST'])
def add_todo():
    if 'username' not in session:
        return jsonify({"error": "Not authorized"}), 401
        
    data = request.json
    new_todo = {
        "id": int(time.time()),
        "task": data.get('task'),
        "assigned_to": data.get('assigned_to'),
        "deadline": data_get('deadline'),
        "is_completed": False,
        "images": data.get('images', [])
    }
    TODOS.append(new_todo)
    return jsonify(new_todo), 201
    
@app.route('/api/todos/<int:todo_id>/complete', methods=['POST'])
def complete_todo(todo_id):
    if 'username' not in session:
        return jsonify({"error": "Not authorized"}), 401
        
    for todo in TODOS:
        if todo['id'] == todo_id:
            todo['is_completed'] = not todo['is_completed'] # Toggle
            return jsonify(todo)
            
    return jsonify({"error": "Todo not found"}), 404

# DASHBOARD API
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    if 'username' not in session:
        return jsonify({"error": "Not authorized"}), 401
    
    today_str = datetime.date.today().isoformat()
    
    # 1. Bugünkü Daily'ler
    todays_dailies = [d for d in DAILIES if d['date'] == today_str]
    
    # 2. Yaklaşan Todo'lar (1 Hafta)
    today = datetime.date.today()
    one_week_later = today + datetime.timedelta(days=7)
    
    upcoming_todos = []
    for todo in TODOS:
        if todo['is_completed']:
            continue
            
        deadline = datetime.datetime.strptime(todo['deadline'], "%Y-%m-%d").date()
        if today <= deadline <= one_week_later:
            days_diff = (deadline - today).days
            if days_diff == 0:
                todo['days_left_text'] = "<b>Son Gün!</b>"
            else:
                todo['days_left_text'] = f"{days_diff} gün kaldı"
            upcoming_todos.append(todo)
            
    return jsonify({
        "todays_dailies": todays_dailies,
        "upcoming_todos": sorted(upcoming_todos, key=lambda x: x['deadline'])
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000) # Backend http://localhost:5000 adresinde çalışacak