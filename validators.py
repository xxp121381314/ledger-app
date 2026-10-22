# -*- coding: utf-8 -*-
# 记账 APP 的校验模块

# 允许的分类列表
CATEGORIES = ["餐饮", "交通", "购物", "娱乐","医疗", "其他"]

def validate_amount(amount_str):
    """
    检查金额是否合法：必须是数字，且大于 0。
    输入：amount_str（字符串）
    输出：合法返回 float 类型，不合法返回 None。
    """
    try:
        num = float(amount_str)  # 尝试把文字转成小数
        if num > 0:              # 如果大于 0
            return num           # 交差，返回这个数字
    except ValueError:
        # 如果用户输入的不是数字（比如"abc"），float会报错
        # 走到这里，我们啥也不干，直接跳过
        pass
    
    return None                  # 只要没成功 return，就说明不合法，返回 None


def validate_category(category_str):
    """
    检查分类是否在允许的列表里。
    输入：category_str（字符串）
    输出：合法返回该分类字符串，不合法返回 None。
    """
    if category_str in CATEGORIES:
        return category_str      # 在名单里，放行
    else:
        return None              # 不在名单里，返回空
