# PS Study Dashboard

SSAFY 15기 데이터 트랙 코딩테스트 스터디의 주간 문제풀이 현황을 보여주는 대시보드입니다.

## Stack

- Backend: FastAPI, httpx, APScheduler, pydantic-settings
- Frontend: Vue 3, Vite, Pinia, TanStack Query, Tailwind CSS
- Deploy: Docker multi-arch images, Helm, ArgoCD

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Optional environment variables:

```bash
export GITHUB_TOKEN=ghp_xxx
export GITHUB_OWNER=ssafy15-data
export GITHUB_REPO=python_codingtest
export STUDY_MEMBERS=dong99u,JiseokLee0106,minjun069,hyo-4,holmane333,kjin5341-blip,us4c0d3,watermell0n
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

For local API access:

```bash
echo 'VITE_API_URL=http://localhost:8000/api' > frontend/.env.local
```

## API

- `GET /api/health`
- `GET /api/milestones`
- `GET /api/matrix/{milestone_id}`
- `GET /api/members`
- `POST /api/refresh`

