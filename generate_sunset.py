import pandas as pd
import glob
import os
from datetime import datetime

# ================= 配置区 =================
# 1. 数据源路径 (保持不变)
CSV_DIR = r"\\10.155.154.102\晚霞预报" 

# 2. 输出路径 (已修改为你指定的桌面路径)
OUTPUT_DIR = r"C:\Users\Administrator\Desktop\sunset-web"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")

# 确保输出目录存在，如果不存在则自动创建
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
# =========================================

def get_latest_csv():
    """自动获取最新日期的CSV文件"""
    today_str = datetime.now().strftime('%Y%m%d')
    csv_pattern = os.path.join(CSV_DIR, f'{today_str}.csv')
    files = glob.glob(csv_pattern)
    
    if not files:
        print(f"❌ 未找到今日文件: {csv_pattern}")
        return None
    
    return files[0]

def clean_location_name(name):
    """去掉地名中的'东方市'前缀"""
    if isinstance(name, str) and name.startswith("东方市"):
        return name.replace("东方市", "")
    return name

def format_time_only(time_str):
    """将 '2026-07-30 18:54:37' 转换为 '18:54'，只保留时分"""
    if not isinstance(time_str, str) or len(time_str) < 16:
        return time_str
    try:
        # 假设格式为 YYYY-MM-DD HH:MM:SS，取第11到16位字符
        return time_str[11:16]
    except:
        return time_str

def format_date_display(date_str):
    """将 '20260730' 或 '2026-07-30' 转换为 '7月30日' 或 '30日' 格式"""
    s = str(date_str).replace('-', '').replace('/', '')
    if len(s) == 8:
        month = int(s[4:6])
        day = int(s[6:8])
        return f"{month}月{day}日"
    return date_str

