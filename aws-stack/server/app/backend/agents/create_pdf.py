from reportlab.lib.pagesizes import A4, mm, portrait
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph, Spacer, PageBreak, FrameBreak, SimpleDocTemplate,Image,Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.units import cm
from reportlab.lib import colors
from datetime import datetime
import glob
import os


class CreatePDFAgent:
    def __init__(self):
        pass
    
    def delete_files_in_folder(self,folder_path='images'):
        '''画像ファイル削除'''
        files = glob.glob(os.path.join(folder_path, '*'))
        
        # 各ファイルを削除
        for file in files:
            try:
                os.remove(file)
            except Exception as e:
                print(f"{file} の削除中にエラーが発生: {e}")

    def create_pdf_helper(self,current_style,fontsize,leading,alignment,target):
        '''PDF作成のhelper'''
        current_style.fontSize       = fontsize*mm
        current_style.leading        = leading*mm
        current_style.alignment      = alignment #　trip\Lib\site-packages\reportlab\lib\enums.py
        return Paragraph(target, current_style)

    def create_pdf_filename(self,place):
        '''PDFファイル名作成'''
        # 現在時刻を取得
        now = datetime.now()
        # yyyyMMddHHmmSS形式でフォーマット
        formatted_now = now.strftime('%Y%m%d%H%M%S')
        
        title = f"{place}おすすめスポット集"
        pdf_filename = f'{title}_{formatted_now}.pdf'
        return title,pdf_filename
    
    def create_spots_part(self,current_style,story,spots_detail):
        '''各スポット表示作成'''
        for spot in spots_detail:
            for key in spot.keys():            
                spot_name = key
                parapraph =  self.create_pdf_helper(current_style,
                                            fontsize=8,leading=15,alignment=0,target=spot_name)
                story.append(parapraph)
                story.append(Spacer(1, 10 * mm))
                
                # 画像（読み込めない可能性を考慮）
                try:
                    im = Image(f"./images/{spot_name}.jpg", 12*cm, 8*cm)
                    story.append(im)
                except:
                    continue
                story.append(Spacer(1, 5 * mm))
                
                # 紹介文
                intro_text  = spot[key]['summary']
                parapraph =  self.create_pdf_helper(current_style,
                                            fontsize=3,leading=4,alignment=0,target=intro_text)    
                story.append(parapraph)
                story.append(Spacer(1, 3 * mm))
                
                # Webサイトリンク
                spot_link = f"<a href={spot[key]['url']}><font color='blue'>詳細はこちら！</font></a>"
                parapraph =  self.create_pdf_helper(current_style,
                                            fontsize=4,leading=10,alignment=0,target=spot_link)
                story.append(parapraph)
                story.append(Spacer(1, 3 * mm))
                # GoogleMapのリンク
                spot_link = f"<a href={spot[key]['googlemap_url']}><font color='blue'>所在地を表示（Gooogle Map）</font></a>"
                parapraph =  self.create_pdf_helper(current_style,
                                            fontsize=4,leading=10,alignment=0,target=spot_link)
                story.append(parapraph)
                story.append(Spacer(1, 3 * mm))

                # このページを終了する
                story.append(PageBreak())
        
    def create_directions_part(self,current_style,story,
                          route
                          ):
        '''経路の表示作成'''
        parapraph =  self.create_pdf_helper(current_style,
                                        fontsize=8,leading=18,alignment=0,target='現地までの移動経路')
        story.append(parapraph)
        story.append(Spacer(1, 15 * mm))
        
        # 具体的な経路出力
        current_style.fontSize       = 4*mm
        current_style.leading        = 5*mm
        current_style.alignment      = 0
        for line in route['route_message']:
            # 空行にはスペーサーを追加
            if line == '':
                story.append(Spacer(1, 5 * mm))
            else:
                story.append(Paragraph(line, current_style))
        story.append(Spacer(1, 3 * mm))
        
        # 乗り換え案内
        route_link = f"<a href={route['web_search_url']}><font color='blue'>経路詳細</font></a>"
        parapraph =  self.create_pdf_helper(current_style,
                                        fontsize=4,leading=10,alignment=0,target=route_link)
        story.append(parapraph)
        story.append(Spacer(1, 5 * mm))
        
        story.append(PageBreak())
        
    def create_rental_car_part(self,current_style,story,rental_car,target_terminal):
        '''レンタカー関連'''
        parapraph =  self.create_pdf_helper(current_style,
                                        fontsize=8,leading=18,alignment=0,target='レンタカー関連の情報')
        story.append(parapraph)
        story.append(Spacer(1, 10 * mm))
            
        
        # 店舗情報画像
        parapraph =  self.create_pdf_helper(current_style,
                                        fontsize=6,leading=10,alignment=0,target=f'{target_terminal}周辺のレンタカー店舗情報(1.2km圏内)')
        story.append(parapraph)
        story.append(Spacer(1, 3 * mm))
        #　画像設定 
        im = Image(f"./images/{rental_car['map_img']}", 16*cm, 10*cm)
        story.append(im)
        story.append(Spacer(1, 5 * mm))       

        # Google Mapの情報
        route_link = f"<a href={rental_car['map_url']}><font color='blue'>Google Map</font></a>"
        parapraph =  self.create_pdf_helper(current_style,
                                        fontsize=4,leading=10,alignment=0,target=route_link)
        story.append(parapraph)
        story.append(Spacer(1, 5 * mm))
        
        story.append(PageBreak())        
        

    def create_hotels_part(self,current_style,story,
                          recommended_hotels):
        '''ホテルのリンク表示作成''' 
        parapraph =  self.create_pdf_helper(current_style,
                                        fontsize=8,leading=18,alignment=0,target='おすすめのホテルリンク集')
        story.append(parapraph)
        story.append(Spacer(1, 15 * mm))

        for hotels in recommended_hotels:
            route_link = f"<a href={hotels['formattedUrl']}><font color='blue'>{hotels['title']}</font></a>"
            parapraph =  self.create_pdf_helper(current_style,
                                            fontsize=4,leading=12,alignment=0,target=route_link)
            story.append(parapraph)
            story.append(Spacer(1, 5 * mm))
            
        story.append(PageBreak())


    def create_weather_part(self,current_style,story,
                          weather_info_links):
        '''天気がわかるサイトのリンク作成''' 
        parapraph =  self.create_pdf_helper(current_style,
                                        fontsize=8,leading=18,alignment=0,target='旅行先の天気情報（昨年分）')
        story.append(parapraph)
        story.append(Spacer(1, 15 * mm))

        for hotels in weather_info_links:
            route_link = f"<a href={hotels['formattedUrl']}><font color='blue'>{hotels['title']}</font></a>"
            parapraph =  self.create_pdf_helper(current_style,
                                            fontsize=4,leading=12,alignment=0,target=route_link)
            story.append(parapraph)
            story.append(Spacer(1, 5 * mm))  
            
    def optimize_route_plan_part(self,current_style,story,
                                 optimize_route_plan
                                 ):
        '''旅程表作成'''
        parapraph = self.create_pdf_helper(current_style,
                                        fontsize=8,leading=10,alignment=0,target='旅程案')
        story.append(parapraph)

        # 旅程作成
        # Tableの数値設定
        page_width, page_height = A4
        left_margin = 64
        right_margin = 64
        table_width = page_width - left_margin - right_margin
        col_widths = [table_width / 5.0 * 1.0, 
                    table_width / 5.0 * 2.0, 
                    table_width / 5.0 * 2.0]
        
        # テーブル作成
        table = Table(optimize_route_plan,colWidths=col_widths)
        # テーブルのスタイルを設定
        style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'HeiseiKakuGo-W5'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),  # ヘッダーの背景色をグレーに設定
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # ヘッダーのテキスト色を白に設定
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # 全てのセルのテキストを中央揃えに設定
            ('FONTNAME', (0, 0), (-1, 0), 'HeiseiKakuGo-W5'),  # ヘッダーのフォントをボールドに設定
            ('TOPPADDING', (0, 0), (-1, 0), 12),  # ヘッダーの下のパディングを設定
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # ヘッダーの下のパディングを設定
            ('TOPPADDING', (0, 1), (-1, -1), 18),  # セルの上のパディングを設定
            ('BOTTOMPADDING', (0, 1), (-1, -1), 18),  # セルの下のパディングを設定
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # セルの背景色をベージュに設定
            ('GRID', (0, 0), (-1, -1), 1, colors.white),  # グリッド線を設定
        ])
        table.setStyle(style)    
        
        story.append(table)
        story.append(PageBreak())
    
    def create_pdf(self,place=None,
                   spots_detail=None,
                   route=None,
                   optimize_route_plan=None,
                   rental_car=None,
                   target_terminal=None,
                   recommended_hotels=None,
                   weather_info_links=None
                   ):
        '''
        Report LabでPDF作成
        https://apspotplate.io/blog/a-guide-to-generate-pdfs-in-python/
        https://mori-memo.hateblo.jp/entry/2024/04/21/171759
        '''
        # ファイル名設定
        title,pdf_filename = self.create_pdf_filename(place)
        p = SimpleDocTemplate(pdf_filename, pagesize=portrait(A4))

        # スタイル指定
        styles                  = getSampleStyleSheet()
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))    
        current_style                = styles['Normal']
        current_style.fontName = "HeiseiKakuGo-W5"  # 本文のフォントを指定
        story                   = [Spacer(1, 10 * mm)]

        # PDFの内容
        # 見出し
        parapraph =  self.create_pdf_helper(current_style,
                                    fontsize=10,leading=50,alignment=0,target=title)
        story.append(parapraph)
        story.append(Spacer(1, 20 * mm))
        # 各スポットの登録
        self.create_spots_part(current_style,story,spots_detail)
        # 現地周辺までの行き方
        self.create_directions_part(current_style,story,
                          route
                          )
        # 現地での周る順番
        self.optimize_route_plan_part(current_style,story,
                          optimize_route_plan
                          )
        # レンタカー関連の情報
        self.create_rental_car_part(current_style,story,
                          rental_car,target_terminal
                          )
        # おすすめホテルリンク集
        self.create_hotels_part(current_style,story,
                          recommended_hotels
                          )
        # 天気情報
        self.create_weather_part(current_style,story,
                          weather_info_links
                          )

        # PDF作成
        p.build(story)        
    
        return pdf_filename

    def run(self, trip: dict):
        # PDF作成
        pdf_filename = self.create_pdf(
            place=trip['place'],
            spots_detail=trip['spots_detail'],
            route=trip['route'],
            optimize_route_plan=trip['optimize_route_plan'],
            rental_car=trip['rental_car'],
            target_terminal=trip['terminal_destination'],
            recommended_hotels = trip['recommended_hotels'],
            weather_info_links = trip['weather_info_links']
                        )
        trip['pdf_filename'] = pdf_filename
        # imagesフォルダのファイル削除
        self.delete_files_in_folder(folder_path='images')
        print('PDF作成完了')
        return trip


