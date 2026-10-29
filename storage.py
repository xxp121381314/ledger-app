# -*- coding: utf-8 -*-
import sqlite3

DB_FILE = "ledger.db"

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            date TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT '支出'
        )
    """)
    conn.commit()
    conn.close()

def add_bill(amount, category, note, date, bill_type="支出"):
    """添加账单"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bills (amount, category, note, date, type) VALUES (?, ?, ?, ?, ?)",
        (amount, category, note, date, bill_type)
    )
    conn.commit()
    conn.close()

def get_bills_by_filter(month_str=None, keyword=None):
    """支持月份和关键词组合筛选账单"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    sql = "SELECT * FROM bills WHERE 1=1"
    params = []
    
    if month_str:
        sql += " AND date LIKE ?"
        params.append(month_str + "%")
    if keyword:
        sql += " AND (note LIKE ? OR category LIKE ?)"
        params.append(f"%{keyword}%")
        params.append(f"%{keyword}%")
        
    sql += " ORDER BY date DESC, id DESC"
    
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    
    return [{"id": row["id"], "amount": row["amount"], "category": row["category"], 
             "note": row["note"], "date": row["date"], "type": row["type"]} for row in rows]

def get_monthly_stats(month_str):
    """获取某个月份的总收入、总支出、结余"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(amount) FROM bills WHERE date LIKE ? AND type = '支出'", (month_str + "%",))
    expense = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT SUM(amount) FROM bills WHERE date LIKE ? AND type = '收入'", (month_str + "%",))
    income = cursor.fetchone()[0] or 0.0
    
    conn.close()
    return income, expense, (income - expense)

def get_category_stats(month_str):
    """获取某个月份各分类的支出总和"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT category, SUM(amount) FROM bills 
        WHERE date LIKE ? AND type = '支出'
        GROUP BY category
    """, (month_str + "%",))
    rows = cursor.fetchall()
    conn.close()
    return [{"分类": row[0], "金额": row[1]} for row in rows]

def delete_bill(bill_id):
    """删除账单"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
    conn.commit()
    conn.close()

def import_bills(bills_data):
    """批量导入账单数据，完美兼容钱迹导出格式和本软件导出格式"""
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
            if note == 'nan':
                note = ''
            bill_type = str(row.get('类型', '支出'))
            if bill_type not in ['支出', '收入']:
                bill_type = '支出'
                
            cursor.execute(
                "INSERT INTO bills (amount, category, note, date, type) VALUES (?, ?, ?, ?, ?)",
                (amount, category, note, date_str, bill_type)
            )
            success_count += 1
        except Exception:
            pass 
            
    conn.commit()
    conn.close()
    return success_count
