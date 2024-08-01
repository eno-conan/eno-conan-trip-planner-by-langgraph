# https://zenn.dev/yamagishihrd/articles/2022-09_01-google-spreadsheet-with-python#fn-d711-5
# oauth2client [4] は現在非推奨になっており、今後は google-auth [5] の利用が推奨されています。
# https://google-auth.readthedocs.io/en/master/user-guide.html
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')


class UploadPdfAgent:
    def __init__(self):
        pass

    # 特定のメールアドレスにアクセス権を付与する関数
    def set_file_access(self,service, file_id, email):
        permissions = {
            'type': 'user',
            'role': 'reader',
            'emailAddress': email
        }
        for i in range(2):
            try:
                service.permissions().create(fileId=file_id, 
                                            body=permissions, 
                                            ).execute()
                permissions = service.permissions().list(fileId=file_id).execute()  
                break
            except:
                if i == 1:
                    raise Exception()

    def upload_pdf(self,file_name):
        scope = ['https://www.googleapis.com/auth/drive']

        credentials = service_account.Credentials.from_service_account_file('trip-pdf-sa.json')
        scoped_credentials = credentials.with_scopes(scope)

        service = build('drive', 'v3', credentials=scoped_credentials)
        # アップロードするファイルのパス
        file_path = file_name
        # ファイルメタデータを定義
        file_metadata = {
            'name': os.path.basename(file_path),
        }

        # ファイルをアップロード
        media = MediaFileUpload(file_path, mimetype='application/pdf')
        for i in range(2):
            try:
                file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                fileId = file.get('id')
                break
            except:
                if i == 1:
                    raise Exception()
        file_url = f'https://drive.google.com/file/d/{fileId}/view'
        
        # 特定のメールアドレスを設定
        self.set_file_access(service, fileId, os.getenv('GMAIL_ADDRESS'))    
        return file_url
    
    def delete_create_pdf(self,target_pdf):
        if os.path.exists(target_pdf):
            print(f'ローカルの作成ファイル削除完了')
            os.remove(target_pdf)
        else:
            print(f'{target_pdf} が見つかりません。')      


    def run(self, trip: dict):
        target_pdf = trip['pdf_filename']
        file_url = self.upload_pdf(file_name=target_pdf)
        print(f'Google Driveへのアップロード完了')
        trip['pdf_google_drive_url'] = file_url
        if not file_url == '':
            print(file_url)
            self.delete_create_pdf(target_pdf)   
        return trip