# def scan_created_pdf_by_llama():
#     '''
#     作成したPDFの検証
#     https://docs.llamaindex.ai/en/stable/module_guides/loading/connector/llama_parse/
#     '''
#     from llama_parse import LlamaParse
#     parser = LlamaParse(
#         api_key=os.getenv('LLAMA_CLOUD_API_KEY'),
#         result_type="markdown",
#         verbose=True,
#     )    
#     documents = parser.load_data('./鳥取県おすすめスポット集_20240603182442.pdf')        
#     index = VectorStoreIndex.from_documents(documents)
#     query_engine = index.as_query_engine(
#         response_mode="accumulate", # kの数分、レスポンス取得できる
#         similarity_top_k=1,
#         # streaming=True
#         )
#     query='このPDFでは観光名所が記述されています。それらの名前を全て教えてください。'
#     response = query_engine.query(query)
#     print(str(response.response))  

# def spread_sheet():
#     from google.oauth2.service_account import Credentials
#     import gspread

#     scopes = [
#         'https://www.googleapis.com/auth/spreadsheets',
#         'https://www.googleapis.com/auth/drive'
#     ]

#     credentials = Credentials.from_service_account_file(
#         'trip-pdf-sa.json',
#         scopes=scopes
#     )

#     gc = gspread.authorize(credentials)
#     spreadsheet_url = "https://docs.google.com/spreadsheets/d/1MRKzSQ9JqTOPrzFB8Bf8pPM4M4M3OjfGQLAjA39V8zY"

#     spreadsheet = gc.open_by_url(spreadsheet_url)
#     print(spreadsheet.sheet1.get_all_values())

#     # https://zenn.dev/yamagishihrd/articles/2022-09_01-google-spreadsheet-with-python 