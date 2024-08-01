import chainlit as cl
from backend.langgraph_agent_chain import MasterAgent
from langchain_core.messages import HumanMessage, AIMessage
from backend.agents.bullet_stations import BULLET_STATIONS
from backend.agents.airports import AIRPORTS
import traceback
from typing import Dict, Optional
import os
from openai import OpenAI
import webbrowser
from dotenv import load_dotenv
import time
load_dotenv(dotenv_path='.env')

client = OpenAI()
agent = MasterAgent()

def create_message(role, content):
    return {'role': role, 'content': content}


def update_params(key, value):
    '''
    メッセージ履歴に新しいメッセージを追加する関数
    '''
    params = cl.user_session.get("params")
    params[key] = value
    cl.user_session.set("params", params)

async def open_new_chat_another_tab():
    '''質問に対する回答がなく、timeoutとなった場合にページをリロード'''
    temp_msg = cl.Message(content='10分間入力がなかったので、処理を終了します・・・（5秒後に新しいタブで、ページを再表示します。）')
    await temp_msg.send()
    time.sleep(5)
    hostname = os.getenv('CHAINLIT_HOST', 'localhost')
    url = f"{hostname}/trip"
    webbrowser.open(url)

async def decide_transpotation_message(chat_history,
                                       target_prefecture_bullet,target_prefecture_airports,
                                       content):
    '''
    都道府県の状態に基づいて、新幹線・飛行機に関するメッセージのやりとり 
    '''
    if len(target_prefecture_bullet) > 0 and len(target_prefecture_airports) > 0:
        msg = cl.Message(content='旅行先の都道府県には、新幹線停車駅・空港両方あります。')
        await msg.send()
        res = await cl.AskActionMessage(
        content=f'どっちをつかって現地まで移動する？',
        actions=[
            # http://mrxray.on.coocan.jp/Delphi/Others/Symbols_List.htm
            # https://home.unicode.org/
            cl.Action(name='bullet', value='新幹線', label='🚝 新幹線'),
            cl.Action(name='airports', value='飛行機', label='🛫 飛行機'),
        ],
        timeout=600
        ).send()
        if res:
            chat_history['transpotation'] = res.get('value')
            if res.get('value') == '新幹線':
                selected_transpotation = target_prefecture_bullet
                chat_history['transpotation'] = content
            else:
                selected_transpotation = target_prefecture_airports       
        else:
            await open_new_chat_another_tab()        
    elif len(target_prefecture_bullet) == 0 and len(target_prefecture_airports) > 0:
        selected_transpotation = target_prefecture_airports
        chat_history['transpotation'] = '飛行機'
        msg = cl.Message(content='旅行先の都道府県には、空港のみなので、飛行機を使います。')
        await msg.send()
    elif len(target_prefecture_bullet) > 0 and len(target_prefecture_airports) == 0:
        chat_history['transpotation'] = '新幹線'
        selected_transpotation = target_prefecture_bullet
        msg = cl.Message(content='旅行先の都道府県には、空港はないので、新幹線を使います。')
        await msg.send()
    else:
        # 奈良県が例の一つだが、空港・新幹線停車駅、どちらもない場合
        selected_transpotation = []
        msg = cl.Message(content='入力した都道府県に、空港・新幹線停車駅がないので、主要な駅を目的地にします。')
        await msg.send()

    # 選択肢が・・・
    # 0個
    if len(selected_transpotation) == 0:
        chat_history['terminal_destination'] = None
    # 1個        
    elif len(selected_transpotation) == 1:
        chat_history['terminal_destination'] = selected_transpotation[0]
    # 2個以上        
    elif len(selected_transpotation) > 1:
        # 暫定でランダム取得
        import random
        random_value = random.choice(selected_transpotation)
        chat_history['terminal_destination'] = random_value

async def is_can_start_to_create_pdf():
    res = await cl.AskActionMessage(
    content=f'入力してもらった情報でPDF作成進めます！よろしいでしょうか？？',
    actions=[
        cl.Action(name='continue', value='true', label='✅ OK!'),
        cl.Action(name='cancel', value='false', label='❌ ちょっと待った！！'),
    ],
    timeout=300
    ).send()
    if res.get('value') == 'true':
        return True
    else:
        return False

