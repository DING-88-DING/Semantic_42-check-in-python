import requests
from web3 import Web3
from openpyxl import load_workbook
import logging

# --- 配置日志记录 ---
# 设置日志格式，包含时间、日志级别和消息
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 全局配置 ---
# API的URL地址
API_URL = "https://copium-api.semanticlayer.io/claimdailyxp"

# 从浏览器复制的HTTP请求头
HEADERS = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": "https://42.semanticlayer.io",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://42.semanticlayer.io/",
    "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
}

# Excel文件名
EXCEL_FILE = "wallets.xlsx"

def claim_xp(private_key: str, privy_token: str, proxy_ip: str = None):
    """
    为单个钱包地址请求XP。

    参数:
    - private_key (str): 钱包的私钥.
    - privy_token (str): 用于身份验证的Privy令牌.
    - proxy_ip (str, optional): 代理IP和端口 (例如 '127.0.0.1:7890'). 默认为None.
    """
    try:
        # 1. 从私钥派生钱包地址
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        account = Web3().eth.account.from_key(private_key)
        address = account.address
        logging.info(f"成功从私钥派生地址: {address}")

    except Exception as e:
        logging.error(f"无效的私钥: {private_key[:10]}... - 错误: {e}")
        return

    # 2. 设置代理 (如果提供)
    proxies = None
    if proxy_ip:
        proxies = {
            "http": f"http://{proxy_ip}",
            "https": f"http://{proxy_ip}",
        }
        logging.info(f"地址 {address} 使用代理: {proxy_ip}")
    else:
        logging.info(f"地址 {address} 不使用代理")

    # 3. 构建请求体 (Payload)
    payload = {
        "data": {
            "address": address,
            "privyToken": privy_token
        }
    }

    try:
        # 4. 发送POST请求
        logging.info(f"正在为地址 {address} 请求XP...")
        response = requests.post(
            API_URL,
            headers=HEADERS,
            json=payload,
            proxies=proxies,
            timeout=30  # 设置30秒超时
        )

        # 5. 检查并记录结果
        if response.status_code == 200:
            logging.info(f"✅ 成功! 地址: {address} - 响应: {response.json()}")
        else:
            logging.error(
                f"❌ 失败! 地址: {address} - 状态码: {response.status_code} - 响应: {response.text}"
            )

    except requests.exceptions.ProxyError as e:
        logging.error(f"❌ 代理错误! 地址: {address} - 代理: {proxy_ip} - 错误: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ 请求异常! 地址: {address} - 错误: {e}")
    except Exception as e:
        logging.error(f"❌ 发生未知错误! 地址: {address} - 错误: {e}")


def main():
    """
    主函数，用于读取Excel文件并处理所有钱包。
    """
    try:
        # 加载Excel工作簿
        workbook = load_workbook(filename=EXCEL_FILE)
        sheet = workbook.active
    except FileNotFoundError:
        logging.error(f"错误: 未找到 '{EXCEL_FILE}' 文件。请确保该文件与脚本在同一目录下。")
        # 创建一个模板文件以供参考
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Wallets"
        ws.append(["PrivateKey", "ProxyIP", "PrivyToken"])
        # 模板1: 无密码代理
        ws.append(["0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "123.45.67.89:8080", "ey... (token for wallet 1)"])
        # 模板2: 有密码代理
        ws.append(["0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "my_user:my_password@198.76.54.32:8888", "ey... (token for wallet 2)"])
        wb.save(EXCEL_FILE)
        logging.info(f"已为您创建一个包含格式示例的模板文件 '{EXCEL_FILE}'，请填入您的数据后重新运行脚本。")
        return

    # 遍历Excel中的每一行 (跳过表头)
    for row in sheet.iter_rows(min_row=2, values_only=True):
        # 即使某些单元格为空，也安全地获取值
        private_key = row[0] if len(row) > 0 else None
        proxy_ip = row[1] if len(row) > 1 else None
        privy_token = row[2] if len(row) > 2 else None

        # 私钥和PrivyToken是必须的
        if not private_key or not privy_token:
            logging.warning(f"跳过缺少私钥或PrivyToken的数据行: {row}")
            continue

        # 执行请求。如果proxy_ip是None或空字符串，则不使用代理。
        claim_xp(str(private_key), str(privy_token), str(proxy_ip) if proxy_ip else None)
        logging.info("-" * 50) # 添加分隔符

if __name__ == "__main__":
    main()