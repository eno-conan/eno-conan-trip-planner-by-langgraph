import os
from googleapiclient.discovery import build    
from llama_index.readers.web import SimpleWebPageReader
from llama_index.llms.openai import OpenAI
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
) 
from llama_index.core import Settings
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')

class SearchRecommendHotelsAgent:
    def __init__(self):
        pass
    
    def get_detail_from_webpage_by_rag(self,url,query):
        '''URLに対する検索'''
        documents = SimpleWebPageReader(html_to_text=True).load_data([url])
        
        # storage_contextのフォルダ名
        url_without_https = url.replace("https://", "")
        url_modified = url_without_https.replace("/", "_").replace(".","-")
            
        MODEL = "gpt-4o-mini-2024-07-18"
        # MODEL = "gpt-4-turbo-2024-04-09" # $0.02/call
        Settings.llm = OpenAI(model=MODEL)
        # VectorStoreIndex==============================
        try:
            storage_context = StorageContext.from_defaults(
                persist_dir=f'./storage_context/{url_modified}')
            index = VectorStoreIndex.from_documents(documents,
                                                    storage_context=storage_context
                                                    )
        except:
            index = VectorStoreIndex.from_documents(documents,
                                                    show_progress=True,
                                                    )
            index.storage_context.persist(persist_dir=f'./storage_context/{url_modified}')

        query_engine = index.as_query_engine()
        response = query_engine.query(query)
        print(str(response.response))
        return str(response.response)

    def get_recommened_hotels_link(self, place):
        '''
        Googleでいくつか検索
        '''
        KEYWORD = f'{place}  ホテル　安い'

        # Google Customサーチ結果を取得
        s = build('customsearch','v1',
                developerKey = os.getenv('GOOGLE_API_KEY'))

        results = []
        for i in range(2):
            try:
                r = s.cse().list(q = KEYWORD,
                                cx = os.getenv('CUSTOM_SEARCH_ENGINE_ID'),
                                lr = 'lang_ja',
                                num = 3,
                                start = 3).execute()
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

    def run(self, trip: dict):
        results = self.get_recommened_hotels_link(place=trip["place"])
        # 観光スポットの情報を次のnodeへ
        trip['recommended_hotels'] = results
        print(f'おすすめホテルの情報取得完了')
        return trip