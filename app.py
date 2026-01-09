import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

st.set_page_config(page_title="热搜神器 Pro", page_icon="🔥", layout="wide") # layout="wide" 让页面变宽

# --- 侧边栏设置 (新功能) ---
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
                    score_str = score_tag.get_text()
                    # 尝试把 "123456" 这种文字转成数字，方便画图
                    try:
                        score_num = int(score_str)
                    except:
                        score_num = 0 # 如果是"置顶"或"新"，给0分
                else:
                    score_str = "置顶"
                    score_num = 0
                
                hot_list.append({
                    "标题": title,
                    "热度显示": score_str, # 给表格看
                    "热度值": score_num,   # 给画图用
                    "链接": link
                })
        return pd.DataFrame(hot_list)
    except Exception as e:
        st.error(f"出错了: {e}")
        return None

# --- 主界面逻辑 ---
st.title("🔥 微博热搜分析台 v2.0")

# 1. 获取数据
with st.spinner('正在连接微博...'):
    df = get_data()

if df is not None and not df.empty:
    
    # --- 新功能：侧边栏筛选 ---
    # 在侧边栏加一个输入框
    keyword = st.sidebar.text_input("🔍 搜索关键词 (例如: 游戏, 明星名)")
    
    # 如果用户输入了内容，就过滤表格
    if keyword:
        # 这一句是 Pandas 的筛选魔法：只要标题包含关键词，就留下来
        filtered_df = df[df['标题'].str.contains(keyword)]
        st.write(f"包含 **“{keyword}”** 的热搜共有 {len(filtered_df)} 条")
    else:
        filtered_df = df # 没输入就显示全部

    # --- 新功能：数据可视化 (柱状图) ---
    st.subheader("📊 热度排行可视化")
    
    # 只画前10名，不然图太挤了
    chart_data = filtered_df.head(10).set_index("标题") # 把标题设为横坐标
    
    # Streamlit 自带的柱状图，指定用 '热度值' 这一列来画高低
    st.bar_chart(chart_data['热度值'], color="#ff4b4b") 

    # --- 表格展示 ---
    st.subheader("📋 详细数据表")
    
    # 只要展示用的几列，把用来画图的 '热度值' 隐藏掉，美观一点
    display_df = filtered_df[['标题', '热度显示', '链接']]
    
    st.dataframe(
        display_df,
        column_config={
            "链接": st.column_config.LinkColumn("点击跳转")
        },
        use_container_width=True,
        hide_index=True # 隐藏掉 0,1,2 这种索引列
    )
    
    # 下载按钮 (保持不变)
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下载当前结果",
        data=csv,
        file_name='weibo_hot_v2.csv',
        mime='text/csv',
    )
    
else:
    st.warning("暂无数据")