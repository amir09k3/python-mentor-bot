# src/models/database.py
import sqlite3
from pathlib import Path
from datetime import datetime

# مسیر پایگاه داده (در پوشه اصلی پروژه)
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "mentor.db"

# ایجاد پوشه data اگر وجود نداره
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    """ایجاد جدول users اگر وجود نداشت"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            join_date TEXT NOT NULL,
            level TEXT DEFAULT 'beginner',
            experience INTEGER DEFAULT 0
        )
    """)
    
    # جدول تمرین‌ها
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            test_cases TEXT NOT NULL  -- JSON: [{"input": [...], "expected": ...}]
        )
    """)

    # جدول سابقه ارسال‌ها
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            is_correct BOOLEAN NOT NULL,
            score INTEGER NOT NULL,
            submitted_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(exercise_id) REFERENCES exercises(id)
        )
    """)

# اضافه کردن 10 تمرین
    cursor.execute("SELECT COUNT(*) FROM exercises")
    if cursor.fetchone()[0] == 0:
        import json

        exercises_data = [
            # --- ساده ---
            (1, "جمع دو عدد", "تابعی به نام add(a, b) بنویسید که دو عدد را جمع کند.", "beginner", [
                {"input": [2, 3], "expected": 5},
                {"input": [0, 0], "expected": 0},
                {"input": [-1, 1], "expected": 0}
            ]),
            (2, "بیشینه سه عدد", "تابع max3(a, b, c) که بزرگ‌ترین سه عدد را برمی‌گرداند.", "beginner", [
                {"input": [1, 2, 3], "expected": 3},
                {"input": [5, -1, 0], "expected": 5},
                {"input": [-2, -5, -1], "expected": -1}
            ]),
            (3, "فاکتوریل (تکراری)", "تابع fact(n) با حلقه for (n >= 0).", "beginner", [
                {"input": [0], "expected": 1},
                {"input": [1], "expected": 1},
                {"input": [5], "expected": 120}
            ]),
            (4, "معکوس رشته", "تابع reverse(s) بدون استفاده از s[::-1].", "beginner", [
                {"input": ["abc"], "expected": "cba"},
                {"input": ["123"], "expected": "321"},
                {"input": [""], "expected": ""}
            ]),
            # --- متوسط ---
            (5, "فیبوناچی (بازگشتی)", "تابع fib(n) بازگشتی (n >= 0).", "intermediate", [
                {"input": [0], "expected": 0},
                {"input": [1], "expected": 1},
                {"input": [5], "expected": 5}
            ]),
            (6, "میانگین لیست", "تابع average(lst) که میانگین اعداد لیست را برمی‌گرداند.", "intermediate", [
                {"input": [[1, 2, 3]], "expected": 2.0},
                {"input": [[10]], "expected": 10.0},
                {"input": [[-1, 1]], "expected": 0.0}
            ]),
            (7, "حذف تکراری‌ها", "تابع unique(lst) که عناصر تکراری را حذف می‌کند (ترتیب حفظ شود).", "intermediate", [
                {"input": [[1, 2, 2, 3]], "expected": [1, 2, 3]},
                {"input": [[1, 1, 1]], "expected": [1]},
                {"input": [[1, 2, 3, 2, 1]], "expected": [1, 2, 3]}
            ]),
            # --- سخت ---
            (8, "مرتب‌سازی حبابی", "تابع bubble_sort(lst) که لیست را مرتب می‌کند.", "advanced", [
                {"input": [[3, 1, 2]], "expected": [1, 2, 3]},
                {"input": [[5, 4, 3, 2, 1]], "expected": [1, 2, 3, 4, 5]},
                {"input": [[]], "expected": []}
            ]),
            (9, "جستجوی دودویی", "تابع binary_search(lst, x) که اندیس x را برمی‌گرداند (یا -1).", "advanced", [
                {"input": [[1, 2, 3, 4, 5], 3], "expected": 2},
                {"input": [[1, 2, 3], 4], "expected": -1},
                {"input": [[10], 10], "expected": 0}
            ]),
            (10, "برج هانوی", "تابع hanoi(n) که حداقل تعداد حرکت را برمی‌گرداند (2^n - 1).", "advanced", [
                {"input": [1], "expected": 1},
                {"input": [2], "expected": 3},
                {"input": [3], "expected": 7}
            ])
        ]

        for ex_id, title, desc, diff, cases in exercises_data:
            cursor.execute("""
                INSERT INTO exercises (id, title, description, difficulty, test_cases)
                VALUES (?, ?, ?, ?, ?)
            """, (ex_id, title, desc, diff, json.dumps(cases)))
        
        print("✅ 10 تمرین به دیتابیس اضافه شد.")
    
    conn.commit()
    conn.close()
    print(f"✅ پایگاه داده آماده شد: {DB_PATH}")

def add_user(user_id: int, first_name: str = "", username: str = ""):
    """افزودن یا به‌روزرسانی کاربر"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # اگر کاربر وجود داشت، فقط اطلاعات عمومی به‌روز شود
    cursor.execute("""
        INSERT INTO users (user_id, first_name, username, join_date)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            first_name = excluded.first_name,
            username = excluded.username
    """, (user_id, first_name, username, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def get_user(user_id: int):
    """دریافت اطلاعات کاربر با user_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "user_id": row[0],
            "first_name": row[1],
            "username": row[2],
            "join_date": row[3],
            "level": row[4],
            "experience": row[5]
        }
    return None

def update_user_level(user_id: int, level: str, exp: int = 0):
    """به‌روزرسانی سطح و امتیاز کاربر"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users 
        SET level = ?, experience = experience + ?
        WHERE user_id = ?
    """, (level, exp, user_id))
    
    conn.commit()
    conn.close()
    
def add_submission(user_id: int, exercise_id: int, code: str, is_correct: bool, score: int):
    """ذخیره سابقه ارسال تمرین"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO submissions (user_id, exercise_id, code, is_correct, score, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, exercise_id, code, is_correct, score, now))
    conn.commit()
    conn.close()

def get_user_profile(user_id: int):
    """دریافت پروفایل کامل کاربر"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # اطلاعات پایه
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        return None
    
    # آمار تمرین‌ها
    cursor.execute("""
        SELECT 
            COUNT(*) as total_submissions,
            SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_submissions,
            SUM(score) as total_score
        FROM submissions WHERE user_id = ?
    """, (user_id,))
    stats = cursor.fetchone()
    
    conn.close()
    
    return {
        "user_id": user[0],
        "first_name": user[1],
        "username": user[2],
        "join_date": user[3][:10],  # فقط تاریخ
        "level": user[4],
        "experience": user[5],
        "total_submissions": stats[0] or 0,
        "correct_submissions": stats[1] or 0,
        "total_score": stats[2] or 0
    }

def get_leaderboard(limit: int = 5):
    """دریافت جدول رده‌بندی"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.user_id, u.first_name, u.username, u.experience
        FROM users u
        ORDER BY u.experience DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows