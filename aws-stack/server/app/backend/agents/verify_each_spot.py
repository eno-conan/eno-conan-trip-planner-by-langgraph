import traceback
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')
from PIL import Image
import requests
import os
import urllib.parse
import traceback
from llama_index.core import VectorStoreIndex
from llama_index.readers.web import SimpleWebPageReader
import os
import googlemaps
from geopy.geocoders import Nominatim
import concurrent.futures
import time

gm = googlemaps.Client(key=os.getenv('GOOGLE_API_KEY'))


class VerifyEachSpotAgent:
    '''URLから画像ダウンロード
    https://python-codes.net/entry/python-get-image-from-url
    '''
    def __init__(self):
        pass
        
    def verify_image(self,spot):
        for image in spot['image']:
            try:
                # 画像を取得
                response = requests.get(image)
                if '.png' in image:
                # 画像をファイルに保存
                    file_name = f'images/{spot["name"]}.png'
                else:
                    file_name = f'images/{spot["name"]}.jpg'
                with open(f'{file_name}', 'wb') as f:
                    f.write(response.content)
                # 画像検証
                with Image.open(file_name) as img:
                    img.verify()
                # 画像パスを返す
                return file_name
            except Exception as e:
                traceback.print_exc()
        # どの画像も検証に失敗した場合
        return ''

            
    def verify_location(self,spot_name):
        # geolocator = Nominatim(user_agent="my_app")
        # location = geolocator.geocode(spot_name)
        # if location.latitude is None or \
        #     location.longitude is None:
        # ダメなら、GoogleMap API適用
        res = gm.geocode(spot_name)
        if len(res) > 0:
            location = res[0]['geometry']['location']
            return (location['lat'], location['lng'])
        else:
            return ''
        # else:
        #     return (location.latitude, location.longitude)       
        

    def get_spot_summary(self,spot):
        '''WEBのURLから内容取得
        https://docs.llamaindex.ai/en/v0.9.48/api/llama_index.readers.SimpleWebPageReader.html
        https://python.langchain.com/v0.1/docs/integrations/document_loaders/web_base/
        '''
        query_get_summary = f'{spot["name"]}とはどんな場所ですか？100文字以上200文字以内の日本語で説明をお願いします。'
        documents = SimpleWebPageReader(html_to_text=True).load_data([spot['url']])
                
        # # インデックスの作成
        index = VectorStoreIndex.from_documents(documents)    
        query_engine = index.as_query_engine(similarity_top_k=3)
        query_to_doc = query_engine.query(query_get_summary)
        if query_to_doc == 'Empty Response':
            query_to_doc = ''
        return str(query_to_doc)
    
    def get_googlemap_link(self,spot_name):
        BASE_URL = 'https://www.google.com/maps/search/'
        encoded_query = urllib.parse.quote(spot_name)
        googlemap_url = f'{BASE_URL}{encoded_query}'
        return googlemap_url
    

    def verify_each_spot(self,spots_detail):
        if not os.path.exists('images'):
            os.makedirs('images')
        spot_name = list(spots_detail.keys())[0]
        spot_info = spots_detail[spot_name]
        # 1. 画像検証
        image_path = self.verify_image(spot_info)
        # 2. 位置検証
        location = self.verify_location(spot_info['name'])
        # 3. サマリー取得検証
        summary = self.get_spot_summary(spot_info)
        # 4. GoogleマップのURL取得
        googlemap_url = self.get_googlemap_link(spot_info['name'])
        if location == '' or summary == '':
            return {spot_name:{}}
        else:
            return {spot_name:{
                    'name':spot_name,
                    'url':spot_info['url'],
                    'image_path':image_path,
                    'location':location,
                    'summary':summary,
                    'googlemap_url':googlemap_url,
                            }
                        }


    def run(self, trip: dict):
        spots_detail = trip['spots_detail']
        # 並列処理
        time.sleep(3)
        temp_spots_detail = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_spot = {executor.submit(self.verify_each_spot, spot): spot for spot in spots_detail}
            for future in concurrent.futures.as_completed(future_to_spot):
                try:
                    result = future.result()
                    temp_spots_detail.append(result)
                except Exception:
                    traceback.print_exc()
        
        update_spots_detail = []
        for spots_detail in temp_spots_detail:
            spot_name = list(spots_detail.keys())[0]
            if not spots_detail[spot_name] == {}:
                update_spots_detail.append(spots_detail)
                # 5カ所情報が集まればそこで終了
                # if len(update_spots_detail) == 5:
                #     break
        # trip['spots_detail'] = [{'金沢21世紀美術館': {'name': '金沢21世紀美術館', 'url': 'https://www.weekend-kanazawa.com/entry/21stcenturymuseumofcontemporaryartkanazawa', 'image': ['https://next.jorudan.co.jp/trv/images/640/20617.jpg', 'http://www.kanazawa-kankoukyoukai.or.jp/lsc/upfile/spot/0001/0066/10066_2_l.jpg', 'https://deco-roo.com/wp-content/uploads/2022/03/kanazawa21-01.jpg']}}, {'兼六園': {'name': '兼六園', 'url': 'https://kenrokuen.or.jp/', 'image': ['https://www.kanazawa-kankoukyoukai.or.jp/lsc/upfile/spot/0001/0106/10106_1_m.jpg', 'https://www.kanazawa-kankoukyoukai.or.jp/lsc/upfile/spot/0001/0106/10106_9_l.jpg', 'https://www.airtrip.jp/travel-column/wp-content/uploads/2017/09/ebf4cca69e8d1f5d742e5304d7ac4c23.jpg']}}, {'能登半島': {'name': '能登半島', 'url': 'https://notocho.jp/', 'image': ['https://blog-imgs-135-origin.fc2.com/f/l/y/flyinthesky2012/DSC_1095_01_2020092710154354b.jpg', 'https://www.jre-travel.com/content/dam/jretravel/site/page/article/images/00342/a00342_05_p.jpg', 'https://imgcp.aacdn.jp/img-a/800/auto/aa/gm/article/4/9/6/6/2/4/202303021619/map_noto.png']}}, {'ひがし茶屋街': {'name': 'ひがし茶屋街', 'url': 'https://www.kanazawa-kankoukyoukai.or.jp/higashi', 'image': ['https://s3-ap-northeast-1.amazonaws.com/thegate/2020/12/25/12/04/53/Higashi-Chaya-District.jpg', 'https://tabi-mag.jp/wp-content/uploads/IS029405.jpg', 'https://www.airtrip.jp/travel-column/wp-content/uploads/2017/09/79f7912c493af99bb829944e05fded56-1024x543.jpg']}}, {'和倉温泉': {'name': '和倉温泉', 'url': 'https://www.wakura.or.jp/', 'image': ['https://d340eiag32bpum.cloudfront.net/img/post/spot/731/73029-5AP0RQFLnK1M9mDffYgp_lrg_re.jpg', 'https://s3-ap-northeast-1.amazonaws.com/thegate/2021/01/19/15/38/42/Wakura-hotspring.jpg', 'https://sta.app.tabi-wester.westjr.co.jp/images/ticket/235d620dab0be7e6b977b2a6fcbbc0c8.jpg']}}]
        trip['spots_detail'] = update_spots_detail
        print('各スポットの検証完了')
        return trip

if __name__ == "__main__": 
    # cd aws-stack/server/app/backend/agents/
    aa = VerifyEachSpotAgent()
    aa.run(trip={})