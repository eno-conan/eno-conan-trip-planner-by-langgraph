import os
import traceback
from llama_index.readers.web import SimpleWebPageReader
from llama_index.core import VectorStoreIndex,StorageContext, Settings
from typing import List,Dict
from llama_index.llms.openai import OpenAI
from openai import OpenAI
import googlemaps
from geopy.geocoders import Nominatim

from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')
client = OpenAI()
gm = googlemaps.Client(key=os.getenv('GOOGLE_API_KEY'))

class GetSpotsAgent:
    def __init__(self):
        pass

    def get_detail_from_webpage_by_rag(self, query: str,url=None):
        res = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful japan travel assistant."},
            {"role": "user", "content": f"{query}"}
        ],
        temperature=1
        )
        return str(res.choices[0].message.content)                        

    def run(self, trip: dict):
        # trip["place"] = "石川県"
        query_get_spots=f'''
        {trip["place"]}の観光スポットを日本語で6つ教えて
        ・スポット名以外の情報は不要
        ・出力形式：カンマ区切り
        ・「、」は、「,]に置換
        '''
        res = self.get_detail_from_webpage_by_rag(
            query=query_get_spots)
        retrieve_spots = res.split(',')
        formatted_spots = []
        for spot in retrieve_spots:
            trim_space_from_spot = spot.strip()
            formatted_spot_name = trim_space_from_spot.replace('・', ',').replace('\n','')
            formatted_spots.append(formatted_spot_name)

        print(formatted_spots)
        trip['spots'] = formatted_spots
                
        print(f'スポット名の取得・緯度経度の検証取得完了')
        return trip

if __name__ == "__main__": 
    # cd aws-stack/server/app/backend/agents/
    aa = GetSpotsAgent()
    aa.run(trip={})


# # chromadbの場合
# import chromadb
# # https://docs.llamaindex.ai/en/stable/understanding/storing/storing/
# db = chromadb.PersistentClient(path="./chroma_db")
# try:
#     chroma_collection = db.get_or_create_collection(name="trip")
#     vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
#     storage_context = StorageContext.from_defaults(vector_store=vector_store)
#     index = VectorStoreIndex.from_vector_store(
#         vector_store, storage_context=storage_context
#     )
# except:
#     # create your index
#     index = VectorStoreIndex.from_documents(
#         documents, storage_context=storage_context
#     )