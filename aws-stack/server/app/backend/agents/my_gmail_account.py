import os
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')

class MyGmailAccount:
    #ご自身のgmailアドレス
    account = os.getenv('GMAIL_ADDRESS')
    #アプリパスワード（16桁）
    password = os.getenv('GMAIL_APP_PASSWORD')