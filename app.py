# -*- coding: utf-8 -*-
import streamlit as st
import validators
import storage
import datetime
import plotly.express as px
import pandas as pd

# 初始化数据库
storage.init_db()

st.set_page_config(page_title="极简记账本", page_icon="💰", layout="centered")
st.title("💰 极简记账本")

# ==================== 1. 记一笔 ====================
with st.form("add_bill_form", clear_on_submit=True):
    st.subheader("📝 记一笔")
    
    # 顶部类型选择
    bill_type = st.radio("类型", ["支出", "收入"], horizontal=True)
    
    col1, col2 = st.columns(2)
    with col1:
        amount_str = st.text_input("金额", placeholder="例如 35.5")
        category = st.selectbox("分类", validators.CATEGORIES)
    with col2:
        date_obj = st.date_input("日期", datetime.date.today())
        note = st.text_input("备注（可选）", placeholder="比如：午饭")
    
    submitted = st.form_submit_button("保存账单", use_container_width=True)

    if submitted:
        valid_amount = validators.validate_amount(amount_str)
        if valid_amount is None:
            st.error("❌ 金额不合法！必须是大于 0 的数字。")
        else:
            date_str = date_obj.strftime("%Y-%m-%d")
            storage.add_bill(valid_amount, category, note, date_str, bill_type)
            st.success("✅ 记账成功！")
            st.rerun()

# ==================== 2. 筛选与数据统计 ====================
st.divider()
st.subheader("🔍 筛选与统计")

# 生成过去 12 个月的列表
now = datetime.datetime.now()
months_list = [(now - datetime.timedelta(days=30*i)).strftime("%Y-%m") for i in range(12)]

col_f1, col_f2 = st.columns(2)
with col_f1:
    selected_month = st.selectbox("选择月份", months_list)
with col_f2:
    keyword = st.text_input("搜索（备注/分类）", placeholder="比如：吃饭")

# 查询数据
filtered_bills = storage.get_bills_by_filter(selected_month, keyword)
income, expense, balance = storage.get_monthly_stats(selected_month)

# 展示三个指标卡片
c1, c2, c3 = st.columns(3)
c1.metric(label="📥 收入", value=f"¥ {income:.2f}")
c2.metric(label="📤 支出", value=f"¥ {expense:.2f}")
c3.metric(label="💎 结余", value=f"¥ {balance:.2f}")

# ==================== 3. 图表与导出 ====================
stats_data = storage.get_category_stats(selected_month)
if stats_data:
    col_chart, col_export = st.columns([3, 1])
    
    with col_chart:
        chart_data = {item["分类"]: item["金额"] for item in stats_data}
        fig = px.pie(
            names=list(chart_data.keys()), 
            values=list(chart_data.values()), 
            hole=0.4, title=f"{selected_month} 支出占比"
        )
        fig.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=280)
        st.plotly_chart(fig, use_container_width=True)
        
    with col_export:
        st.write("") # 占位
        st.write("") 
        # 把账单转成 DataFrame 导出
        if filtered_bills:
            df = pd.DataFrame(filtered_bills)
            # 重命名列名，去除不需要导出的 id
            df = df[['date', 'type', 'category', 'amount', 'note']]
            df.columns = ["日期", "类型", "分类", "金额(元)", "备注"]
            csv = df.to_csv(index=False).encode('utf-8-sig') # utf-8-sig 防止 Excel 乱码
            
            st.download_button(
                label="📥 导出为 CSV",
                data=csv,
                file_name=f"账单_{selected_month}.csv",
                mime="text/csv",
                use_container_width=True
            )

# ==================== 4. 历史账单列表 ====================
st.divider()
st.subheader("📋 账单明细")

if filtered_bills:
    grouped_bills = {}
    for b in filtered_bills:
        date = b["date"]
        if date not in grouped_bills:
            grouped_bills[date] = []
        grouped_bills[date].append(b)
    
    for date, day_bills in grouped_bills.items():
        day_expense = sum(item["amount"] for item in day_bills if item["type"] == "支出")
        day_income = sum(item["amount"] for item in day_bills if item["type"] == "收入")
        
        # 每日标题
        st.markdown(f"#### 📅 {date}")
        if day_income > 0:
            st.markdown(f"<span style='color:green;font-size:14px;'>今日收入：+{day_income:.2f}</span> | <span style='color:red;font-size:14px;'>今日支出：-{day_expense:.2f}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:red;font-size:14px;'>今日支出：-{day_expense:.2f}</span>", unsafe_allow_html=True)

        # 每日明细
        for b in day_bills:
            col_info, col_btn = st.columns([4, 1])
            with col_info:
                color = "green" if b['type'] == '收入' else "red"
                sign = "+" if b['type'] == '收入' else "-"
                st.markdown(f"<span style='color:{color};'>**{b['category']}** | {sign} ¥ {b['amount']:.2f}</span>  \n<small style='color:gray;'>备注：{b['note'] or '无'}</small>", unsafe_allow_html=True)
            
            with col_btn:
                if st.button("🗑️ 删除", key=f"del_{b['id']}"):
                    storage.delete_bill(b['id'])
                    st.rerun()
        
        st.markdown("<hr style='border: 1px dashed #ddd; margin: 10px 0;'/>", unsafe_allow_html=True)
else:
    st.info("没有找到符合条件的账单。")
