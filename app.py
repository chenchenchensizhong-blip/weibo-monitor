import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# --- 1. 网页基础设置 ---
# 设置网页的标题和图标
st.set_page_config(page_title="我的热搜神器", page_icon="🔥")

# 网页的大标题
st.title("🔥 微博热搜实时监控")
st.write("这是我开发的第一个网页程序！")

# --- 2. 定义抓取数据的工具 (函数) ---
# @st.cache_data 是 Streamlit 的魔法，让它不要每次刷新都重新抓取，防止被封，每60秒过期一次
@st.cache_data(ttl=60)
def get_data():
    # 目标网址
    url = "https://s.weibo.com/top/summary?cate=realtimehot"
    # 伪装成浏览器，否则微博不理我们
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": "SUB=_2AkMSbd_Pf8NxqwJRmP4SzWjja4xzzw_EieKkgX1ZJRMxHRl-yT9jqhErtRB6PToS2X_kQd-bHwF5_0xZ_5qg1Q..;" 
    }
    
    try:
        # 发送请求
        response = requests.get(url, headers=headers)
        
        # 解析网页
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 找到所有热搜条目 (在网页代码里它们通常在 td 标签下)
        items = soup.select('td.td-02')
        
        # 准备一个空列表装数据
        hot_list = []
        
        for item in items:
            link_tag = item.find('a') # 找到链接标签
            if link_tag:
                title = link_tag.get_text() # 获取标题文字
                link = "https://s.weibo.com" + link_tag['href'] # 获取完整链接
                
                # 获取热度值 (有些置顶广告没有热度值，要处理一下)
                score_tag = item.find('span')
                if score_tag:
                    score = score_tag.get_text()
                else:
                    score = "置顶"
                
                # 把这一条存进去
                hot_list.append({
                    "标题": title,
                    "热度": score,
                    "链接": link
                })
                
        # 转换成表格格式返回
        return pd.DataFrame(hot_list)
        
    except Exception as e:
        st.error(f"出错了: {e}")
        return None

# --- 3. 网页交互逻辑 ---

# 放置一个按钮
if st.button('点击刷新热搜'):
    st.cache_data.clear() # 清除缓存，强制刷新
    st.rerun() # 重新运行程序

# 显示加载状态
with st.spinner('正在从微博偷瞄数据...'):
    df = get_data() # 调用上面的函数

# --- 4. 展示结果 ---
if df is not None and not df.empty:
    top_10 = df.head(10)
    
    col1, col2 = st.columns(2)
    col1.metric("当前第一名", top_10.iloc[0]['标题'])
    col2.metric("热度值", top_10.iloc[0]['热度'])
    
    st.subheader("前 10 名榜单")
    st.dataframe(
        top_10,
        column_config={
            "链接": st.column_config.LinkColumn("点击跳转")
        },
        use_container_width=True
    )

    # === 新增：防乱码下载按钮 ===
    # 1. 把数据转换成 csv 字符串，并指定编码为 utf-8-sig (Excel 专供)
    csv = df.to_csv(index=False).encode('utf-8-sig')
    
    # 2. 显示下载按钮
    st.download_button(
        label="📥 下载数据 (Excel打开不乱码)",
        data=csv,
        file_name='weibo_hot_search.csv',
        mime='text/csv',
    )
    # ==========================

else:
    st.warning("⚠️ 成功连接了微博，但没有抓到数据。")
    st.info("这通常是因为微博开启了反爬虫防御，请稍后再试。")