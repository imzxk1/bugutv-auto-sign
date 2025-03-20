#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import random
import requests
import smtplib
import traceback
import json
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
load_dotenv()

# 配置日志
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOG_DIR, f"autosign_{datetime.now().strftime('%Y%m%d')}.log"))
    ]
)
logger = logging.getLogger('bugutv_autosign')

# 用户配置
USERNAME = os.getenv('BUGUTV_USERNAME', '')
PASSWORD = os.getenv('BUGUTV_PASSWORD', '')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = os.getenv('EMAIL_PORT', '')
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
EMAIL_TO = os.getenv('EMAIL_TO', '')

# 网站URL
BASE_URL = "https://www.bugutv.vip"
LOGIN_URL = f"{BASE_URL}/wp-admin/admin-ajax.php"  # WordPress标准的AJAX处理URL
USER_URL = f"{BASE_URL}/user"
CHECK_IN_URL = f"{BASE_URL}/wp-admin/admin-ajax.php"  # WordPress标准的AJAX处理URL

class BuguTVAutoSign:
    def __init__(self, username, password, debug=False):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': BASE_URL,
            'Origin': BASE_URL
        }
        self.session.headers.update(self.headers)
        self.debug = debug
        self.max_retries = 3
        self.current_retry = 0
        self.is_logged_in = False
        self.log_dir = LOG_DIR
        self.nonce = None  # 用于签到的nonce参数

    def save_debug_info(self, filename, content):
        """保存调试信息到文件"""
        if not self.debug:
            return
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_path = os.path.join(self.log_dir, f"{filename}_{timestamp}.html")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"保存页面内容到: {file_path}")

    def login(self):
        """登录布谷TV网站"""
        try:
            logger.info(f"开始登录过程 - 用户名: {self.username}")
            
            # 首先获取首页，获取cookies和一些必要的参数
            logger.info("请求网站首页")
            response = self.session.get(BASE_URL)
            logger.info(f"首页状态码: {response.status_code}")
            self.save_debug_info("index", response.text)
            
            # 查看获取到的cookies
            logger.info(f"获取到cookie: {self.session.cookies.get_dict()}")
            
            # 请求登录页面
            logger.info("请求登录页面")
            login_page_response = self.session.get(USER_URL)
            logger.info(f"登录页面状态码: {login_page_response.status_code}")
            self.save_debug_info("login_page", login_page_response.text)
            
            # 尝试通过WordPress标准的AJAX方式登录
            logger.info("执行登录请求")
            login_data = {
                'action': 'user_login',  # WordPress登录操作的标准名称
                'username': self.username,
                'password': self.password,
                'rememberme': '1'
            }
            
            login_response = self.session.post(LOGIN_URL, data=login_data)
            logger.info(f"登录响应状态码: {login_response.status_code}")
            logger.info(f"登录响应头: {login_response.headers}")
            logger.info(f"登录响应文本: {login_response.text}")
            self.save_debug_info("login_response", login_response.text)
            
            # 尝试检查我们是否已登录 - 访问用户中心页面
            logger.info("请求用户中心页面确认登录状态")
            user_response = self.session.get(USER_URL)
            self.save_debug_info("user_page", user_response.text)
            
            # 登录成功的标志通常是页面中包含用户名或一些个人信息
            # 这里我们简单地检查页面内容来确定是否登录成功
            if self.username.lower() in user_response.text.lower() or "退出" in user_response.text or "签到" in user_response.text:
                logger.info("登录成功!")
                self.is_logged_in = True
                
                # 从用户页面中提取nonce值
                nonce_match = re.search(r'go-user-qiandao[^>]*data-nonce="([^"]+)"', user_response.text)
                if nonce_match:
                    self.nonce = nonce_match.group(1)
                    logger.info(f"成功获取签到nonce: {self.nonce}")
                else:
                    logger.warning("未找到签到nonce值，签到可能会失败")
                
                return True
            else:
                logger.warning("无法确认登录状态，可能登录失败")
                return False
                
        except Exception as e:
            logger.error(f"登录过程中发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def check_in(self):
        """执行网站签到"""
        try:
            if not self.is_logged_in:
                logger.warning("未登录，无法执行签到")
                return False
                
            if not self.nonce:
                logger.warning("缺少签到所需的nonce参数，无法签到")
                return False
                
            logger.info("开始执行签到")
            
            # 准备签到请求头
            check_in_headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Referer': USER_URL
            }
            
            # 使用正确的签到参数
            check_in_data = {
                'action': 'user_qiandao',  # 从JS代码中获取的实际action名称
                'nonce': self.nonce       # 从页面中提取的nonce值
            }
            
            response = self.session.post(
                CHECK_IN_URL, 
                data=check_in_data,
                headers=check_in_headers
            )
            
            logger.info(f"签到响应状态码: {response.status_code}")
            logger.info(f"签到响应文本: {response.text}")
            self.save_debug_info("checkin_response", response.text)
            
            # 最简单的字符串匹配方式
            if "\u4eca\u65e5\u5df2\u7b7e\u5230" in response.text:
                logger.info("今日已签到，请明日再来")
                return True
                
            if "\u7b7e\u5230\u6210\u529f" in response.text:
                logger.info("签到成功！")
                return True
                
            # 尝试去除可能的BOM标记后解析JSON
            try:
                # 处理可能存在的BOM标记
                response_text = response.text
                if response_text.startswith('\ufeff'):
                    response_text = response_text[1:]
                
                data = json.loads(response_text, strict=False)
                status = data.get('status')
                msg = data.get('msg', '')
                
                if status == "1" or status == 1:
                    logger.info(f"签到成功! 消息: {msg}")
                    return True
                
                # 检查特定消息
                if status == "0":
                    # 尝试把Unicode编码的消息解码成中文
                    try:
                        decoded_msg = bytes(msg, 'utf-8').decode('unicode_escape')
                        logger.info(f"消息解码: {decoded_msg}")
                        if '今日已' in decoded_msg or '已签到' in decoded_msg or '今天已' in decoded_msg:
                            logger.info("今日已签到，请明日再来")
                            return True
                    except:
                        pass
                    
                    # 如果上面的方法不起作用，再尝试直接匹配
                    if '今日已签到' in msg or '已签到' in msg or msg == "\u4eca\u65e5\u5df2\u7b7e\u5230\uff0c\u8bf7\u660e\u65e5\u518d\u6765":
                        logger.info("今日已签到，请明日再来")
                        return True
                
                logger.warning(f"无法识别的签到响应: {msg}")
                return False
                
            except Exception as e:
                logger.warning(f"无法解析响应: {str(e)} - {response.text}")
                # 最后一次尝试，直接匹配字符串
                if '今日已' in response.text or '已签到' in response.text:
                    logger.info("通过直接文本匹配发现今日已签到")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"签到过程中发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def send_notification(self, success, message):
        """发送邮件通知"""
        if not all([EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_TO]):
            logger.info("未配置邮件通知，跳过发送")
            return
            
        try:
            from email.mime.text import MIMEText
            from email.header import Header
            
            subject = f"布谷TV自动签到{'成功' if success else '失败'}"
            msg = MIMEText(message, 'plain', 'utf-8')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = EMAIL_USERNAME
            msg['To'] = EMAIL_TO
            
            server = smtplib.SMTP_SSL(EMAIL_HOST, int(EMAIL_PORT))
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USERNAME, EMAIL_TO, msg.as_string())
            server.quit()
            
            logger.info("邮件通知发送成功")
        except Exception as e:
            logger.error(f"发送邮件通知失败: {str(e)}")

    def run(self):
        """运行自动签到流程"""
        success = False
        message = ""
        
        # 尝试登录并签到，最多重试设定的次数
        while self.current_retry < self.max_retries and not success:
            if self.current_retry > 0:
                logger.info(f"第 {self.current_retry} 次重试...")
                time.sleep(5 * self.current_retry)  # 重试延迟，随重试次数增加
                
            login_success = self.login()
            if login_success:
                check_in_success = self.check_in()
                
                # 直接使用检查签到的返回值作为成功标志
                if check_in_success:
                    success = True
                    message = "自动签到成功 (或今日已签到)!"
                    logger.info(message)
                else:
                    message = "登录成功但签到失败"
                    logger.warning(message)
            else:
                message = "登录失败"
                logger.warning(message)
                
            self.current_retry += 1
            
        if not success:
            message = f"自动签到失败，已重试 {self.max_retries} 次"
            logger.error(message)
            
        # 发送通知
        self.send_notification(success, message)
        
        return success

def main():
    """主函数"""
    # 检查环境变量配置
    if not USERNAME or not PASSWORD:
        logger.error("未配置用户名或密码，请在.env文件中设置BUGUTV_USERNAME和BUGUTV_PASSWORD")
        sys.exit(1)
        
    # 创建签到对象并运行
    auto_sign = BuguTVAutoSign(USERNAME, PASSWORD, debug=True)
    success = auto_sign.run()
    
    # 返回状态码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 