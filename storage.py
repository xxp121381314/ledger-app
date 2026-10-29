# -*- coding: utf-8 -*-
import sqlite3

DB_FILE = "ledger_v3.db"  # 版本升级，换了个新名字，防止旧数据冲突

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 账单表：新增 account 字段
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            date TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT '支出',
            account TEXT DEFAULT '微信'
        )
    """)
    # 设置表：用于存预算等配置
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_bill(amount, category, note, date, bill_type, account="微信"):
    """添加账单"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bills (amount, category, note, date, type, account) VALUES (?, ?, ?, ?, ?, ?)",
        (amount, category, note, date, bill_type, account)
    )
    conn.commit()
    conn.close()

def update_bill(bill_id, amount, category, note, date, bill_type, account):
    """更新账单"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE bills 
        SET amount=?, category=?, note=?, date=?, type=?, account=? 
        WHERE id=?
    """, (amount, category, note, date, bill_type, account, bill_id))
    conn.commit()
    conn.close()

def get_bills_by_filter(month_str=None, keyword=None):
    """筛选账单"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    sql = "SELECT * FROM bills WHERE 1=1"
    params = []
    
    if month_str:
        sql += " AND date LIKE ?"
        params.append(month_str + "%")
    if keyword:
        sql += " AND (note LIKE ? OR category LIKE ? OR account LIKE ?)"
        params.append(f"%{keyword}%")
        params.append(f"%{keyword}%")
        params.append(f"%{keyword}%")
        
    sql += " ORDER BY date DESC, id DESC"
    
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    
    return [{"id": row["id"], "amount": row["amount"], "category": row["category"], 
             "note": row["note"], "date": row["date"], "type": row["type"], 
             "account": row["account"]} for row in rows]

def get_monthly_stats(month_str):
    """获取月度收支"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM bills WHERE date LIKE ? AND type = '支出'", (month_str + "%",))
    expense = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT SUM(amount) FROM bills WHERE date LIKE ? AND type = '收入'", (month_str + "%",))
    income = cursor.fetchone()[0] or 0.0
    conn.close()
    return income, expense, (income - expense)

def get_category_stats(month_str):
    """分类支出统计"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT category, SUM(amount) FROM bills WHERE date LIKE ? AND type = '支出' GROUP BY category", (month_str + "%",))
    rows = cursor.fetchall()
    conn.close()
    return [{"分类": row[0], "金额": row[1]} for row in rows]

def get_daily_trends(month_str):
    """获取每日支出趋势（用于折线图）"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, SUM(amount) FROM bills 
        WHERE date LIKE ? AND type = '支出' 
        GROUP BY date ORDER BY date ASC
    """, (month_str + "%",))
    rows = cursor.fetchall()
    conn.close()
    return {row[0][-5:]: row[1] for row in rows} # 只取 "10-29" 这种格式作为X轴

def delete_bill(bill_id):
    """删除账单"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
    conn.commit()
    conn.close()

def import_bills(bills_data):
    """兼容钱迹导入"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    success_count = 0
    for row in bills_data:
        try:
            amount = float(row.get('金额(元)', row.get('金额')))
            raw_date = str(row.get('日期', row.get('时间', '')))
            date_str = raw_date.split(' ')[0] if raw_date else "2026-10-01"
            category = str(row.get('分类', '其它'))
            note = str(row.get('备注', ''))
            if note == 'nan': note = ''
            bill_type = str(row.get('类型', '支出'))
            if bill_type not in ['支出', '收入']: bill_type = '支出'
            # 兼容钱迹的账户列，如果没有则默认微信
            account = str(row.get('账户1', '微信'))
            if account == 'nan' or not account: account = '微信'
                
            cursor.execute(
                "INSERT INTO bills (amount, category, note, date, type, account) VALUES (?, ?, ?, ?, ?, ?)",
                (amount, category, note, date_str, bill_type, account)
            )
            success_count += 1
        except Exception:
            pass 
    conn.commit()
    conn.close()
    return success_count

# ===== 设置相关（预算） =====
def set_setting(key, value):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_setting(key, default=""):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default
