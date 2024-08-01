import os
from googleapiclient.discovery import build    
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')

class SearchWeatherAgent:
    def __init__(self):
        pass
    
    def search_weather(self, place):
        '''
        Googleで天気・気温情報取得
        '''
        KEYWORD = f'2023年7月 気温 {place}'

        s = build('customsearch','v1',
                developerKey = os.getenv('GOOGLE_API_KEY'))
        results = []
        for i in range(2):
            try:
                r = s.cse().list(q = KEYWORD,
                                cx = os.getenv('CUSTOM_SEARCH_ENGINE_ID'),
                                lr = 'lang_ja',
                                num = 2,
                                start = 1).execute()
                for item in r['items']:
                    result = {}
                    result['title'] = item['title']
                    result['formattedUrl'] = item['formattedUrl']
                    results.append(result)  
                break
            except:
                if i == 1:
                    raise Exception()
        return results
        
        # # 取得結果に対する質問
        # from openai import OpenAI
        # client = OpenAI()
        # results_str = ', '.join(results)
        # question = 'textに含まれる空港名を1つ教えて'
        # res = client.chat.completions.create(
        #     model="gpt-3.5-turbo-0125",
        #     # model="gpt-4-turbo-2024-04-09",
        #     messages=[
        #         {"role": "system", "content": "You are a helpful assistant."},
        #         {"role": "user", "content": f"Text: {results_str}"},
        #         {"role": "user", "content": f"Question: {question}"}
        #     ],
        #     temperature=1
        # )
        # print(res.choices[0].message.content)
 

    def run(self, trip: dict):
        results = self.search_weather(place=trip["place"])
        # 観光スポットの情報を次のnodeへ
        trip['weather_info_links'] = results
        print(f'天気の情報取得')
        return trip