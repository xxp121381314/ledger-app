# -*- coding: utf-8 -*-
# 记账 APP 的网页前端界面 - 优化版

import streamlit as st
import validators
import storage
import datetime
import plotly.express as px

# 页面设置：使用 centered 模式，在手机和电脑上都不会太宽
st.set_page_config(page_title="极简记账本", page_icon="💰", layout="centered")
st.title("💰 极简记账本")

# ==================== 1. 顶部：记一笔表单 ====================
with st.form("add_bill_form", clear_on_submit=True):
    st.subheader("📝 记一笔")
    
    # 使用两列布局，手机上会自动上下堆叠
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
            storage.add_bill(valid_amount, category, note, date_str)
            st.success("✅ 记账成功！")
            st.rerun()

# ==================== 2. 中部：统计与饼图 ====================
st.divider()
current_month = datetime.datetime.now().strftime("%Y-%m")
monthly_total = storage.get_monthly_total(current_month)

# 用带颜色的指标卡片展示
st.metric(label=f"📊 {current_month} 月总支出", value=f"¥ {monthly_total:.2f}")

stats_data = storage.get_category_stats(current_month)
if stats_data:
    # 把数据转成字典给 Plotly
    chart_data = {item["分类"]: item["金额"] for item in stats_data}
    
    # 使用 Plotly 画饼图
    fig = px.pie(
        names=list(chart_data.keys()), 
        values=list(chart_data.values()), 
        hole=0.4, # 中间挖个洞，变成环形图更好看
        title="分类支出占比"
    )
    fig.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=300)
    st.plotly_chart(fig, use_container_width=True)

# ==================== 3. 底部：账单列表与行内删除 ====================
# ==================== 3. 底部：账单列表（按日期合并） ====================
st.divider()
st.subheader("📋 历史账单")

bills = storage.get_all_bills()

if bills:
    # 核心逻辑：把同一天的账单归类到一个“字典”里
    grouped_bills = {}
    for b in bills:
        date = b["date"]
        if date not in grouped_bills:
            grouped_bills[date] = []
        grouped_bills[date].append(b)
    
    # 遍历每一天
    for date, day_bills in grouped_bills.items():
        # 算出这一天的总支出
        day_total = sum(item["amount"] for item in day_bills)
        
        # 显示当天的标题和总计（用 st.markdown 画一条好看的标题）
        st.markdown(f"### 📅 {date} | 当天总支出：**¥ {day_total:.2f}**")
        
        # 遍历当天的每一笔账单
        for b in day_bills:
            col_info, col_btn = st.columns([4, 1])
            
            with col_info:
                # 为了让合并后看起来不那么单调，前面加个小圆点
                st.markdown(f"● **{b['category']}** | ¥ {b['amount']:.2f}  \n<small style='color:gray;'>备注：{b['note'] or '无'}</small>", unsafe_allow_html=True)
            
            with col_btn:
                if st.button("🗑️ 删除", key=f"del_{b['id']}"):
                    storage.delete_bill(b['id'])
                    st.rerun()
        
        # 每一天结束后，画一条虚线分隔开
        st.markdown("<hr style='border: 1px dashed #ccc;'/>", unsafe_allow_html=True)
else:
    st.info("暂无账单，快去上面记一笔吧！")
