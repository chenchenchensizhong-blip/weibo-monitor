import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import altair as alt  # <--- 新增：引入更强大的绘图库 (Streamlit自带)

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
                    raw_text = score_tag.get_text()
                    # 正则提取数字
                    found_numbers = re.findall(r'\d+', raw_text)
                    if found_numbers:
                        score_num = int(found_numbers[0])
                        display_text = raw_text 
                    else:
                        score_num = 0
                        display_text = raw_text
                else:
                    display_text = "置顶"
                    score_num = 0
                
                hot_list.append({
                    "标题": title,
                    "热度显示": display_text, 
                    "热度值": score_num,   
                    "链接": link
                })
        
        df = pd.DataFrame(hot_list)
        # 数据层面先排一次序
        return df.sort_values(by="热度值", ascending=False)

    except Exception as e:
        st.error(f"出错了: {e}")
        return None

# --- 主界面逻辑 ---
st.title("🔥 微博热搜分析台 v2.2")

with st.spinner('正在连接微博...'):
    df = get_data()

if df is not None and not df.empty:
    
    keyword = st.sidebar.text_input("🔍 搜索关键词 (例如: 剧集)")
    
    if keyword:
        filtered_df = df[df['标题'].str.contains(keyword)]
        st.write(f"包含 **“{keyword}”** 的热搜共有 {len(filtered_df)} 条")
    else:
        filtered_df = df

    # --- 数据可视化 (升级版) ---
    st.subheader("📊 热度排行可视化")
    
    if not filtered_df.empty:
        # 只取前 15 名画图，避免太拥挤
        chart_data = filtered_df.head(15)
        
        # 使用 Altair 画图，它能精准控制排序
        chart = alt.Chart(chart_data).mark_bar().encode(
            # X轴：显示标题，sort='-y' 表示按照 Y 轴的数据倒序排列 (从大到小)
            x=alt.X('标题', sort='-y', axis=alt.Axis(labelAngle=-45)), 
            # Y轴：显示热度值
            y='热度值',
            # 颜色：根据热度值变色，越热越红
            color=alt.Color('热度值', scale=alt.Scale(scheme='reds')),
            # 鼠标悬停提示 (Tooltip)
            tooltip=['标题', '热度显示', '热度值']
        )
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("没有符合条件的数据可画图")

    # --- 表格展示 ---
    st.subheader("📋 详细数据表")
    
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
        file_name='weibo_hot_v2_2.csv',
        mime='text/csv',
    )
    
else:
    st.warning("暂无数据，请稍后刷新")