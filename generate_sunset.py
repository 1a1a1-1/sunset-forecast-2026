import pandas as pd
import glob
import os
from datetime import datetime

# ================= 配置区 =================
# 1. 数据源路径
CSV_DIR = r"\\10.155.154.102\晚霞预报" 

# 2. 输出路径 (保持不变)
OUTPUT_DIR = r"C:\Users\Administrator\Desktop\sunset-web"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")

# 确保输出目录存在
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
    """将时间转换为 HH:MM 格式"""
    if not isinstance(time_str, str) or len(time_str) < 16:
        return time_str
    try:
        return time_str[11:16]
    except:
        return time_str

def format_date_display(date_str):
    """将日期转换为 '7月30日' 格式"""
    s = str(date_str).replace('-', '').replace('/', '')
    if len(s) == 8:
        month = int(s[4:6])
        day = int(s[6:8])
        return f"{month}月{day}日"
    return date_str

def generate_html(df):
    """生成包含背景图和增强排版的HTML"""
    
    # 1. 数据预处理
    df['观赏点'] = df['观赏点'].apply(clean_location_name)
    
    # 处理时间字段
    for col in ['日落时间', '预计开始时间', '预计结束时间']:
        if col in df.columns:
            df[col] = df[col].apply(format_time_only)
            
    # 格式化概率
    if '出现概率' in df.columns:
        df['出现概率'] = pd.to_numeric(df['出现概率'], errors='coerce').round(2)
    
    # 提取唯一的地点和日期
    locations = sorted(df['观赏点'].unique().tolist())
    dates_raw = sorted(df['预报日期'].unique().tolist())
    dates_display = [format_date_display(d) for d in dates_raw]
    
    # 将DataFrame转换为JSON
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
            --text-main: #333333;
            --text-sub: #666666;
            --card-bg: rgba(255, 255, 255, 0.92); /* 卡片半透明白色 */
        }}
        
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            margin: 0; 
            padding: 0; 
            color: var(--text-main); 
            min-height: 100vh;
            /* 核心改动：背景图设置 */
            background: url('晚霞.jpg') no-repeat center center fixed;
            background-size: cover;
            -webkit-font-smoothing: antialiased;
        }}

        /* 顶部标题栏 - 半透明毛玻璃效果 */
        header {{ 
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(10px);
            padding: 20px 15px; 
            text-align: center; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        h1 {{ margin: 0; color: #d63031; font-size: 1.6rem; font-weight: 700; letter-spacing: 1px; }}
        
        /* 一级导航：地点滑动 */
        .location-scroller {{
            display: flex;
            overflow-x: auto;
            white-space: nowrap;
            padding: 15px;
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(10px);
            scrollbar-width: none;
        }}
        .location-scroller::-webkit-scrollbar {{ display: none; }}
        
        .loc-tab {{
            display: inline-block;
            padding: 10px 20px;
            margin-right: 12px;
            border-radius: 24px;
            background: rgba(240, 240, 240, 0.8);
            color: #666;
            font-size: 1.05rem;
            font-weight: 500;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        .loc-tab.active {{
            background: var(--primary-color);
            color: white;
            box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4);
            transform: scale(1.05);
        }}

        /* 二级导航：日期选择 */
        .date-selector {{
            display: flex;
            justify-content: center;
            gap: 15px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(10px);
            margin-bottom: 15px;
        }}
        .date-pill {{
            padding: 10px 24px;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.9);
            border: 2px solid transparent;
            color: var(--text-sub);
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .date-pill.active {{
            border-color: var(--primary-color);
            color: var(--primary-color);
            background: white;
        }}

        /* 内容展示区 */
        .content-area {{ 
            padding: 0 15px 40px; 
            max-width: 600px; 
            margin: 0 auto;
        }}
        
        /* 数据卡片 - 半透明毛玻璃 + 左右排版 */
        .forecast-card {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border-radius: 18px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
            border: 1px solid rgba(255,255,255,0.5);
        }}
        
        /* 全宽项 */
        .full-width {{
            margin-bottom: 18px;
            padding-bottom: 15px;
            border-bottom: 1px dashed #e0e0e0;
        }}

        /* 核心改动：标签在左，数值在右，并排显示 */
        .data-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            font-size: 1.15rem; /* 整体字号放大 */
        }}
        .data-row:last-child {{ margin-bottom: 0; }}
        
        .data-label {{
            color: #888;
            font-size: 1.05rem;
            font-weight: 500;
        }}
        
        .data-value {{
            font-weight: 700;
            color: #333;
            font-size: 1.2rem; /* 数值字号进一步放大 */
        }}
        
        .highlight-text {{ color: var(--primary-color); }}
        
        .level-badge {{ 
            display: inline-block; 
            padding: 6px 16px; 
            border-radius: 8px; 
            color: white; 
            font-size: 1.1rem; 
            font-weight: bold;
        }}
        .level-1 {{ background-color: #2ecc71; }} 
        .level-2 {{ background-color: #f1c40f; color: #333; }} 
        .level-3 {{ background-color: #e67e22; }} 
        .level-4 {{ background-color: #e74c3c; }} 
        .level-5 {{ background-color: #8e44ad; }}

        .empty-tip {{ 
            text-align: center; 
            padding: 60px 20px; 
            color: #666; 
            font-size: 1.1rem; 
            background: rgba(255,255,255,0.9);
            border-radius: 16px;
            backdrop-filter: blur(10px);
        }}
    </style>
</head>
<body>

<header>
    <h1>🌅 东方市晚霞预报</h1>
</header>

<div class="location-scroller" id="locContainer"></div>

<div class="date-selector" id="dateContainer"></div>

<div id="resultArea" class="content-area"></div>

<script>
    const rawData = {data_json};
    const locations = {locations};
    const datesRaw = {dates_raw};
    const datesDisplay = {dates_display};

    const locContainer = document.getElementById('locContainer');
    const dateContainer = document.getElementById('dateContainer');
    const resultArea = document.getElementById('resultArea');

    let currentLoc = locations[0];
    let currentDate = datesRaw[0];

    function init() {{
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
        document.querySelectorAll('.loc-tab').forEach(t => t.classList.remove('active'));
        tabElement.classList.add('active');
        renderData();
    }}

    function renderDates() {{
        dateContainer.innerHTML = '';
        datesRaw.forEach((date, index) => {{
            const pill = document.createElement('div');
            pill.className = `date-pill ${{date === currentDate ? 'active' : ''}}`;
            pill.innerText = datesDisplay[index];
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
        const filtered = rawData.filter(item => 
            item['观赏点'] === currentLoc && String(item['预报日期']) === String(currentDate)
        );

        if (filtered.length === 0) {{
            resultArea.innerHTML = '<div class="empty-tip">该日期暂无预报数据</div>';
            return;
        }}

        let html = '';
        filtered.forEach(item => {{
            let levelClass = 'level-' + item['晚霞等级'];
            
            html += `
            <div class="forecast-card">
                <div class="data-row full-width">
                    <span class="data-label">晚霞描述</span>
                    <span class="data-value">${{item['晚霞描述'] || '暂无描述'}}</span>
                </div>

                <div class="data-row">
                    <span class="data-label">晚霞等级</span>
                    <span class="level-badge ${{levelClass}}">${{item['晚霞等级']}} 级</span>
                </div>

                <div class="data-row">
                    <span class="data-label">出现概率</span>
                    <span class="data-value highlight-text">${{item['出现概率']}}%</span>
                </div>

                <div class="data-row">
                    <span class="data-label">日落时间</span>
                    <span class="data-value">${{item['日落时间'] || '--:--'}}</span>
                </div>

                <div class="data-row">
                    <span class="data-label">预计开始</span>
                    <span class="data-value">${{item['预计开始时间'] || '--:--'}}</span>
                </div>

                <div class="data-row">
                    <span class="data-label">预计结束</span>
                    <span class="data-value">${{item['预计结束时间'] || '--:--'}}</span>
                </div>
            </div>`;
        }});

        resultArea.innerHTML = html;
    }}

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
            df = pd.read_csv(csv_file, encoding='utf-8') 
            
            print("✨ 正在生成视觉增强版网页...")
            html = generate_html(df)
            
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write(html)
                
            print(f"✅ 成功！文件已保存至: {OUTPUT_FILE}")
            
        except Exception as e:
            print(f"❌ 处理出错: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️ 任务终止：未找到数据源")
