import csv
import os
import glob
from datetime import datetime

# ================= 配置区域 =================
# 局域网共享文件夹路径（请确保你的电脑有读取权限）
CSV_DIR = r'\\10.155.154.102\晚霞预报'
# 本地生成网页的保存路径（请修改为你实际的本地文件夹路径）
OUTPUT_DIR = r'C:\Users\Administrator\Desktop\sunset-web'
# ===========================================

def get_today_csv():
    """自动获取局域网中当天最新的CSV文件"""
    today_str = datetime.now().strftime('%Y%m%d')
    csv_pattern = os.path.join(CSV_DIR, f'{today_str}.csv')
    csv_files = glob.glob(csv_pattern)

    if not csv_files:
        print(f"❌ 未找到今天的CSV文件: {csv_pattern}")
        return None

    # 取修改时间最新的文件
    csv_file = max(csv_files, key=os.path.getmtime)
    print(f"✅ 正在读取文件: {os.path.basename(csv_file)}")
    return csv_file

def read_csv_data(csv_file):
    """读取CSV数据"""
    data_rows = []
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data_rows.append(row)
        print(f"✅ 成功读取 {len(data_rows)} 条数据")
        return data_rows
    except Exception as e:
        print(f"❌ 读取CSV失败: {e}")
        return None

def generate_html(data_rows):
    """生成HTML网页内容"""
    table_body = ""
    for row in data_rows:
        table_body += f"""
        <tr>
            <td>{row.get('观赏点', '')}</td>
            <td><span class="badge">{row.get('晚霞等级', '')}</span></td>
            <td>{row.get('出现概率', '')}</td>
            <td>{row.get('预计开始时间', '')} - {row.get('预计结束时间', '')}</td>
        </tr>
        """

    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>晚霞观赏预报</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: linear-gradient(to bottom, #ff9a9e, #fad0c4); min-height: 100vh; padding: 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; background: rgba(255,255,255,0.9); border-radius: 12px; padding: 30px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); }}
        h1 {{ text-align: center; color: #d35400; margin-bottom: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background-color: #f8f9fa; color: #555; font-weight: 600; }}
        tr:hover {{ background-color: #fff5f5; }}
        .badge {{ background: #ff7675; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.9em; }}
        .footer {{ text-align: center; margin-top: 30px; color: #888; font-size: 0.8em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌅 晚霞观赏预报</h1>
        <table>
            <thead>
                <tr>
                    <th>观赏点</th>
                    <th>晚霞等级</th>
                    <th>出现概率</th>
                    <th>预计时间</th>
                </tr>
            </thead>
            <tbody>
                {table_body}
            </tbody>
        </table>
        <div class="footer">数据来源: 局域网自动读取 | 自动生成网页</div>
    </div>
</body>
</html>
"""
    return html_content

def main():
    # 1. 获取当天CSV文件
    csv_file = get_today_csv()
    if not csv_file:
        return

    # 2. 读取数据
    data_rows = read_csv_data(csv_file)
    if not data_rows:
        return

    # 3. 生成HTML
    html_content = generate_html(data_rows)

    # 4. 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 5. 保存为index.html
    output_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ 网页生成成功！")
    print(f"📂 文件位置: {output_path}")
    print("💡 提示: 接下来请运行 auto_push.bat 推送更新")

if __name__ == '__main__':
    main()
