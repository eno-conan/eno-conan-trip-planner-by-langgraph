import networkx as nx
import geopy.distance
import numpy as np
import os
import googlemaps
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')

gm = googlemaps.Client(key=os.getenv('GOOGLE_API_KEY'))

class OptimizeRoutePlanAgent:
    def __init__(self):
        pass
    
    def calclate_optimal_route(self,place:str,terminal_destination:str,
                               spot_list:list, location_list:list):
        
        # https://github.com/eno-conan/trip-pdf-creator/blob/main/aws-stack/server/app/backend/agents/optimize_route_plan.py
        
        spots = {}
        geolocator = Nominatim(user_agent="my_app")
        
        visit_place = place[:-1]
        # ターミナルの緯度・経度取得
        place_name = f"{terminal_destination}, {visit_place}, 日本"
        location = geolocator.geocode(place_name)
        if location.latitude is None or \
                    location.longitude is None:
            # GoogleMap API適用
            res = gm.geocode(terminal_destination)
            location = res[0]['geometry']['location']        
            spots[terminal_destination] = (location['lat'], location['lng'])                
        else:
            spots[terminal_destination] = (location.latitude, location.longitude)
         
        for idx,spot_name in enumerate(spot_list):
            spots[spot_name] = location_list[idx]  
        
        # 距離行列を作成
        spots_list_to_dict = list(spots.keys())
        n = len(spots_list_to_dict)
        distance_matrix = np.zeros((n, n))

        for i, spot1 in enumerate(spots_list_to_dict):
            for j, spot2 in enumerate(spots_list_to_dict):
                if i != j:
                    coords_1 = spots[spot1]
                    coords_2 = spots[spot2]
                    distance = geopy.distance.distance(coords_1, coords_2).km
                    distance_matrix[i, j] = distance

        # TSPアルゴリズムを適用
        G = nx.from_numpy_array(distance_matrix)
        tsp_path = nx.approximation.traveling_salesman_problem(G, cycle=True)

        # 最短ルートの表示
        tsp_route = [spots_list_to_dict[i] for i in tsp_path]
        print("最短ルート: ", tsp_route)
        
        # この配列に情報を設定==========================
        data = []
        day_cnt = 1
        data.append(["時刻","イベント","メモ欄"])
        data.append(["---",f'{day_cnt}日目開始',"---"])
        
        from datetime import datetime, timedelta
        # TODO:日程も、チャットから入力可能な状態にしたいな。
        # 出発8時
        current_time = datetime(2024, 6, 18, 9, 0, 0)
        
        # 8時（仮）～スタート
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M").split(' ')[1]
        data.append([formatted_time,f"{spots_list_to_dict[0]} 出発",""])

        # 平均速度 (km/h) を設定
        average_speed_kmh = 40
        # 各移動区間の距離と所要時間を算出
        total_distance = 0
        # 日々のランチ
        is_before_lunch = True

        for k in range(len(tsp_path) - 1):
            start = tsp_path[k]
            end = tsp_path[k + 1]
            distance = distance_matrix[start, end]
            time = (distance / average_speed_kmh) * 60
            total_distance += distance
            # print(f"{spots_list_to_dict[start]} -> {spots_list_to_dict[end]}: 時間 = {time:.2f} 分")
            
            if not time == 0:
                # 移動時間概算
                if time <= 30:
                    travel_time = 30
                elif 30 < time and time <= 60:
                    travel_time = 60
                elif 60 < time and time <= 120:
                    travel_time = 90
                else:
                    travel_time = 120

            # ある時点から次時点までの移動時間を計算
            current_time = current_time + timedelta(minutes=travel_time)
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M").split(' ')[1]
            data.append([formatted_time,f'{tsp_route[k + 1]} 到着',""])

            # お昼休憩を挟む
            if int(formatted_time.split(':')[0]) >= 12 and is_before_lunch:
                current_time = current_time + timedelta(minutes=60)
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M").split(' ')[1]
                data.append([formatted_time,f'お昼休憩',""])
                is_before_lunch = False
                
            # ある観光スポットの滞在時間
            if not k == (len(tsp_path) - 1) - 1:
                current_time = current_time + timedelta(minutes=60)
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M").split(' ')[1]
                data.append([formatted_time,f'{tsp_route[k + 1]} 観光終了',""])
                
             # 17時を過ぎている場合は、その日の観光は終了！ホテルへ移動
            if int(formatted_time.split(':')[0]) >= 17:
                current_time = current_time + timedelta(minutes=60)
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M").split(' ')[1]
                data.append([formatted_time,f'ホテル 到着',""])
                data.append(["-----",f'{day_cnt}日目 終了',"-----"])
                day_cnt += 1
                is_before_lunch = True
                # 翌日分の最小
                data.append(["-----",f'{day_cnt}日目 開始',"-----"])
                current_time = datetime(2024, 6, 18 + day_cnt, 9, 0, 0)
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M").split(' ')[1]
                data.append([formatted_time,f'ホテル 出発',""])

        return data

    def run(self, trip: dict):
        spots_detail = trip['spots_detail']
        
        spot_list = []
        location_list = []
        for spot in spots_detail:
            for spot_name in spot.keys():
                spot_list.append(spot_name)
                location_list.append(spot[spot_name]['location'])              
        
        data = self.calclate_optimal_route(
            place=trip['place'],
            # place="静岡県",
            spot_list=spot_list,
            location_list=location_list,
            terminal_destination=trip['terminal_destination']
            # terminal_destination="浜松駅"
                                           )

        trip['optimize_route_plan'] = data
        print(f'現地で効率よく周る順番、取得完了')
        return trip

if __name__ == "__main__": 
    aa = OptimizeRoutePlanAgent()
    aa.run(trip={})