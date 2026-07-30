import pandas as pd
import glob
import os
from datetime import datetime

# ================= 配置区 =================
# 1. 数据源路径 (保持不变)
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

def format_time_only(time_val):
    """将时间格式化为 HH:MM，如果为空则返回 '--'"""
    if pd.isna(time_val) or time_val == '':
        return "--"
    try:
        time_str = str(time_val).strip()
        # 尝试多种常见格式
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%H:%M:%S", "%H:%M"]:
            try:
                return datetime.strptime(time_str, fmt).strftime("%H:%M")
            except ValueError:
                continue
        return time_str[:5] # 兜底截取
    except:
        return str(time_val)

def format_date_display(date_str):
    """将日期转换为 '7月30日' 格式"""
    s = str(date_str).replace('-', '').replace('/', '')
    if len(s) == 8:
        month = int(s[4:6])
        day = int(s[6:8])
        return f"{month}月{day}日"
    return date_str

def generate_html(df):
    """生成包含背景图和并排布局的HTML"""
    
    # 1. 数据预处理 (严格使用原始列名)
    # 清洗观赏点名称
    df['观赏点'] = df['观赏点'].apply(clean_location_name)
    
    # 格式化时间字段 (日落时间 + 预计开始/结束时间)
    if '日落时间' in df.columns:
        df['日落时间'] = df['日落时间'].apply(format_time_only)
    if '预计开始时间' in df.columns:
        df['预计开始时间'] = df['预计开始时间'].apply(format_time_only)
    if '预计结束时间' in df.columns:
        df['预计结束时间'] = df['预计结束时间'].apply(format_time_only)
        
    # 格式化概率 (保留两位小数)
    if '出现概率' in df.columns:
        df['出现概率'] = pd.to_numeric(df['出现概率'], errors='coerce').round(2)
    
    # 提取地点和日期
    all_locations = sorted(df['观赏点'].unique().tolist())
    if '鱼鳞洲' in all_locations:
        all_locations.remove('鱼鳞洲')
        locations = ['鱼鳞洲'] + all_locations
    else:
        locations = all_locations
    dates_raw = sorted(df['预报日期'].unique().tolist())
    dates_display = [format_date_display(d) for d in dates_raw]
    
    # 将DataFrame转换为JSON供前端使用
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
            --card-bg: rgba(255, 255, 255, 0.92);
        }}
        
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            margin: 0; 
            padding: 0; 
            color: var(--text-main); 
            min-height: 100vh;
            /* 背景图设置：晚霞.jpg 必须与 index.html 同目录 */
            background: url('晚霞.jpg') no-repeat center center fixed;
            background-size: cover;
            -webkit-font-smoothing: antialiased;
        }}

        /* 顶部标题栏 - 半透明毛玻璃 */
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
        
        /* 一级导航：地点横向滑动 */
        .location-scroller {{
            display: flex;
            overflow-x: auto;
            white-space: nowrap;
            padding: 15px;
            background: rgba(255, 255, 255, 0.80);
            backdrop-filter: blur(10px);
            scrollbar-width: none;
        }}
        .location-scroller::-webkit-scrollbar {{ display: none; }}
        
        .loc-tab {{
            display: inline-block;
            padding: 10px 20px;
            margin-right: 12px;
            border-radius: 24px;
            background: rgba(240, 240, 240, 0.85);
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
            background: rgba(255, 255, 255, 0.70);
            backdrop-filter: blur(10px);
            margin-bottom: 15px;
        }}
        
        .date-pill {{
            padding: 8px 18px;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.85);
            border: 2px solid transparent;
            color: var(--text-sub);
            font-size: 0.95rem; /* 从1.1rem调小到0.95rem */
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap; /* 强制不换行 */
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
        
        /* 数据卡片 - 半透明毛玻璃 + 并排布局 */
        .forecast-card {{
            background: rgba(255, 255, 255, 0.55);
            backdrop-filter: blur(12px);
            border-radius: 18px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
            border: 1px solid rgba(255,255,255,0.5);
        }}
        
        /* 全宽项 (晚霞描述) */
        .full-width {{
            margin-bottom: 18px;
            padding-bottom: 15px;
            border-bottom: 1px dashed #e0e0e0;
        }}

        /* 核心：标签在左，数值在右，并排显示 */
        .data-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            font-size: 1.15rem;
        }}
        .data-row:last-child {{ margin-bottom: 0; }}
        
        .data-label {{
            color: #444;
            font-size: 1.05rem;
            font-weight: 500;
        }}
        
        .data-value {{
            font-weight: 700;
            color: #333;
            font-size: 1.2rem;
            text-shadow: 0 1px 2px rgba(255,255,255,0.8);
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

<!-- 一级导航：地点滑动 -->
<div class="location-scroller" id="locContainer"></div>

<!-- 二级导航：日期切换 -->
<div class="date-selector" id="dateContainer"></div>

<!-- 数据展示 -->
<div id="resultArea" class="content-area"></div>

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

    // 初始化地点导航
    function initLocations() {{
        locations.forEach(loc => {{
            const chip = document.createElement('div');
            chip.className = 'loc-tab';
            chip.innerText = loc;
            chip.onclick = () => switchLocation(loc, chip);
            if(loc === currentLoc) chip.classList.add('active');
            locContainer.appendChild(chip);
        }});
    }}

    // 切换地点
    function switchLocation(loc, element) {{
        currentLoc = loc;
        document.querySelectorAll('.loc-tab').forEach(el => el.classList.remove('active'));
        element.classList.add('active');
        render();
    }}

    // 初始化日期导航
    function initDates() {{
        datesRaw.forEach((date, index) => {{
            const btn = document.createElement('div');
            btn.className = 'date-pill';
            btn.innerText = datesDisplay[index];
            btn.onclick = () => switchDate(date, btn);
            if(date === currentDate) btn.classList.add('active');
            dateContainer.appendChild(btn);
        }});
    }}

    // 切换日期
    function switchDate(date, element) {{
        currentDate = date;
        document.querySelectorAll('.date-pill').forEach(el => el.classList.remove('active'));
        element.classList.add('active');
        render();
    }}

    // 渲染核心逻辑
    function render() {{
        const filtered = rawData.filter(item => 
            item['观赏点'] === currentLoc && String(item['预报日期']) === String(currentDate)
        );

        if (filtered.length === 0) {{
            resultArea.innerHTML = '<div class="empty-tip">该日期暂无预报数据</div>';
            return;
        }}

        let html = '';
        filtered.forEach(item => {{
            const level = item['晚霞等级'];
            const levelClass = `level-${{level}}`;
            
            html += `
            <div class="forecast-card">
                <div class="data-row full-width">
                    <span class="data-label">晚霞描述</span>
                    <span class="data-value">${{item['晚霞描述'] || '暂无描述'}}</span>
                </div>

                <div class="data-row">
                    <span class="data-label">晚霞等级</span>
                    <span class="level-badge ${{levelClass}}">${{level}} 级</span>
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

    // 启动
    initLocations();
    initDates();
    render();

</script>
</body>
</html>"""
    return html_content

if __name__ == "__main__":
    print("⏳ 正在读取最新数据...")
    csv_file = get_latest_csv()
    
    if csv_file:
        try:
            # 读取CSV，假设编码为utf-8，如果乱码可尝试 'gbk'
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
