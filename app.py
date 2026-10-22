# -*- coding: utf-8 -*-
# 记账 APP 的网页前端界面（升级版）

import streamlit as st
import validators
import storage
import datetime
import plotly.express as px

st.set_page_config(page_title="极简记账本", page_icon="💰", layout="centered")
st.title("💰 极简记账本")

# ==================== 1. 顶部：记一笔表单 ====================
with st.form("add_bill_form", clear_on_submit=True):
    st.subheader("📝 记一笔")
    
    # 新增：收入/支出单选框
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
            # 把类型传给 storage
            storage.add_bill(valid_amount, category, note, date_str, bill_type)
            st.success("✅ 记账成功！")
            st.rerun()

# ==================== 2. 中部：统计与饼图 ====================
st.divider()
current_month = datetime.datetime.now().strftime("%Y-%m")
income, expense, balance = storage.get_monthly_stats(current_month)

# 用三列展示指标卡片
c1, c2, c3 = st.columns(3)
c1.metric(label="📥 本月收入", value=f"¥ {income:.2f}", delta="进账")
c2.metric(label="📤 本月支出", value=f"¥ {expense:.2f}", delta="-出账", delta_color="inverse")
c3.metric(label="💎 本月结余", value=f"¥ {balance:.2f}")

stats_data = storage.get_category_stats(current_month)
if stats_data:
    chart_data = {item["分类"]: item["金额"] for item in stats_data}
    fig = px.pie(
        names=list(chart_data.keys()), 
        values=list(chart_data.values()), 
        hole=0.4, title="本月支出占比"
    )
    fig.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=300)
    st.plotly_chart(fig, use_container_width=True)

# ==================== 3. 底部：账单列表 ====================
st.divider()
st.subheader("📋 历史账单")

bills = storage.get_all_bills()

if bills:
    grouped_bills = {}
    for b in bills:
        date = b["date"]
        if date not in grouped_bills:
            grouped_bills[date] = []
        grouped_bills[date].append(b)
    
    for date, day_bills in grouped_bills.items():
        # 算出这一天的支出和收入
        day_expense = sum(item["amount"] for item in day_bills if item["type"] == "支出")
        day_income = sum(item["amount"] for item in day_bills if item["type"] == "收入")
        
        st.markdown(f"### 📅 {date}")
        if day_income > 0:
            st.markdown(f"<span style='color:green;'>今日收入：+{day_income:.2f}</span> | <span style='color:red;'>今日支出：-{day_expense:.2f}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:red;'>今日支出：-{day_expense:.2f}</span>", unsafe_allow_html=True)

        for b in day_bills:
            col_info, col_btn = st.columns([4, 1])
            with col_info:
                # 如果是收入，前面加个 [+] 变绿色；支出加 [-] 变红色
                color = "green" if b['type'] == '收入' else "red"
                sign = "+" if b['type'] == '收入' else "-"
                st.markdown(f"<span style='color:{color};'>**{b['category']}** | {sign} ¥ {b['amount']:.2f}</span>  \n<small style='color:gray;'>备注：{b['note'] or '无'}</small>", unsafe_allow_html=True)
            
            with col_btn:
                if st.button("🗑️ 删除", key=f"del_{b['id']}"):
                    storage.delete_bill(b['id'])
                    st.rerun()
        
        st.markdown("<hr style='border: 1px dashed #ccc;'/>", unsafe_allow_html=True)
else:
    st.info("暂无账单，快去上面记一笔吧！")
