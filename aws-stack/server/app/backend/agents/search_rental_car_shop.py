import os
import googlemaps
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime
import time
import traceback
from geopy.geocoders import Nominatim
from PIL import Image
import io
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')

api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("GOOGLE_MAPS_API_KEY環境変数が設定されていません")
gm = googlemaps.Client(key=api_key)

class SearchRentalCarShopAgent:
    def __init__(self):
        pass
    
    def create_pdf_filename(self,prefix):
        '''PDFファイル名作成'''
        # 現在時刻を取得
        now = datetime.now()
        # yyyyMMddHHmmSS形式でフォーマット
        formatted_now = now.strftime('%Y%m%d%H%M%S')
        
        img_filename = f'{prefix}_{formatted_now}.png'
        return img_filename
        
    def template(self,lat,lng):
        return f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Google Maps Circle and Places</title>
                    <script>
                    async function initMap() {{
                        const {{ Map }} = await google.maps.importLibrary("maps");
                        const {{ AdvancedMarkerElement }} = await google.maps.importLibrary("marker");
                        var center = {{lat: {lat}, lng: {lng}}};
                        var zoomLevel = 14; // URLから取得したズームレベル

                        var map = new Map(document.getElementById("map"), {{
                        zoom: zoomLevel,
                        center: center,
                        mapId: "DEMO_MAP_ID",
                        disableDefaultUI: true, // a way to quickly hide all controls
                        }});

                        var circle = new google.maps.Circle({{
                        map: map,
                        center: center,
                        radius: 1200, // メートル単位の半径
                        fillColor: '#D25353',
                        fillOpacity: 0.2,
                        strokeColor: '#AA0000',
                        strokeOpacity: 0.8,
                        strokeWeight: 2
                        }});

                        // レンタカーの場所を検索
                        var request = {{
                        location: center,
                        radius: '1000',
                        query: 'レンタカー'
                        }};

                        var service = new google.maps.places.PlacesService(map);
                        service.textSearch(request, function(results, status) {{
                        if (status === google.maps.places.PlacesServiceStatus.OK) {{
                            for (var i = 0; i < results.length; i++) {{
                            createMarker(results[i]);
                            }}
                        }}
                        }});

                        function createMarker(place) {{
                        var marker = new AdvancedMarkerElement({{
                            map: map,
                            position: place.geometry.location,
                            title: 'Uluru'
                        }});

                        google.maps.event.addListener(marker, 'click', function() {{
                            var infowindow = new google.maps.InfoWindow({{
                            content: place.name
                            }});
                            infowindow.open(map, marker);
                        }});
                        }}
                    }}
                    </script>
                    <style>
                    /* マップのサイズを指定 */
                    #map {{
                        height: 700px;
                        width: 100%;
                    }}
                    </style>
                </head>
                <body onload="initMap()">
                <div id="map"></div>
                <script async defer src="https://maps.googleapis.com/maps/api/js?language=ja&region=JP&key={api_key}&libraries=places&loading=async&callback=initMap"></script>
                </body>
                </html>
                """
    
    def create_rental_car_store_map(self,visit_place,target_terminal):
        # 旅行先のターミナル駅の移動・経度取得   
        res = gm.geocode(target_terminal)
        location = res[0]['geometry']['location']
        latitude = location['lat']
        longitude = location['lng']

        # テンプレート取得
        html_template = self.template(lat=latitude,lng=longitude)
        # HTMLファイルを作成
        html_file_path = "map.html"
        with open(html_file_path, "w", encoding="utf-8") as file:
            file.write(html_template)
            
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            html_file_path = os.path.join(current_dir, "../.." ,"map.html")
            local_file_url = f"file:///{html_file_path}"

            # スクリーンショットを撮る
            img_file_name = self.create_pdf_filename(prefix='rental_car_store_map')
            # imagesフォルダのパスを生成
            images_dir = os.path.join(current_dir, "../..", "images")
            screenshot_path = os.path.join(images_dir, img_file_name)


            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(local_file_url)
                time.sleep(15)
                page.screenshot(path=screenshot_path)
                browser.close()       

            print("スクリーンショットが保存されました")
            try:
                os.remove(html_file_path)
            except:
                traceback.print_exc()
        except:
            traceback.print_exc()
            os.remove(html_file_path)
        
        rental_car_dict = {}
        rental_car_dict['map_img'] = img_file_name
        rental_car_dict['map_url'] = f'https://www.google.com/maps/search/レンタカー/@{latitude},{longitude},14z'
        return rental_car_dict

    def run(self, trip: dict):
        rental_car_dict = self.create_rental_car_store_map(
            visit_place=trip['place'],
            target_terminal=trip['terminal_destination']
        )
        print(f'レンタカー関連の情報取得完了')
        trip['rental_car'] = rental_car_dict
        return trip
    
if __name__ == "__main__": 
    aa = SearchRentalCarShopAgent()
    aa.run(trip={})