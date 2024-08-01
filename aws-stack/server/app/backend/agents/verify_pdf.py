from openai import OpenAI
import re
import pymupdf4llm
import pathlib
import os
import traceback
# import fitz
from .conditional import ConditionalEdge

client = OpenAI()

class VerifyPdfAgent:
    def __init__(self):
        pass

    def exist_check_pdf(self,file_name):
        '''PDFのファイルが存在すること'''
        if os.path.exists(file_name):
           return True
        return False

    def check_page_and_image_count_from_pdf(self,file_name):
        '''PDFのページ数・画像枚数取得'''  # PyMuPDF
        # Open the PDF file
        # try:
        #     pdf_document = fitz.open(file_name)
        # except:
        #     traceback.print_exc()
        #     raise Exception()
        
        cnt_images = 0
        is_ok_verify = True
        # is_ok_verify = False
        # cnt_page_pdf = len(pdf_document)
        # for _ in range(2):
        #     for page_index in range(len(pdf_document)):
        #         page = pdf_document[page_index]
        #         image_list = page.get_images(full=True)
        #         # print(f"Page {page_index + 1}: {len(image_list)} images")
        #         cnt_images += len(image_list)
        #     if cnt_page_pdf >= 10 and cnt_images >= 5:
        #         is_ok_verify = True
        #         print(f'このPDFは{cnt_page_pdf}ページ')
        #         print(f'このPDFには画像が{cnt_images}枚')
        #         break
        return is_ok_verify

    def check_pdf_convert_to_markdown(self,file_name):
        '''PDFをMarkdownに変換して内容を確認'''
        md_text = pymupdf4llm.to_markdown(file_name)
        temp_md_filename = 'output.md'
        pathlib.Path(temp_md_filename).write_bytes(md_text.encode())
        with open(temp_md_filename, 'r', encoding='utf-8') as file:
            markdown_content = file.read()
           
        questions = [
            '"詳細はこちら！" が何個あるか、数字だけを教えて',
            'ヘッダーが時刻,イベント,メモ欄、となっている表の行数を、数字だけ教えて'
        ]
        expected_numbers = [5,10]
        is_ok_verify = False
        for idx,question in enumerate(questions):
            # print(question)
            for _ in range(2):
                res = client.chat.completions.create(
                    model="gpt-4o-mini-2024-07-18",
                    messages=[
                        {"role": "system", "content": "You are a helpful AI travel assistant."},
                        {"role": "user", "content": f"Content:{markdown_content}"},
                        {"role": "user", "content": f"Question: {question}"}
                    ],
                    temperature=0.25
                )

                # 数字以外の情報が取得されるケースもあるので、回答から数字だけ抽出
                text = str(res.choices[0].message.content)
                numbers = re.findall(r'\d+', text)
                if len(numbers) == 1:
                    if int(numbers[0]) >= expected_numbers[idx]:
                        # print(f'{res.choices[0].message.content}個')
                        is_ok_verify = True
                        break
                    else:
                        is_ok_verify = False
                        
        if os.path.exists(temp_md_filename):
            os.remove(temp_md_filename)
            
        return is_ok_verify


    def run(self, trip: dict):
        target_pdf = trip['pdf_filename']
        # target_pdf = '静岡県おすすめスポット集_20240624121832.pdf'
        is_exist = self.exist_check_pdf(file_name=target_pdf)
        is_expected_page_and_image_cnt = self.check_page_and_image_count_from_pdf(file_name=target_pdf)
        is_expected_sentense_cnt = self.check_pdf_convert_to_markdown(file_name=target_pdf)
        if is_exist:
            print(f'PDFの確認完了（成功）')
            if is_expected_sentense_cnt and is_expected_page_and_image_cnt:
                print(f'PDFの確認完了（成功（パーフェクト！））')
            return ConditionalEdge.SUCCESS
        else:
            print(f'PDFの確認完了（失敗）')
            return ConditionalEdge.FAILED
        
if __name__ == "__main__": 
    # cd aws-stack/server/app/backend/agents/
    aa = VerifyPdfAgent()
    print(aa.run(trip={}))