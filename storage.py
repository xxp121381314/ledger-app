# -*- coding: utf-8 -*-
# 记账 APP 的数据库模块（升级版）

import sqlite3

DB_FILE = "ledger_v2.db"

def init_db():
    """初始化数据库，建表"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 注意：新增了 type 字段，默认值是 '支出'
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
    """添加一笔账单"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bills (amount, category, note, date, type) VALUES (?, ?, ?, ?, ?)",
        (amount, category, note, date, bill_type)
    )
    conn.commit()
    conn.close()

def get_all_bills():
    """获取所有账单，返回列表"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bills ORDER BY date DESC, id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        result.append({
            "id": row["id"], "amount": row["amount"],
            "category": row["category"], "note": row["note"],
            "date": row["date"], "type": row["type"] # 新增 type
        })
    return result

def get_monthly_stats(month_str):
    """获取某个月份的总收入、总支出和结余"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 算总支出
    cursor.execute("SELECT SUM(amount) FROM bills WHERE date LIKE ? AND type = '支出'", (month_str + "%",))
    expense = cursor.fetchone()[0] or 0.0
    
    # 算总收入
    cursor.execute("SELECT SUM(amount) FROM bills WHERE date LIKE ? AND type = '收入'", (month_str + "%",))
    income = cursor.fetchone()[0] or 0.0
    
    conn.close()
    return income, expense, (income - expense)

def get_category_stats(month_str):
    """获取某个月份各分类的支出总和（只看支出）"""
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
    """根据编号删除账单"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
    conn.commit()
    conn.close()
