# -*- coding: utf-8 -*-
# 记账 APP 的数据库模块

import sqlite3

DB_FILE = "ledger.db"  # 账本数据库文件

def init_db():
    """初始化数据库，建表"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 建一张 bills（账单）表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def add_bill(amount, category, note, date):
    """添加一笔账单到数据库"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 插入数据，用问号占位符防止 SQL 注入
    cursor.execute(
        "INSERT INTO bills (amount, category, note, date) VALUES (?, ?, ?, ?)",
        (amount, category, note, date)
    )
    conn.commit()
    conn.close()


def get_all_bills():
    """获取所有账单，返回列表"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # 查询所有数据，默认按时间倒序排列
    cursor.execute("SELECT * FROM bills ORDER BY date DESC,id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "amount": row["amount"],
            "category": row["category"],
            "note": row["note"],
            "date": row["date"]
        })
    return result


def get_monthly_total(month_str):
    """获取某个月份的总支出（比如 month_str="2026-10"）"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 用 LIKE 和 % 模糊匹配整个月的日期，SUM 是自动求和
    cursor.execute("SELECT SUM(amount) FROM bills WHERE date LIKE ?", (month_str + "%",))
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0.0

def get_category_stats(month_str):
    """获取某个月份各分类的支出总和"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # GROUP BY 意思是按分类分组，SUM(amount) 算总和
    cursor.execute("""
        SELECT category, SUM(amount) 
        FROM bills 
        WHERE date LIKE ? 
        GROUP BY category
    """, (month_str + "%",))
    rows = cursor.fetchall()
    conn.close()
    
    # 把结果变成字典列表，方便画图
    result = []
    for row in rows:
        result.append({"分类": row[0], "金额": row[1]})
    return result

def delete_bill(bill_id):
    """根据编号删除账单"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
    conn.commit()
    conn.close()
