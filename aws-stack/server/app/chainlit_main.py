from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from chainlit.utils import mount_chainlit
from dotenv import load_dotenv
import logging

# ログの基本設定を行う
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv(dotenv_path='.env')

app = FastAPI()


@app.get("/")
def read_main():
    return RedirectResponse(url="/trip")
    # return {"message": "Hello World from main app"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

mount_chainlit(app=app, target="chainlit_app.py", path="/trip")

'''
cd aws-stack/server/app
uvicorn chainlit_main:app --reload
'''