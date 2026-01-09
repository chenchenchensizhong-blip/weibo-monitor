import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re  # <--- 新增：引入正则表达式库，专门用来提取文本中的数字

st.set_page_config(page_title="热搜神器 Pro", page_icon="🔥", layout="wide")

st.sidebar.title("控制台 🎛️")
st.sidebar.info("这里可以筛选数据")

@st.cache_data(ttl=60)
def get_data():
    url = "https://s.weibo.com/top/summary?cate=realtimehot"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": "SUB=_2AkMSbd_Pf8NxqwJRmP4SzWjja4xzzw_EieKkgX1ZJRMxHRl-yT9jqhErtRB6PToS2X_kQd-bHwF5_0xZ_5qg1Q..;"
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('td.td-02')
        hot_list = []
        
        for item in items:
            link_tag = item.find('a')
            if link_tag:
                title = link_tag.get_text()
                link = "https://s.weibo.com" + link_tag['href']
                
                score_tag = item.find('span')
                if score_tag:
                    raw_text = score_tag.get_text() # 获取原始文本，例如 "剧集 168111" 或 "234567"
                    
                    # === 数据清洗核心逻辑 ===
                    # 使用正则表达式 r'\d+' 查找所有的数字
                    # \d 代表数字，+ 代表一个或多个
                    found_numbers = re.findall(r'\d+', raw_text)
                    
                    if found_numbers:
                        # 如果找到了数字，取第一个并转成整数
                        score_num = int(found_numbers[0])
                        # 如果原始文本里有中文（比如"剧集"），我们保留原始文本用来显示，但用数字来画图
                        display_text = raw_text 
                    else:
                        # 如果没找到数字（比如只有"置顶"、"爆"字），就设为0
                        score_num = 0
                        display_text = raw_text
                    # =======================
                    
                else:
                    display_text = "置顶"
                    score_num = 0
                
                hot_list.append({
                    "标题": title,
                    "热度显示": display_text, # 这一列给人看（包含中文）
                    "热度值": score_num,     # 这一列给电脑看（纯数字，用来排序和画图）
                    "链接": link
                })
        # 按照“热度值”从高到低重新排序，防止因为抓取顺序导致乱序
        df = pd.DataFrame(hot_list)
        return df.sort_values(by="热度值", ascending=False)

    except Exception as e:
        st.error(f"出错了: {e}")
        return None

# --- 主界面逻辑 ---
st.title("🔥 微博热搜分析台 v2.1")

with st.spinner('正在连接微博...'):
    df = get_data()

if df is not None and not df.empty:
    
    keyword = st.sidebar.text_input("🔍 搜索关键词 (例如: 剧集, 只有数字)")
    
    if keyword:
        filtered_df = df[df['标题'].str.contains(keyword)]
        st.write(f"包含 **“{keyword}”** 的热搜共有 {len(filtered_df)} 条")
    else:
        filtered_df = df

    # --- 数据可视化 ---
    st.subheader("📊 热度排行可视化")
    
    # 既然清洗了数据，我们现在可以放心地画图了
    # 取前15名，效果更好
    if not filtered_df.empty:
        chart_data = filtered_df.head(15).set_index("标题")
        st.bar_chart(chart_data['热度值'], color="#ff4b4b") 
    else:
        st.write("没有符合条件的数据可画图")

    # --- 表格展示 ---
    st.subheader("📋 详细数据表")
    
    # 显示给人看的那一列 '热度显示'
    display_df = filtered_df[['标题', '热度显示', '链接']]
    
    st.dataframe(
        display_df,
        column_config={
            "链接": st.column_config.LinkColumn("点击跳转")
        },
        use_container_width=True,
        hide_index=True
    )
    
    # 下载按钮
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下载当前结果",
        data=csv,
        file_name='weibo_hot_v2_1.csv',
        mime='text/csv',
    )
    
else:
    st.warning("暂无数据，请稍后刷新")