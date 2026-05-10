cd "D:\opencode\xiuxian-game\xiuxian-mmo-game-main\xiuxian-mmo-game-main"
python -c "from backend.main import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)"