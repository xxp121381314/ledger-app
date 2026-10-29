# -*- coding: utf-8 -*-
import streamlit as st
import validators
import storage
import datetime
import plotly.express as px
import pandas as pd

storage.init_db()
st.set_page_config(page_title="极简记账本", page_icon="💰", layout="centered")

# ==================== 0. 密码锁与安全机制 ====================
# 从数据库获取密码，如果没设置过，就初始化一个默认的 123456
db_pwd = storage.get_setting("password", "123456")
if storage.get_setting("password", "") == "":
    storage.set_setting("password", "123456")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 隐私保护")
    pwd = st.text_input("请输入密码", type="password", placeholder="请输入您的密码")
    if st.button("进入账本", use_container_width=True):
        # 去数据库里对比密码
        if pwd == storage.get_setting("password", ""):
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("密码错误！请重试。")
    st.stop()  # 没登录成功，后面的代码不执行

# ==================== 状态管理 ====================
if 'mode' not in st.session_state:
    st.session_state.mode = 'view'
if 'edit_data' not in st.session_state:
    st.session_state.edit_data = None

def set_mode(mode, data=None):
    st.session_state.mode = mode
    st.session_state.edit_data = data
    st.rerun()

# ==================== 顶部导航 ====================
c_title, c_btn, c_logout = st.columns([3, 1.5, 1])
with c_title:
    st.title("💰 极简记账本")
with c_btn:
    if st.session_state.mode == 'view':
        if st.button("➕ 记一笔", use_container_width=True, type="primary"):
            set_mode('add')
    else:
        if st.button("❌ 取消", use_container_width=True):
            set_mode('view')
