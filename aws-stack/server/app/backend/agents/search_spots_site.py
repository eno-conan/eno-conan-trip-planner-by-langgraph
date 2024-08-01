from tavily import TavilyClient
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


class SearchSpotsSiteAgent:
    def __init__(self):
        pass

    def search_tavily(self, query: str):
        #  https://docs.tavily.com/docs/tavily-api/python-sdk#usage-%EF%B8%8F
        # https://docs.tavily.com/docs/tavily-api/Topics/news
        results = tavily_client.search(query=query, 
                                       max_results=1,
                                    #    search_depth="advanced", \
                                       include_answer=True,
                                       include_raw_content=False,
                                       include_images=True
                                       )
        sources = results['results']
        # スコアが最も高いURLを抽出
        highest_score_item = max(sources, key=lambda x: x['score'])
        highest_score_url = highest_score_item['url']
        return highest_score_url

    def run(self, trip: dict):
        # highest_score_url = self.search_tavily(
        #     query=f'{trip["place"]}の観光名所を掲載しているWebサイトを教えて')
        # # スコアが最も高い情報のリンクを次へ
        # trip['spots_url'] = highest_score_url
        print(f'{trip["place"]}のWebサイト取得完了')
        return trip
