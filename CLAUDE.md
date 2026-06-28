# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

日本の都道府県を指定すると、観光スポット・交通経路・ドライブルート・宿泊・天気をまとめたPDFを自動生成し、Google DriveへアップロードしてGmailで通知する旅行計画支援ツール。個人の技術検証目的のプロジェクト。

## Repository Structure

```
aws-stack/                    # CDK インフラ + サーバーアプリ一式
  pyproject.toml              # CDK 依存管理 (uv)
  uv.lock
  app.py                      # CDK エントリーポイント
  cdk.json
  aws_stack/aws_stack_stack.py  # ECS Fargate + ALB + SSM 構成定義
  tests/unit/                 # CDK インフラテスト
  server/
    pyproject.toml            # サーバーアプリ依存管理 (uv)
    uv.lock
    Dockerfile                # python:3.12-slim + uv + Playwright
    docker-compose.yml
    app/
      chainlit_main.py        # FastAPI エントリーポイント (Chainlit をマウント)
      chainlit_app.py         # Chainlit 会話ハンドラ + パスワード認証
      backend/
        langgraph_agent_chain.py  # LangGraph ワークフロー定義
        agents/               # 各ノードのエージェント実装
```

## Development Commands

### ローカル起動 (uvicorn 直接)

```bash
cd aws-stack/server
uv sync
cd app
uv run uvicorn chainlit_main:app --reload
# → http://localhost:8000/trip  (/ は /trip にリダイレクト)
# → http://localhost:8000/health  (ヘルスチェック)
```

### Docker Compose

```bash
cd aws-stack/server
docker compose up
```

### CDK デプロイ

```bash
cd aws-stack
uv sync
uv run cdk deploy
```

### テスト (CDK インフラのみ)

```bash
cd aws-stack
uv run pytest
uv run pytest tests/unit/test_aws_stack_stack.py  # 単一ファイル指定
```

### 依存関係の追加

```bash
# CDK 層
cd aws-stack && uv add <package>

# サーバー層
cd aws-stack/server && uv add <package>
```

## Required Credentials

`aws-stack/server/app/.env` を作成して以下を設定する：

| 変数名 | 用途 |
|--------|------|
| `OPENAI_API_KEY` | GPT-4o, GPT-4o-mini |
| `ANTHROPIC_API_KEY` | Claude 3.5 Sonnet (乗り換え画像 OCR) |
| `TAVILY_API_KEY` | スポット検索 |
| `GOOGLE_API_KEY` | Google Maps API + Custom Search |
| `CUSTOM_SEARCH_ENGINE_ID` | Google Custom Search Engine ID |
| `GMAIL_ADDRESS` | Chainlit ログイン用ユーザー名 + メール送信元 |
| `GMAIL_APP_PASSWORD` | Gmail アプリパスワード |
| `CHAINLIT_HOST` | タイムアウト時のリロード先 URL (任意) |

加えて、Google Drive アップロード用サービスアカウントキー `trip-pdf-sa.json` を `aws-stack/server/app/` に配置する。

AWS 環境では上記の機密情報は **SSM Parameter Store** に SecureString として格納し、ECS タスク定義で参照する。

## LangGraph Workflow

`backend/langgraph_agent_chain.py` が全ノードを定義する。

### ワークフロー分岐

```
入力 (place, plan_style, near_station)
  |
  +-- plan_style == 'recommend' → [search] → [get_spots] → [search_each_spot]
  +-- plan_style == 'designate' ─────────────────────────→ [search_each_spot]
                                                                  |
                                                     [verify_each_spot_agent]
                                                       |               |
                                              (spots >= 3)         (< 3) END
                                                  [get_directions]
                                                       |
                                            [optimize_drive_plan]
                                                       |
                                             [search_rental_car]
                                                       |
                                          [search_recommend_hotels]
                                                       |
                                              [search_weather]
                                                       |
                                               [create_pdf]
                                              /           \
                                     (検証OK)             (検証NG) END
                                     [upload_pdf]
                                          |
                                      [send_mail]
                                          |
                                         END
```

### 主要エージェントと使用技術

| ノード | ファイル | 使用技術 |
|--------|---------|---------|
| `search` | `search_spots_site.py` | Tavily API |
| `get_spots` | `get_spots_from_document.py` | GPT-4o, LlamaIndex, Google Maps API |
| `search_each_spot` | `search_each_spot.py` | Tavily API (並行実行) |
| `verify_each_spot_agent` | `verify_each_spot.py` | Google Maps, PIL, geopy |
| `get_directions` | `get_directions.py` | Playwright, Claude 3.5 Sonnet |
| `optimize_drive_plan` | `optimize_route_plan.py` | NetworkX, geopy, Google Maps |
| `search_rental_car` | `search_rental_car_shop.py` | Selenium, Google Maps |
| `search_recommend_hotels` | `search_recommend_hotels.py` | Google Custom Search, LlamaIndex, GPT-4o-mini |
| `create_pdf` | `create_pdf.py` | ReportLab |
| `upload_pdf` | `upload_pdf.py` | Google Drive API |
| `send_mail` | `send_mail.py` | Gmail SMTP |

`conditional.py` に `ConditionalEdge` (SUCCESS/FAILED) と `TripStyle` (RECOMMEND/DESIGNATE) の Enum を定義。

`GraphState` の主要フィールド: `place`, `terminal_destination`, `near_station`, `plan_style`, `spots`, `spots_detail`, `images_path`, `route`, `optimize_route_plan`, `pdf_filename`, `pdf_google_drive_url`

## AWS Architecture

`aws_stack/aws_stack_stack.py` が CDK v2 で以下を定義：
- **VPC**: 既存 VPC (`sample-vpc`) を lookup
- **ECS Fargate**: CPU 512, Memory 1024 MB, desired count 1
- **ALB**: パブリック HTTP (HTTPS なし)
- **SSM Parameter Store**: 機密情報を SecureString で管理し、ECS タスクへシークレット注入
- **コンテナイメージ**: `ecs.ContainerImage.from_asset('./server')` でローカル Dockerfile からビルド

## Chainlit Authentication

`chainlit_app.py` のパスワード認証:
- ユーザー名: `GMAIL_ADDRESS` 環境変数の値
- パスワード: `"pwd"` (ハードコード)
