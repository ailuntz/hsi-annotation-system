## 后端启动
cd backend
conda activate backend
uvicorn app.main:app --reload

## 前端启动
cd frontend
npm run dev

# 后端初始化
conda create -n backend python=3.10 -y
conda activate backend
cd backend
pip install -r requirements.txt
cp .env.example .env
alembic revision --autogenerate -m "Initial tables"
alembic upgrade head

# 前端初始化
cd frontend
npm install
npx playwright install chromium
npm run generate-api

# 检查和测试
npm run check #前端类型检查
python -m ruff check . #后端 Ruff lint 
python -m mypy app --ignore-missing-imports #后端 Mypy 类型检查
python -m pytest tests/ -v #后端 Pytest
npm run test:e2e #前端 E2E 测试 (需要后端服务运行)
