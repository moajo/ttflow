"""Webダッシュボードの起動例

起動方法:
    uv run python examples/web_dashboard.py

ブラウザで http://localhost:8000 を開く
"""

import uvicorn

import ttflow
from ttflow.web import create_app

client = ttflow.setup("onmemory")


@client.workflow(trigger="hello")
def サンプルワークフロー(ctx):
    """挨拶するだけのワークフロー"""
    ctx.log("Hello, ttflow!")
    ctx.set_state("greeting_count", (ctx.get_state("greeting_count", 0) + 1))


@client.workflow(trigger=ttflow.state_trigger("greeting_count"))
def 挨拶カウント監視(ctx, args):
    """greeting_countの変更を検知する"""
    ctx.log(f"挨拶回数が変わりました: {args['old']} → {args['new']}")


@client.workflow(trigger=ttflow.every_trigger())
def 毎回実行(ctx):
    """毎回のrun()で実行される"""
    ctx.log("毎回実行されるワークフローです")


app = create_app(client)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