async def call_langgraph_agents(chat_history):
    '''LangGraphを用いたツール呼び出し'''
    temp_msg = cl.Message(content='PDFを作成中です・・・（3分前後お待ちください！）')
    await temp_msg.send()

    result = {}
    # 最大2回実行
    for i in range(2):
        try: 
            result = await cl.make_async(agent.invoke)(
                params={
                        'place':chat_history.get('prefecture'),
                        'terminal_destination':chat_history.get('terminal_destination'),
                        'near_station':chat_history.get('near_station'),
                        'plan_style':chat_history.get('style'),
                        }
                )
            # 成功したので、履歴を削除
            cl.user_session.set('chat_history', {'messages': []})
            break
        except:
            traceback.print_exc()
            temp_msg.content = '作成失敗😢😢😢'
            await temp_msg.update()
            # 再実行に向けて
            if i < 1:
                temp_msg = cl.Message(content='再実行します・・・')
                await temp_msg.send()
                time.sleep(5)
            else:
                temp_msg = cl.Message(content='申し訳ございません。管理者にお問合せお願いします。')
                await temp_msg.send()

    # 結果に基づきメッセージを送信
    if result.get('status') == 200:
        temp_msg.content = '作成完了😀😀😀'
        await temp_msg.update()

        await cl.Message(
            content= result.get('pdf_google_drive_url'),
        ).send()
        # ドライブリンク共有
        # https://github.com/eno-conan/trip-pdf-creator/commit/6c5d263abb380cb93aaa30864fe1c0ac596acf4e
        # elements = [
        #     cl.Text(name="完成PDF", display="inline", url=result['pdf_google_drive_url'])
        # ]               

async def restart():
    cl.user_session.set('chat_history', {'messages': []})
    temp_msg = cl.Message(content='都道府県から再入力だ・・・')
    await temp_msg.send()

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if (username, password) == (os.getenv('GMAIL_ADDRESS'), "pwd"):
        return cl.User(
            identifier="eno", metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None


@cl.on_chat_start
async def on_chat_start():
    app_user = cl.user_session.get("user")
    if app_user is not None:
        pass
        # await cl.Message(f"Hello {app_user.identifier}").send()

    # LangGraphコンパイル
    agent.run()
    msg = cl.Message(content='旅行をしようじゃないか！！！')
    chat_history = cl.user_session.get('chat_history')
    await msg.send()
    
    msg = cl.Message(content=f'どの都道府県に旅行したい？？？（XXX県、という形式で入力）')
    await msg.send()
    
    # メッセージの履歴を保存するためのリストをセッションに保存
    cl.user_session.set('chat_history', {'messages': []})
    cl.user_session.set('params', {})    

@cl.on_message
async def main(message: cl.Message):
    
    content = message.content
    chat_history = cl.user_session.get('chat_history')
    chat_history['messages'].append(create_message('user', f'Answer: {content}'))

    if chat_history.get('prefecture') is None:
        # 新幹線と電車の情報を取得
        target_prefecture_bullet = BULLET_STATIONS.get(content)
        target_prefecture_airports = AIRPORTS.get(content)
        
        if target_prefecture_airports is None or target_prefecture_airports is None:
            msg = cl.Message(content='都道府県名が正しくありませんので、もう1度入力🙁')
            await msg.send()
            return

        # 都道府県の状態に基づいて、新幹線・飛行機に関するメッセージのやりとり 
        await decide_transpotation_message(chat_history,
                                           target_prefecture_bullet,target_prefecture_airports,
                                           content)
        # 行先をhistoryに設定
        chat_history['prefecture'] = content
        
        res = await cl.AskActionMessage(
        content=f'どっちがいい？',
        actions=[
            cl.Action(name='continue', value='recommend', label='おすすめに任せる'),
            cl.Action(name='cancel', value='designate', label='行きたいスポットを指定する'),
        ],
        timeout=600
        ).send()
        if res:
            if res.get('value') == 'designate':
                chat_history['style'] = res.get('value')
                # おすすめ or 自分でスポット指定を、historyに設定
                temp_msg = cl.Message(content='''気になるスポットを5カ所入力してください！
                                      ※入力例
                                      ・小樽運河
                                      ・札幌市時計台
                                      ・藻岩山
                                      ・札幌市円山動物園
                                      ・白い恋人パーク
                                      ''')
                await temp_msg.send()
            else:
                chat_history['style'] = res.get('value')
                msg = cl.Message(content='自宅最寄り駅を教えて！')
                await msg.send()
        else:
            await open_new_chat_another_tab()

    elif chat_history.get('near_station') is None and chat_history.get('style') == 'recommend':
        # 最寄り駅をhistoryに設定
        chat_history['near_station'] = content

        is_start = await is_can_start_to_create_pdf()
        # 作成開始
        if is_start:
            await call_langgraph_agents(chat_history)
        else:
            restart()
    # 以降は、行先指定の場合
    elif chat_history.get('designate_spot') is None and chat_history.get('style') == 'designate':
        chat_history['designate_spot'] = content
        msg = cl.Message(content='自宅最寄り駅を教えて！')
        await msg.send()        
    elif chat_history.get('style') == 'designate' and chat_history.get('near_station') is None:
        chat_history['near_station'] = content
        is_start = await is_can_start_to_create_pdf()
        # 作成開始
        if is_start:
            await call_langgraph_agents(chat_history)
        else:
           restart()     
                        
    chat_history = cl.user_session.set('chat_history', chat_history)
    
# @cl.on_chat_end
# def end():
#     '''新しくchatを開く事にした場合'''
#     print("goodbye", cl.user_session.get("id"))