with c_logout:
    if st.button("🚪 退出", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# ==================== 侧边栏：设置与修改密码 ====================
with st.sidebar:
    st.header("⚙️ 设置")
    
    # 1. 预算设置
    current_month = datetime.datetime.now().strftime("%Y-%m")
    saved_budget = storage.get_setting("budget", "2000")
    new_budget = st.number_input(f"设置本月总预算 (元)", value=float(saved_budget), step=100.0)
    if new_budget != float(saved_budget):
        storage.set_setting("budget", new_budget)
        st.rerun()
        
    st.divider()
    
    # 2. 修改密码
    with st.expander("🔐 修改密码"):
        old_pwd = st.text_input("原密码", type="password", key="old_pwd")
        new_pwd = st.text_input("新密码", type="password", key="new_pwd")
        confirm_pwd = st.text_input("确认新密码", type="password", key="confirm_pwd")
        if st.button("确认修改密码"):
            if old_pwd != storage.get_setting("password", ""):
                st.error("原密码错误！")
            elif new_pwd != confirm_pwd:
                st.error("两次输入的新密码不一致！")
            elif len(new_pwd) < 4:
                st.error("新密码长度不能少于4位！")
            else:
                storage.set_setting("password", new_pwd)
                st.success("密码修改成功！下次登录请用新密码。")

# ==================== 表单区域 (新增/修改) ====================
if st.session_state.mode in ['add', 'edit']:
    is_edit = (st.session_state.mode == 'edit')
    data = st.session_state.edit_data
    
    st.subheader("✏️ 修改账单" if is_edit else "📝 记一笔")
    
    with st.form("bill_form", clear_on_submit=not is_edit):
        default_amount = str(data['amount']) if is_edit else ""
        default_date = datetime.datetime.strptime(data['date'], "%Y-%m-%d").date() if is_edit else datetime.date.today()
        default_type = data['type'] if is_edit else "支出"
        default_category = data['category'] if is_edit else validators.CATEGORIES[0]
        default_note = data['note'] if is_edit else ""
        default_account = data['account'] if is_edit else "微信"

        categories = validators.CATEGORIES.copy()
        if default_category not in categories: categories.append(default_category)
            
        ACCOUNTS = ["微信", "支付宝", "银行卡", "现金", "其他"]

        bill_type = st.radio("类型", ["支出", "收入"], index=0 if default_type=="支出" else 1, horizontal=True)
        
        col1, col2 = st.columns(2)
        with col1:
            amount_str = st.text_input("金额", value=default_amount, placeholder="例如 35.5")
            category = st.selectbox("分类", categories, index=categories.index(default_category))
        with col2:
            date_obj = st.date_input("日期", value=default_date)
            account = st.selectbox("账户", ACCOUNTS, index=ACCOUNTS.index(default_account) if default_account in ACCOUNTS else 0)
            
        note = st.text_input("备注（可选）", value=default_note)
        
        submitted = st.form_submit_button("保存", use_container_width=True, type="primary")
        
        if submitted:
            valid_amount = validators.validate_amount(amount_str)
            if valid_amount is None:
                st.error("❌ 金额不合法！")
            else:
                date_str = date_obj.strftime("%Y-%m-%d")
                if is_edit:
                    storage.update_bill(data['id'], valid_amount, category, note, date_str, bill_type, account)
                    st.success("✅ 修改成功！")
                else:
                    storage.add_bill(valid_amount, category, note, date_str, bill_type, account)
                    st.success("✅ 记账成功！")
                set_mode('view')

# ==================== 列表区域 ====================
elif st.session_state.mode == 'view':
    st.divider()
    now = datetime.datetime.now()
    months_list = [(now - datetime.timedelta(days=30*i)).strftime("%Y-%m") for i in range(12)]
    
    col_f1, col_f2 = st.columns(2)
    with col_f1: selected_month = st.selectbox("选择月份", months_list)
    with col_f2: keyword = st.text_input("搜索（备注/分类）", placeholder="比如：吃饭")
    
    filtered_bills = storage.get_bills_by_filter(selected_month, keyword)
    income, expense, balance = storage.get_monthly_stats(selected_month)
    
    c1, c2, c3 = st.columns(3)
    c1.metric(label="📥 收入", value=f"¥ {income:.2f}")
    c2.metric(label="📤 支出", value=f"¥ {expense:.2f}")
    c3.metric(label="💎 结余", value=f"¥ {balance:.2f}")

    # --- 预算预警 ---
    if float(saved_budget) > 0:
        ratio = expense / float(saved_budget)
        if ratio > 1.0:
            st.error(f"🚨 警告：本月支出已超预算！(已花 ¥{expense:.2f} / 预算 ¥{float(saved_budget):.2f})")
        elif ratio > 0.8:
            st.warning(f"⚠️ 注意：本月支出已达预算的 {ratio*100:.0f}%！")
        else:
            st.progress(ratio, text=f"本月预算使用进度：{ratio*100:.1f}%")

    # --- 图表 ---
    stats_data = storage.get_category_stats(selected_month)
    if stats_data:
        col_pie, col_line = st.columns(2)
        with col_pie:
            chart_data = {item["分类"]: item["金额"] for item in stats_data}
            fig_pie = px.pie(names=list(chart_data.keys()), values=list(chart_data.values()), hole=0.4, title="分类占比")
            fig_pie.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=250, showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_line:
            trend_data = storage.get_daily_trends(selected_month)
            if trend_data:
                fig_line = px.line(x=list(trend_data.keys()), y=list(trend_data.values()), title="每日支出趋势", markers=True)
                fig_line.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=250, xaxis_title="", yaxis_title="")
                st.plotly_chart(fig_line, use_container_width=True)

    # --- 导出功能 ---
    if filtered_bills:
        df = pd.DataFrame(filtered_bills)
        df = df[['date', 'type', 'category', 'amount', 'account', 'note']]
        df.columns = ["日期", "类型", "分类", "金额(元)", "账户", "备注"]
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(label="📥 导出当前账单 (CSV)", data=csv, file_name=f"账单_{selected_month}.csv", mime="text/csv")

    # --- 账单列表 ---
    st.divider()
    st.subheader("📋 账单明细")
    
    if filtered_bills:
        grouped_bills = {}
        for b in filtered_bills:
            if b["date"] not in grouped_bills: grouped_bills[b["date"]] = []
            grouped_bills[b["date"]].append(b)
        
        for date, day_bills in grouped_bills.items():
            day_expense = sum(item["amount"] for item in day_bills if item["type"] == "支出")
            day_income = sum(item["amount"] for item in day_bills if item["type"] == "收入")
            
            st.markdown(f"#### 📅 {date}")
            if day_income > 0:
                st.markdown(f"<span style='color:green;font-size:14px;'>收：+{day_income:.2f}</span> | <span style='color:red;font-size:14px;'>支：-{day_expense:.2f}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:red;font-size:14px;'>支：-{day_expense:.2f}</span>", unsafe_allow_html=True)
    
            for b in day_bills:
                col_info, col_edit, col_del = st.columns([5, 1, 1])
                with col_info:
                    color = "green" if b['type'] == '收入' else "red"
                    sign = "+" if b['type'] == '收入' else "-"
                    st.markdown(f"<span style='color:{color};'>**{b['category']}** | {sign} ¥ {b['amount']:.2f}</span> <span style='color:gray;font-size:12px;'>[{b['account']}]</span> <br><small style='color:gray;'>{b['note'] or ''}</small>", unsafe_allow_html=True)
                
                with col_edit:
                    if st.button("✏️", key=f"edit_{b['id']}"): set_mode('edit', b)
                with col_del:
                    if st.button("🗑️", key=f"del_{b['id']}"):
                        storage.delete_bill(b['id'])
                        st.rerun()
            
            st.markdown("<hr style='border: 1px dashed #ddd; margin: 5px 0;'/>", unsafe_allow_html=True)
    else:
        st.info("没有找到符合条件的账单。")

    # --- 数据导入区 ---
    st.divider()
    with st.expander("💾 数据恢复 (导入)"):
        uploaded_file = st.file_uploader("选择账单文件 (.xlsx 或 .csv)", type=["csv", "xlsx"])
        if uploaded_file is not None:
            if st.button("确认导入", type="primary"):
                try:
                    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                    count = storage.import_bills(df.to_dict('records'))
                    st.success(f"✅ 成功导入 {count} 条账单！")
                    st.rerun()
                except Exception as e:
                    st.error(f"读取失败：{e}")
