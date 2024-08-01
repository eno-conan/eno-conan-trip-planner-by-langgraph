from tavily import TavilyClient
from typing import List
import urllib.parse
from llama_index.core import VectorStoreIndex
from llama_index.readers.web import SimpleWebPageReader
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

class ReSearchSpotInvalidImageAgent:
    def __init__(self):
        pass

    def re_search_spot_invalid_image(self, invalid_image_spots,spots_detail):
        temp_spots_detail = spots_detail
        # 画像差し換え
        for re_search_spot in invalid_image_spots:
            print(f'「{spot}」の情報再収集')
            spot_query = f'観光地：{re_search_spot}に関連するWebサイト情報をください。'
            for i in range(2): # 最大2回
                try:
                    results = tavily_client.search(
                        query=spot_query, \
                        max_results=2, \
                        include_answer=True, \
                        include_raw_content=False, \
                        include_images=True)
                    break
                except:
                    if i == 1:
                        raise Exception()
            sources = results['results']
            third_score_item = min(sources, key=lambda x: x['score'])
            if not third_score_item.get('url') is None or third_score_item.get('url') == '':
                if len(results['images'][0]) >= 2:
                    image = results['images'][1]
                else:
                    image = results['images'][0]
            else:
                print('Tavilyから情報再取得失敗')
            
            # スポット情報の更新
            for spot in temp_spots_detail:
                for key in spot.keys():
                    spot_name = key
                    try:
                        if temp_spots_detail[spot_name]['name'] == re_search_spot:
                            temp_spots_detail[spot]['image'] = image
                            break
                    except:
                        print(f'{re_search_spot}の画像情報の再設定ができませんでした。。。')
                        raise Exception()
        return temp_spots_detail
        

    def run(self, trip: dict):
        spots_detail = self.re_search_spot_invalid_image(
            trip['invalid_image_spots'],
            trip['spots_detail']
            )
        trip['spots_detail'] = spots_detail
        print(f'各スポットの再検索完了')
        return trip
