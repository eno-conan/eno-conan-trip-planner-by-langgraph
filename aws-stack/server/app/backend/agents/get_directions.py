import urllib.parse
import base64
from datetime import datetime, timedelta
import time
import os
import anthropic
from playwright.sync_api import sync_playwright
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')

# client = OpenAI()
client = anthropic.Anthropic()

class GetDirectionsAgent:
    def __init__(self):
        pass

    def get_url_for_web_search(self,near_station,goal_station):
        '''乗り換え検索のURL構築
        1週間後の午前9時に現地に到着するような経路検索
        '''
        # 出発時点-到着時点
        encoded_start = urllib.parse.quote(near_station)
        encoded_goal = urllib.parse.quote(goal_station)
        from_to_params = f'from={encoded_start}&to={encoded_goal}' 
        # 現在時刻の取得
        now = datetime.now()
        one_week_later = now + timedelta(weeks=1)

        # yyyyMMddHHmmSS形式でフォーマット
        formatted_now = one_week_later.strftime('%Y%m%d%H%M')
        year = formatted_now[0:4]
        month = formatted_now[4:6]
        day = formatted_now[6:8]
        # hour = formatted_now[8:10]
        # minute_10 = formatted_now[10:11]
        # minute_1 = formatted_now[11:12]
        # date_params = f'y={year}&m={month}&d={day}&hh={hour}&m1={minute_10}&m2={minute_1}'
        date_params = f'y={year}&m={month}&d={day}&hh=10&m1=0&m2=0&type=4'

        encoded_url = f'https://transit.yahoo.co.jp/search/result?{from_to_params}&{date_params}&ticket=ic&expkind=1&userpass=0&ws=3&s=0&al=1&shin=1&ex=1&hb=1&lb=1&sr=1' 
        return encoded_url
    
    def encode_image(self,image_path):
        '''画像エンコード'''
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def compose_screenshot_filename(self,prefix):
        '''imgファイル名作成'''
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 現在時刻を取得
        now = datetime.now()
        # yyyyMMddHHmmSS形式でフォーマット
        formatted_now = now.strftime('%Y%m%d%H%M%S')
        
        img_filename = f'{prefix}_{formatted_now}'
        images_dir = os.path.join(current_dir, "../..", "images")   
        screenshot_path_base = os.path.join(images_dir, img_filename)
        return screenshot_path_base
    
    def generate_screen_shots(self,url,screenshot_path_base):
        with sync_playwright() as p:
            '''スクリーンショット作成'''
            browser = p.chromium.launch(headless=True,
            #                             downloads_path="/tmp",
            #                             args=[
            # '--autoplay-policy=user-gesture-required',
            # '--disable-background-networking',
            # '--disable-background-timer-throttling',
            # '--disable-backgrounding-occluded-windows',
            # '--disable-breakpad',
            # '--disable-client-side-phishing-detection',
            # '--disable-component-update',
            # '--disable-default-apps',
            # '--disable-dev-shm-usage',
            # '--disable-domain-reliability',
            # '--disable-extensions',
            # '--disable-features=AudioServiceOutOfProcess',
            # '--disable-hang-monitor',
            # '--disable-ipc-flooding-protection',
            # '--disable-notifications',
            # '--disable-offer-store-unmasked-wallet-cards',
            # '--disable-popup-blocking',
            # '--disable-print-preview',
            # '--disable-prompt-on-repost',
            # '--disable-renderer-backgrounding',
            # '--disable-setuid-sandbox',
            # '--disable-speech-api',
            # '--disable-sync',
            # '--disk-cache-size=33554432',
            # '--hide-scrollbars',
            # '--ignore-gpu-blacklist',
            # '--metrics-recording-only',
            # '--mute-audio',
            # '--no-default-browser-check',
            # '--no-first-run',
            # '--no-pings',
            # '--no-sandbox',
            # '--no-zygote',
            # '--password-store=basic',
            # '--use-gl=swiftshader',
            # '--use-mock-keychain',
            # '--single-process']
                                        )
            page = browser.new_page()
            page.set_default_timeout(0)
            page.goto(url)
            
            num_screenshots = 2
            scroll_height = 600
            for i in range(num_screenshots):
                # スクリーンショットを撮影
                page.evaluate(f"window.scrollBy(0, {scroll_height})")
                screenshot_path = f"{screenshot_path_base}_{i+1}.png"
                page.screenshot(path=screenshot_path)
                # print(f"Screenshot saved to {screenshot_path}")

                # ページをスクロール
                time.sleep(2)  # スクロール後にページが読み込まれるのを待つ     
            browser.close()

    def read_images_by_ai(self,image_url):
        image_media_type = "image/png"
        image_data = self.encode_image(f'{image_url}_1.png')
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000, # 出力上限（4096まで）
            temperature=0.0, # 0.0-1.0
            system="You are a helpful AI travel assistant.",
            messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": image_media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": "ルート1について、経路・所要時間・料金を教えて"
                            }
                        ],
                    }
                ],
        )
        
        text_from_image = message.content[0].text
        return text_from_image

    def create_route_guide(self,near_station,terminal_destination):
        route = {}
        # # Yahoo乗り換えのリンク作成
        encoded_url = self.get_url_for_web_search(near_station,terminal_destination)
        time.sleep(1)
        print(encoded_url)
        route['web_search_url'] = encoded_url
        
        # 画像保存のパス生成
        screenshot_path_base = self.compose_screenshot_filename(
            prefix=f'{near_station}-{terminal_destination}')
        
        # スクリーンショット作成
        self.generate_screen_shots(encoded_url,screenshot_path_base)
        
        # 画像からの文章作成（画像貼り付けでもいい気がしてきたな（笑））
        text_from_image = self.read_images_by_ai(screenshot_path_base)
        splited_answer_text = text_from_image.split('\n')
        # for text in splited_answer_text:
        #     print(text)
        route['route_message'] = splited_answer_text

        return route

    def run(self, trip: dict):
        near_station = trip['near_station']
        terminal_destination = trip['terminal_destination']
        # near_station = '北与野駅'
        # terminal_destination = '伊丹空港'
        
        # 処理実行
        route = self.create_route_guide(near_station,terminal_destination)
        
        trip['route'] = route
        print(f'経路の取得完了')
        return trip
    
if __name__ == "__main__": 
    # cd aws-stack/server/app/backend/agents/
    aa = GetDirectionsAgent()
    aa.run(trip={})