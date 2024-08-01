import requests
import traceback
import glob
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')
# from typing import List


class DownloadWebImagesAgent:
    '''URLから画像ダウンロード
    https://python-codes.net/entry/python-get-image-from-url
    '''
    def __init__(self):
        pass
    
    def delete_files_in_folder(self,folder_path='images'):
        '''画像ファイル削除'''
        files = glob.glob(os.path.join(folder_path, '*'))
        
        # 各ファイルを削除
        for file in files:
            try:
                os.remove(file)
            except Exception as e:
                print(f"{file} の削除中にエラーが発生: {e}")    

    def download_web_image(self, spots_detail):
        images_path = []
        if not os.path.exists('images'):
            os.makedirs('images')

        # https://tabichannel.com/article/1099/kofu
        for spot in spots_detail:
            for key_spot_name in spot.keys():
                image_url = spot[key_spot_name]['image']

                # 画像を取得
                for i in range(2):
                    try:
                        response = requests.get(image_url)
                        if '.png' in image_url:
                        # 画像をファイルに保存
                            file_name = f'images/{key_spot_name}.png'
                        else:
                            file_name = f'images/{key_spot_name}.jpg'
                        with open(f'{file_name}', 'wb') as f:
                            f.write(response.content)
                        images_path.append(file_name)
                        break
                    except Exception as e:
                        traceback.print_exc()
                    if i == 1:
                        # 2回失敗した場合
                        self.delete_files_in_folder()
                        raise Exception()
                        
        return images_path

    def run(self, trip: dict):
        images_path = self.download_web_image(spots_detail=trip['spots_detail'])
        trip['images_path'] = images_path
        print('画像ダウンロード完了')
        return trip
