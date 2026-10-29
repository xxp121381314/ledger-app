def import_bills(bills_data):
    """批量导入账单数据，完美兼容钱迹导出格式和本软件导出格式"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    success_count = 0
    
    for row in bills_data:
        try:
            # 1. 兼容金额列名
            amount = float(row.get('金额(元)', row.get('金额')))
            
            # 2. 兼容时间列名，并把 "2026-10-28 17:17:00" 截断成 "2026-10-28"
            raw_date = str(row.get('日期', row.get('时间', '')))
            date_str = raw_date.split(' ')[0] if raw_date else "2026-10-01"
            
            # 3. 兼容分类（直接使用钱迹原本的分类，不强制覆盖）
            category = str(row.get('分类', '其它'))
            
            # 4. 处理备注（防止空值变成字符串'nan'）
            note = str(row.get('备注', ''))
            if note == 'nan':
                note = ''
                
            # 5. 兼容类型（钱迹可能有转账等，我们都暂时算作支出）
            bill_type = str(row.get('类型', '支出'))
            if bill_type not in ['支出', '收入']:
                bill_type = '支出'
                
            cursor.execute(
                "INSERT INTO bills (amount, category, note, date, type) VALUES (?, ?, ?, ?, ?)",
                (amount, category, note, date_str, bill_type)
            )
            success_count += 1
        except Exception as e:
            # 遇到坏数据直接跳过，不影响其他行导入
            pass 
            
    conn.commit()
    conn.close()
    return success_count
