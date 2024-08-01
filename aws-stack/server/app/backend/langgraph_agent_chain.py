from typing_extensions import TypedDict
from typing import List
from langgraph.graph import StateGraph,END
import io
from openai import OpenAI
from fastapi import status
from PIL import Image

# Import agent classes
from .agents import GetSpotsAgent, SearchSpotsSiteAgent, SearchEachSpotDetailAgent,\
                    DownloadWebImagesAgent,VerifyDownloadImagesAgent,ReSearchSpotInvalidImageAgent,VerifyEachSpotAgent,\
                    GetDirectionsAgent, OptimizeRoutePlanAgent,SearchRentalCarShopAgent,\
                    SearchRecommendHotelsAgent,SearchWeatherAgent, \
                    CreatePDFAgent,VerifyPdfAgent,UploadPdfAgent,SendMailAgent ,\
                    ConditionalEdge, TripStyle

client = OpenAI()

class GraphState(TypedDict):
    # INPUTs
    place:str
    terminal_destination:str
    near_station:str
    plan_style:str
    # Graph
    # spots_url:str
    spots:List
    spots_detail:List[dict]
    images_path:List[str]
    invalid_image_spots:List[str]
    route:dict
    optimize_route_plan:List[List]
    rental_car:dict
    recommended_hotels:List[dict]
    weather_info_links:List[dict]
    pdf_filename:str
    pdf_google_drive_url:str

class MasterAgent:
    def __init__(self):
        pass

    def route_question(self,trip):
        if trip['plan_style'] == 'recommend':
            return TripStyle.RECOMMEND
        else:
            return TripStyle.DESIGNATE
    
    def count_valid_spots(self,trip):
        spots_detail = trip['spots_detail']
        # print(len(spots_detail))
        if len(spots_detail) >= 3:
            return ConditionalEdge.SUCCESS
        else:
             return ConditionalEdge.FAILED

    def run(self):
        # Initialize agents
        search_trip_agent = SearchSpotsSiteAgent()
        get_spots_agent = GetSpotsAgent()
        search_each_spot_agent = SearchEachSpotDetailAgent()
        verify_each_spot_agent = VerifyEachSpotAgent()
        get_directions_agent = GetDirectionsAgent()
        optimize_route_plan_agent = OptimizeRoutePlanAgent()
        search_rental_car_agent = SearchRentalCarShopAgent()
        search_recommend_hotels_agent = SearchRecommendHotelsAgent()
        search_weather_agent = SearchWeatherAgent()
        create_pdf_agent = CreatePDFAgent()
        verify_pdf_agent = VerifyPdfAgent()
        upload_pdf_agent = UploadPdfAgent()
        send_mail_agent = SendMailAgent()
        workflow = StateGraph(GraphState)

        # Add nodes for each agent
        workflow.add_node('search', search_trip_agent.run)
        workflow.add_node('get_spots', get_spots_agent.run)
        workflow.add_node('search_each_spot', search_each_spot_agent.run)
        workflow.add_node('verify_each_spot_agent',  verify_each_spot_agent.run)
        workflow.add_node('get_directions', get_directions_agent.run)
        workflow.add_node('optimize_drive_plan', optimize_route_plan_agent.run)
        workflow.add_node('search_rental_car', search_rental_car_agent.run)
        workflow.add_node('search_recommend_hotels', search_recommend_hotels_agent.run)
        workflow.add_node('search_weather', search_weather_agent.run)
        workflow.add_node('create_pdf', create_pdf_agent.run)
        workflow.add_node('upload_pdf', upload_pdf_agent.run)
        workflow.add_node('send_mail', send_mail_agent.run)

        # Set up edges
        '''
        # おすすめ or スポット指定で最初から分岐可能な構造にできた。
        https://github.com/langchain-ai/langgraph/blob/main/langgraph/graph/graph.py
        '''
        workflow.set_conditional_entry_point(
            path=self.route_question,
            path_map = {
                        TripStyle.RECOMMEND: "search",
                        # TripStyle.DESIGNATE: END, # Dummy
                        TripStyle.DESIGNATE: "search_each_spot",
                        },
        )
        # workflow.add_edge('search', END) # Dummy
        workflow.add_edge('search', 'get_spots')
        workflow.add_edge('get_spots', 'search_each_spot')
        workflow.add_edge('search_each_spot', 'verify_each_spot_agent')
        workflow.add_conditional_edges(
            # 開始ノードを指定
            source='verify_each_spot_agent',
            # どのノードを呼ぶか判断する関数を指定
            path=self.count_valid_spots,
            path_map={
                ConditionalEdge.SUCCESS: 'get_directions',
                ConditionalEdge.FAILED: END
            },
        )
        workflow.add_edge('get_directions', 'optimize_drive_plan')
        workflow.add_edge('optimize_drive_plan', 'search_rental_car')
        workflow.add_edge('search_rental_car', 'search_recommend_hotels')
        workflow.add_edge('search_recommend_hotels', 'search_weather')
        workflow.add_edge('search_weather', 'create_pdf')
        workflow.add_conditional_edges(
            # 開始ノードを指定
            source='create_pdf',
            # どのノードを呼ぶか判断する関数を指定
            path=verify_pdf_agent.run,
            path_map={
                ConditionalEdge.FAILED: END,
                ConditionalEdge.SUCCESS: 'upload_pdf'
            },
        )
        workflow.add_edge('upload_pdf','send_mail')
        workflow.add_edge('send_mail', END)

        # compile the graph
        self.workflow = workflow.compile()
        
        # Graphの構造確認時のみコメントアウト解除
        # graph図示
        # self.workflow.get_graph().print_ascii()
        # 画像保存
        # img = Image.open(io.BytesIO(self.workflow.get_graph().draw_png()))
        # img.save('./graph.png')
    
    def invoke(self,params):
        print(params)
        place = params['place']
        terminal_destination = params['terminal_destination']
        station = params['near_station']
        plan_style = params['plan_style']
        
        # ターミナルの情報がないケースについて、情報を設定
        if terminal_destination is None:
            # ここでどうやって設定するか？？？
            res = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": "You are a helpful AI travel assistant."},
                    {"role": "user", "content": f"Question: {place}のターミナル駅を1つ、駅名だけ教えて"}
                ],
                temperature=0.25
            )

            text = str(res.choices[0].message.content)
            # print(text)
            terminal_destination = text

        # graph実行
        result = ''
        result = self.workflow.invoke(
                    {
                        'place': place,
                        'terminal_destination': terminal_destination,
                        'near_station':station,
                        'plan_style':plan_style,
                    }
                )
        
        return {
                    'status': status.HTTP_200_OK,
                    'pdf_google_drive_url' : result['pdf_google_drive_url']
                    # 'pdf_google_drive_url' : "result['pdf_google_drive_url']"
                }
        
# if __name__ == "__main__": 
#     aa = MasterAgent()
#     aa.run()
#     params = {
#                 'place': "福岡県",
#                 'terminal_destination': "北九州空港",
#                 'near_station':"大宮駅",
#             }
#     aa.invoke(params)