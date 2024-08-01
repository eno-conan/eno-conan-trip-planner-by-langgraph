import traceback
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')
from PIL import Image
import os    
# from typing import List


class VerifyDownloadImagesAgent:
    '''URLから画像ダウンロード
    https://python-codes.net/entry/python-get-image-from-url
    '''
    def __init__(self):
        pass

    def verify_images(self):
        # imagesフォルダのファイル名取得
        files = os.listdir('images')
        invalid_image_spots = []
        for file in files:
            file_path = f'images/{file}' 
            # ファイル存在判定
            if not os.path.exists(file_path):
                print(f"{file}がありません")

            # 画像ファイルを開いて確認
            try:
                with Image.open(file_path) as img:
                    img.verify()  # 画像ファイルが正常かを検証
            except (IOError, SyntaxError) as e:
                print(f"Error: {e}")
                # 後続処理へ渡す
                spot_name = file.split('.')[0]
                invalid_image_spots.append(spot_name)
                try:
                    os.remove(file_path)
                    print(f"「{file}」を削除")
                except OSError as delete_error:
                    print(f"Error: {delete_error}")                
        return invalid_image_spots

    def run(self, trip: dict):
        invalid_image_spots = self.verify_images()
        trip['invalid_image_spots'] = invalid_image_spots
        print('画像の検証完了')
        return trip
