from tavily import TavilyClient
import traceback
import os
import concurrent.futures
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

class Spot:
    def __init__(self, name:str,url: str, image: list,
                 ):
        self.name = name
        self.url = url
        self.image = image

    def to_dict(self):
        return {
            "name": self.name,
            "url": self.url,
            "image": self.image,
        }

class SearchEachSpotDetailAgent:
    def __init__(self):
        pass

    def retrieve_spots_details(self, spot):
        spot_name = spot

        print(f'「{spot_name}」の情報収集')
        spot_query = f'観光地：{spot_name}に関連するWebサイト情報をください。'
        for i in range(2):
            try:
                results = tavily_client.search(query=spot_query, 
                                            max_results=1, 
                                            include_answer=True, 
                                            include_raw_content=False, 
                                            include_images=True)
                break
            except:
                if i == 1:
                    raise Exception()

        source = results['results'][0]
        if not source.get('url') is None or source.get('url') == '':
            spot_url = source['url']
            image = results['images'][:3]
        else:
            print('情報が取得できませんでした')
            spot_url = ''
            image = []
        
        place_obj = Spot(spot_name, spot_url, image)
        spot_dict = place_obj.to_dict()

        return spot_dict

    def run(self, trip: dict):
        spots = trip['spots']
        # spots = ['兼六園', '金沢21世紀美術館', # '千里浜なぎさドライブウェイ', '白山白川郷ホワイトロード', '能登島水族館', '石川県立美術館','ひがし茶屋街','輪島朝市'
        # ]
        # スポットごとの情報を格納
        update_spots_detail = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_spot = {executor.submit(self.retrieve_spots_details, spot): 
                spot for spot in spots}
            for future in concurrent.futures.as_completed(future_to_spot):
                spot = future_to_spot[future]
                try:
                    result = future.result()
                    update_spots_detail.append({spot:result})
                except Exception as exc:
                    traceback.print_exc()
        trip['spots_detail'] = update_spots_detail
        print(f'各スポットの詳細情報取得完了')
        return trip

if __name__ == "__main__": 
    # cd aws-stack/server/app/backend/agents/
    aa = SearchEachSpotDetailAgent()
    aa.run(trip={})