def generate_html(df):
    """生成包含交互逻辑的HTML"""
    
    # 1. 数据预处理
    df['观赏点'] = df['观赏点'].apply(clean_location_name)
    
    # 处理时间字段 (只留时分)
    if '日落时间' in df.columns:
        df['日落时间'] = df['日落时间'].apply(format_time_only)
    if '预计开始时间' in df.columns:
        df['预计开始时间'] = df['预计开始时间'].apply(format_time_only)
    if '预计结束时间' in df.columns:
        df['预计结束时间'] = df['预计结束时间'].apply(format_time_only)
        
    # 确保概率保留两位小数
    if '出现概率' in df.columns:
        df['出现概率'] = pd.to_numeric(df['出现概率'], errors='coerce').round(2)
    
    # 提取唯一的地点和日期
    locations = sorted(df['观赏点'].unique().tolist())
    # 日期正序排列 (从早到晚)
    dates_raw = sorted(df['预报日期'].unique().tolist())
    
    # 构建用于显示的日期列表 (例如: ["7月30日", "7月31日"])
    dates_display = [format_date_display(d) for d in dates_raw]
    
    # 将DataFrame转换为JSON字符串嵌入JS
    data_json = df.to_json(orient='records', force_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>东方市晚霞预报</title>
    <style>
        :root {{ 
            --primary-color: #ff6b6b; 
            --bg-color: #fff5f5; 
            --card-bg: #ffffff;
            --text-main: #333333;
            --text-sub: #666666;
        }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            background-color: var(--bg-color); 
            margin: 0; 
            padding: 0; 
            color: var(--text-main); 
            -webkit-font-smoothing: antialiased;
        }}
        
        /* 顶部标题栏 */
        header {{ 
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); 
            padding: 20px 15px; 
            text-align: center; 
            box-shadow: 0 2px 10px rgba(255, 107, 107, 0.1);
        }}
        h1 {{ margin: 0; color: #d63031; font-size: 1.4rem; font-weight: 700; letter-spacing: 1px; }}
        
        /* 一级导航：左右滑动的观赏点 */
        .location-scroller {{
            display: flex;
            overflow-x: auto;
            white-space: nowrap;
            padding: 15px;
            background: #fff;
            -webkit-overflow-scrolling: touch; /* iOS顺滑滚动 */
            scrollbar-width: none; /* Firefox隐藏滚动条 */
        }}
        .location-scroller::-webkit-scrollbar {{ display: none; /* Chrome/Safari隐藏滚动条 */ }}
        
        .loc-tab {{
            display: inline-block;
            padding: 8px 18px;
            margin-right: 12px;
            border-radius: 20px;
            background: #f0f0f0;
            color: #666;
            font-size: 0.95rem;
            font-weight: 500;
            transition: all 0.3s ease;
            cursor: pointer;
            border: 1px solid transparent;
        }}
        .loc-tab.active {{
            background: var(--primary-color);
            color: white;
            box-shadow: 0 4px 10px rgba(255, 107, 107, 0.3);
            transform: scale(1.05);
        }}

        /* 二级导航：日期选择胶囊 */
        .date-selector {{
            display: flex;
            justify-content: center;
            gap: 15px;
            padding: 10px 15px 20px;
            background: #fff;
            border-bottom-left-radius: 20px;
            border-bottom-right-radius: 20px;
            margin-bottom: 10px;
        }}
        .date-pill {{
            padding: 8px 20px;
            border-radius: 12px;
            background: #fff;
            border: 1px solid #eee;
            color: var(--text-sub);
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            min-width: 60px;
            text-align: center;
        }}
        .date-pill.active {{
            background: #fff0f0;
            border-color: var(--primary-color);
            color: var(--primary-color);
        }}

        /* 内容展示区 */
        .content-area {{ 
            padding: 0 15px 30px; 
            max-width: 600px; 
            margin: 0 auto;
        }}
        
        /* 数据卡片设计 - 纵向堆叠，内容饱满 */
        .forecast-card {{
            background: var(--card-bg);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            display: grid;
            grid-template-columns: repeat(2, 1fr); /* 两列布局 */
            gap: 15px; /* 间距 */
        }}
        
        /* 全宽项 (如描述) */
        .full-width {{
            grid-column: span 2;
            border-bottom: 1px dashed #eee;
            padding-bottom: 12px;
            margin-bottom: 5px;
        }}

        .data-item {{
            display: flex;
            flex-direction: column; /* 上下结构 */
            justify-content: flex-start;
        }}
        
        .data-label {{
            font-size: 0.85rem;
            color: #999;
            margin-bottom: 6px; /* 标签和数值的间距 */
        }}
        
        .data-value {{
            font-size: 1.15rem; /* 字体加大 */
            font-weight: 700;
            color: #333;
            line-height: 1.2;
        }}
        
        /* 特殊样式 */
        .highlight-text {{ color: var(--primary-color); }}
        
        .level-badge {{ 
            display: inline-block; 
            padding: 4px 12px; 
            border-radius: 6px; 
            color: white; 
            font-size: 1rem; 
            font-weight: bold;
        }}
        .level-1 {{ background-color: #2ecc71; }} 
        .level-2 {{ background-color: #f1c40f; color: #333; }} 
        .level-3 {{ background-color: #e67e22; }} 
        .level-4 {{ background-color: #e74c3c; }} 
        .level-5 {{ background-color: #8e44ad; }}

        .empty-tip {{ text-align: center; color: #999; margin-top: 50px; font-size: 1rem; }}
    </style>
</head>
<body>

<header>
    <h1>🌅 东方市晚霞预报</h1>
</header>

<!-- 一级导航：地点滑动 -->
<div class="location-scroller" id="locContainer">
    <!-- JS填充 -->
</div>

<!-- 二级导航：日期切换 -->
<div class="date-selector" id="dateContainer">
    <!-- JS填充 -->
</div>

<!-- 数据展示 -->
<div id="resultArea" class="content-area">
    <!-- JS填充 -->
</div>

<script>
    // 注入Python处理好的数据
    const rawData = {data_json};
    const locations = {locations};
    const datesRaw = {dates_raw};
    const datesDisplay = {dates_display};

    const locContainer = document.getElementById('locContainer');
    const dateContainer = document.getElementById('dateContainer');
    const resultArea = document.getElementById('resultArea');

    let currentLoc = locations[0];
    let currentDate = datesRaw[0];

    // 初始化
    function init() {{
        // 渲染地点 tabs
        locations.forEach((loc, index) => {{
            const tab = document.createElement('div');
            tab.className = `loc-tab ${{index === 0 ? 'active' : ''}}`;
            tab.innerText = loc;
            tab.onclick = () => switchLocation(loc, tab);
            locContainer.appendChild(tab);
        }});

        renderDates();
        renderData();
    }}

    function switchLocation(newLoc, tabElement) {{
        currentLoc = newLoc;
        // 更新 Tab 样式
        document.querySelectorAll('.loc-tab').forEach(t => t.classList.remove('active'));
        tabElement.classList.add('active');
        renderData();
    }}

    function renderDates() {{
        dateContainer.innerHTML = '';
        datesRaw.forEach((date, index) => {{
            const pill = document.createElement('div');
            pill.className = `date-pill ${{date === currentDate ? 'active' : ''}}`;
            pill.innerText = datesDisplay[index]; // 使用格式化后的 "7月30日"
            pill.onclick = () => switchDate(date, pill);
            dateContainer.appendChild(pill);
        }});
    }}

    function switchDate(newDate, pillElement) {{
        currentDate = newDate;
        document.querySelectorAll('.date-pill').forEach(p => p.classList.remove('active'));
        pillElement.classList.add('active');
        renderData();
    }}

    function renderData() {{
        // 筛选数据
        const filtered = rawData.filter(item => 
            item['观赏点'] === currentLoc && String(item['预报日期']) === String(currentDate)
        );

        if (filtered.length === 0) {{
            resultArea.innerHTML = '<div class="empty-tip">该日期暂无预报数据</div>';
            return;
        }}

        let html = '';
        filtered.forEach(item => {{
            // 处理等级颜色
            let levelClass = 'level-' + item['晚霞等级'];
            
            html += `
            <div class="forecast-card">
                <!-- 第一行：晚霞描述 (全宽) -->
                <div class="data-item full-width">
                    <span class="data-label">晚霞描述</span>
                    <span class="data-value">${{item['晚霞描述'] || '暂无描述'}}</span>
                </div>

                <!-- 第二行：等级 & 概率 -->
                <div class="data-item">
                    <span class="data-label">晚霞等级</span>
                    <div><span class="level-badge ${{levelClass}}">${{item['晚霞等级']}} 级</span></div>
                </div>
                <div class="data-item">
                    <span class="data-label">出现概率</span>
                    <span class="data-value highlight-text">${{item['出现概率']}}%</span>
                </div>

                <!-- 第三行：日落时间 & 预计开始 -->
                <div class="data-item">
                    <span class="data-label">日落时间</span>
                    <span class="data-value">${{item['日落时间'] || '--:--'}}</span>
                </div>
                <div class="data-item">
                    <span class="data-label">预计开始</span>
                    <span class="data-value">${{item['预计开始时间'] || '--:--'}}</span>
                </div>

                <!-- 第四行：预计结束 (单独一行或补位，这里为了平衡放左边，右边留空或放其他) -->
                <div class="data-item">
                    <span class="data-label">预计结束</span>
                    <span class="data-value">${{item['预计结束时间'] || '--:--'}}</span>
                </div>
            </div>`;
        }});

        resultArea.innerHTML = html;
    }}

    // 启动
    init();
</script>

</body>
</html>"""
    return html_content

if __name__ == "__main__":
    print("⏳ 正在读取最新数据...")
    csv_file = get_latest_csv()
    
    if csv_file:
        try:
            # 读取CSV
            df = pd.read_csv(csv_file, encoding='utf-8') 
            
            print("✨ 正在生成新版交互式网页...")
            html = generate_html(df)
            
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write(html)
                
            print(f"✅ 成功！文件已保存至: {OUTPUT_FILE}")
            print("👉 接下来请运行 upload.py 进行上传")
            
        except Exception as e:
            print(f"❌ 处理出错: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️ 任务终止：未找到数据源")
