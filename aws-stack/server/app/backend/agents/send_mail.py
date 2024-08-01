from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import smtplib, ssl
from email.mime.text import MIMEText
from .my_gmail_account import MyGmailAccount 
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')


class SendMailAgent:
    def __init__(self):
        pass

    def make_mime_text(self,mail_to, subject, body):
        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["To"] = mail_to
        msg["From"] = MyGmailAccount.account
        return msg
            

    def send(self,msg):
        server = smtplib.SMTP_SSL(
            "smtp.gmail.com", 465,
            context = ssl.create_default_context())
        server.set_debuglevel(0)
        server.login(MyGmailAccount.account, MyGmailAccount.password)
        server.send_message(msg)   

    def send_mail(self,pdf_google_drive_url):
        '''
        メール送信
        '''
        send_address = os.getenv('GMAIL_ADDRESS')
        msg =self. make_mime_text(
            mail_to = send_address,
            subject = "PDF作成完了",
            body = f"PDFが作成できました。\n{pdf_google_drive_url}"
        )
        self.send(msg)
        # scope = ['https://www.googleapis.com/auth/drive']

        # # Parsing JSON credentials for a service account:
        # # Parsing JSON credentials for a service account:
        # credentials = service_account.Credentials.from_service_account_file('trip-pdf-sa.json')
        # scoped_credentials = credentials.with_scopes(scope)

        # service = build('drive', 'v3', credentials=scoped_credentials)

        # # アップロードするファイルのパス
        # file_path = file_name
        # # ファイルメタデータを定義
        # file_metadata = {
        #     'name': os.path.basename(file_path),
        # }

        # # ファイルをアップロード
        # media = MediaFileUpload(file_path, mimetype='application/pdf')
        # file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        # fileId = file.get('id')

    def run(self, trip: dict):
        pdf_google_drive_url = trip['pdf_google_drive_url']
        # self.send_mail(pdf_google_drive_url=pdf_google_drive_url)
        # print(f'メール送信完了')
        print(f'メール送信完了（今はOFF状態）')
        return trip
