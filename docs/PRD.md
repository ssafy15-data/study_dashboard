# PS Study Dashboard — PRD

> **목적**: Claude / Codex 등 에이전틱 코딩 도구에 넘겨 구현을 시작하기 위한 완전한 스펙 문서
>
> **개발 레포**: `ssafy15-data/study_dashboard`
> **데이터 소스 레포**: `ssafy15-data/python_codingtest`
> **문서 위치**: `docs/PRD.md`

---

## 1. 프로젝트 개요

### 배경
- SSAFY 15기 데이터 트랙 코딩테스트 스터디
- GitHub 레포(`python_codingtest`)에서 Milestone / Issue / PR로 관리 중
- 문제점: 미제출자 확인이 Actions 로그뿐이라 불편, 전체 현황 한눈에 파악 어려움

### 목표
BOJ 대회 스코어보드와 유사한 주간 문제풀이 현황 대시보드를 구축하여 개인 쿠버네티스 홈랩에 GitOps(ArgoCD + Helm) 방식으로 배포한다.

### 레포 분리 전략
| 레포 | 역할 |
|------|------|
| `ssafy15-data/python_codingtest` | 스터디 운영 (문제 이슈, 풀이 PR, Actions) — **변경 없음** |
| `ssafy15-data/study_dashboard` | 대시보드 앱 코드 + CI/CD + Helm 차트 — **신규 생성** |

대시보드는 `python_codingtest`의 GitHub API를 **읽기 전용**으로 조회만 한다.

---

## 2. 인프라 환경

### 클러스터 구성 — K3s on Mixed Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Tailscale Mesh VPN                        │
│                                                             │
│  ┌─────────────────┐   ┌─────────────┐  ┌─────────────┐   │
│  │ control-plane    │   │ worker-01    │  │ worker-02    │  │
│  │ OCI ARM (aarch64)│   │ Proxmox VM  │  │ Proxmox VM  │  │
│  │ Rocky Linux 8.10 │   │ x86_64      │  │ x86_64      │  │
│  │ K3s server       │   │ K3s agent   │  │ K3s agent   │  │
│  └─────────────────┘   └─────────────┘  └─────────────┘   │
│                                                             │
│  ┌─────────────────┐                                        │
│  │ worker-03        │                                       │
│  │ OCI ARM (aarch64)│                                       │
│  │ Rocky Linux 8.10 │                                       │
│  │ K3s agent        │                                       │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
         │
         │ Cloudflare Tunnel
         ▼
  dashboard.도메인.com (외부 접속)
```

### 핵심 인프라 제약
| 항목 | 내용 | 영향 |
|------|------|------|
| 아키텍처 혼합 | ARM64 (OCI) + AMD64 (Proxmox) | **멀티 아키텍처 이미지 빌드 필수** |
| K3s | 경량 k8s 배포판 | Traefik 기본 (nginx-ingress 전환 가능) |
| 네트워크 | Tailscale 메시 VPN | 노드 간 통신은 Tailscale IP |
| 외부 접속 | Cloudflare Tunnel | TLS 종단은 Cloudflare Edge |
| OS | Rocky Linux 8.10 | 전 노드 동일 |

---

## 3. 데이터 소스 — python_codingtest 레포

### 레포 정보
```
owner: ssafy15-data
repo:  python_codingtest
visibility: public
```

### Milestone
- 이름: `260519 스터디` (YYMMDD + " 스터디")
- `due_on` 필드로 마감일 관리
- 1 milestone = 1 스터디 회차 (보통 2~3문제)

### Issue
- 제목: `[LeetCode 3640] Trionic Array II`, `[SWEA 1855] 영준이의 진짜 BFS`
- 파싱 패턴: `^\[(\w+)\s+(\d+)\]\s*(.+)$` → (platform, number, name)
- 지원 플랫폼: `LeetCode`, `SWEA`, `Programmers`, `BOJ`
- 라벨: 난이도 (`Hard`, `Med.`, `Easy`, `D6`, `D5` 등)
- milestone 연결로 회차 소속 파악

### PR
- body 첫 줄: `Issue: #100, #101` → 이슈 번호 파싱
- 정규식: `^Issue:\s*(#\d+(?:,\s*#\d+)*)`
- PR author GitHub 아이디 = 멤버 식별자
- `merged_at` non-null → 풀이 완료

### 멤버
- 스터디 룰: 레포 폴더명 = GitHub 아이디
- Helm values의 `config.studyMembers`로 관리
- 현재 멤버:
  ```
  dong99u, JiseokLee0106, minjun069, hyo-4,
  holmane333, kjin5341-blip, us4c0d3, watermell0n
  ```

---

## 4. 기능 요구사항

### Phase 1 — MVP

#### F-01. 주간 현황 매트릭스 (메인 뷰)
- 현재 진행 중 milestone 자동 선택
- 드롭다운으로 회차 전환
- 테이블: 행 = 멤버, 열 = 문제(이슈)
- 셀 상태:
  | 상태 | 조건 | 표시 |
  |------|------|------|
  | `merged` | merged PR 존재 | 초록 ✓ |
  | `open_pr` | PR 제출, 미merge | 노랑 ⏳ |
  | `not_submitted` (마감 전) | PR 없음 | 빨강 ✗ |
  | `not_submitted` (마감 후) | PR 없음, overdue | 회색 ✗ |
- 문제 헤더: 플랫폼 뱃지 + 번호 + 제목 (클릭 → 이슈 링크)
- 마감 카운트다운: D-3, D-day, Overdue +2일

#### F-02. 기본 통계 카드
메인 뷰 상단 3개 카드:
- 이번 회차 제출률 (%)
- 미제출 인원 / 전체 인원
- 마감까지 남은 시간

#### F-03. 데이터 갱신
- 서버 시작 시 전체 데이터 로드
- 15분 주기 background polling (APScheduler)
- `POST /api/refresh` 수동 갱신
- 마지막 갱신 시각 UI 표시

### Phase 2

#### F-04. 멤버 프로필 페이지 (`/member/{id}`)
#### F-05. 전체 통계 페이지 (`/stats`) + 차트
#### F-06. GitHub OAuth 로그인
#### F-07. Webhook 실시간 갱신 (`POST /webhook/github`)

---

## 5. 기술 스택

### 백엔드
| 항목 | 선택 | 비고 |
|------|------|------|
| 언어 | Python 3.12+ | |
| 프레임워크 | FastAPI | async, OpenAPI 자동 생성 |
| GitHub API | httpx (async) | rate limit 핸들링 포함 |
| 스케줄러 | APScheduler | 15분 interval |
| 캐시 | in-memory dict (MVP) → Redis (Phase 2) | |
| 설정 | pydantic-settings | |
| 테스트 | pytest + pytest-asyncio | |

### 프론트엔드
| 항목 | 선택 | 비고 |
|------|------|------|
| 프레임워크 | Vue 3 (Composition API) | `<script setup>` SFC |
| 빌드 | Vite | SPA, 정적 빌드 → `dist/` |
| 라우팅 | Vue Router 4 | hash 또는 history mode |
| 상태관리 | Pinia | 가볍고 TS 친화적 |
| 데이터 패칭 | @tanstack/vue-query | 자동 refetch, 캐시, 로딩 상태 |
| 스타일 | Tailwind CSS | |
| 차트 | vue-chartjs (Chart.js 래퍼) | Phase 2 |
| HTTP 클라이언트 | axios 또는 ky | vue-query의 queryFn에서 사용 |

### CI/CD & 인프라
| 항목 | 선택 | 비고 |
|------|------|------|
| CI | GitHub Actions | study_dashboard 레포 |
| 이미지 빌드 | docker buildx (multi-arch) | linux/amd64 + linux/arm64 |
| 레지스트리 | ghcr.io | 같은 org, public 무료 |
| 패키지 매니저 | Helm 3 | 차트 패키징 + values 관리 |
| GitOps | ArgoCD | Helm 차트 변경 감지 → 자동 배포 |
| 클러스터 | K3s | Rocky Linux 8.10 |
| Ingress | Traefik (기본) / Nginx Ingress (전환 대비) | |
| 외부 접속 | Cloudflare Tunnel | |

---

## 6. 시스템 아키텍처

```
┌─ GitHub ───────────────────────────────────────┐
│                                                │
│  python_codingtest                              │
│  └── Milestones / Issues / PRs (데이터 소스)     │
│                                                │
│  study_dashboard                                │
│  ├── backend/ + frontend/ + charts/            │
│  └── push main                                 │
│       → GitHub Actions                         │
│         ├── pytest + lint                       │
│         ├── docker buildx (amd64 + arm64)      │
│         ├── ghcr.io push                       │
│         └── Helm values image tag 갱신 → commit │
└────────────────────────────────────────────────┘
                      │
            ArgoCD watches charts/
                      │
                      ▼
┌─ K3s Homelab (Tailscale mesh) ─────────────────┐
│                                                │
│  namespace: ps-dashboard                       │
│                                                │
│  ┌────────────────┐    polling     ┌────────┐  │
│  │ backend:8000   │ ──────────────→│ GitHub │  │
│  │ FastAPI        │    15min       │ API    │  │
│  └───────┬────────┘                └────────┘  │
│          │ /api/*                              │
│  ┌───────▼────────┐                            │
│  │ frontend:80    │  ← nginx serving static    │
│  │ Vue 3 SPA      │                            │
│  └───────┬────────┘                            │
│          │                                     │
│  ┌───────▼────────┐    ┌───────────────────┐   │
│  │ Ingress        │←───│ cloudflared       │   │
│  │ Traefik/Nginx  │    │ (Cloudflare Tunnel)│  │
│  └────────────────┘    └───────────────────┘   │
│                                                │
│  dashboard.도메인.com                            │
└────────────────────────────────────────────────┘
```

---

## 7. 프로젝트 디렉토리 구조

```
study_dashboard/
│
├── README.md
├── .gitignore
│
├── docs/
│   └── PRD.md                         ← 이 문서
│
├── .github/
│   └── workflows/
│       ├── ci.yaml                    # PR: lint + test + helm lint
│       └── build-deploy.yaml          # main push: 멀티아키 빌드 → ghcr.io → tag 갱신
│
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app, lifespan
│   │   ├── config.py                  # pydantic-settings
│   │   ├── github_client.py           # httpx async GitHub API
│   │   ├── data_collector.py          # parse + matrix 빌드
│   │   ├── cache.py                   # in-memory cache
│   │   ├── scheduler.py              # APScheduler
│   │   ├── models.py                  # Pydantic 응답 모델
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── milestones.py
│   │       ├── matrix.py
│   │       ├── members.py
│   │       ├── stats.py               # Phase 2
│   │       └── system.py              # health, refresh
│   └── tests/
│       ├── conftest.py
│       ├── test_data_collector.py
│       └── test_routers.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── index.html                     # Vite 엔트리 포인트
│   ├── Dockerfile
│   ├── nginx.conf                     # SPA용 nginx 설정
│   ├── src/
│   │   ├── main.ts                    # Vue 앱 부트스트랩
│   │   ├── App.vue                    # 루트 컴포넌트
│   │   ├── router/
│   │   │   └── index.ts               # Vue Router 설정
│   │   ├── stores/
│   │   │   └── dashboard.ts           # Pinia 스토어 (선택적)
│   │   ├── composables/
│   │   │   ├── useMatrix.ts           # vue-query로 매트릭스 fetch
│   │   │   ├── useMilestones.ts       # vue-query로 milestone fetch
│   │   │   └── useMembers.ts          # vue-query로 멤버 fetch
│   │   ├── components/
│   │   │   ├── ScoreBoard.vue         # 핵심 매트릭스 테이블
│   │   │   ├── MilestoneSelector.vue  # 회차 드롭다운
│   │   │   ├── StatusCell.vue         # ✓ ⏳ ✗ 셀
│   │   │   ├── PlatformBadge.vue      # LeetCode/SWEA/BOJ 뱃지
│   │   │   ├── StatsCards.vue         # 제출률, 미제출, 마감 카드
│   │   │   └── LastUpdated.vue        # 마지막 갱신 시각
│   │   ├── views/
│   │   │   ├── DashboardView.vue      # 메인 현황판 페이지
│   │   │   ├── MemberView.vue         # Phase 2
│   │   │   └── StatsView.vue          # Phase 2
│   │   ├── lib/
│   │   │   └── api.ts                 # axios 인스턴스 + API 타입 정의
│   │   └── types/
│   │       └── index.ts               # 공유 TypeScript 타입
│   └── public/
│       └── favicon.ico
│
└── charts/
    └── ps-dashboard/                  # Helm 차트
        ├── Chart.yaml
        ├── values.yaml
        ├── values-prod.yaml
        └── templates/
            ├── _helpers.tpl
            ├── namespace.yaml
            ├── backend-deployment.yaml
            ├── backend-service.yaml
            ├── frontend-deployment.yaml
            ├── frontend-service.yaml
            ├── ingress.yaml
            ├── configmap.yaml
            ├── secret.yaml
            └── NOTES.txt
```

---

## 8. Helm 차트 설계

### `charts/ps-dashboard/Chart.yaml`
```yaml
apiVersion: v2
name: ps-dashboard
description: PS Study Dashboard — 코딩테스트 스터디 현황판
type: application
version: 0.1.0
appVersion: "1.0.0"

# Phase 2: Redis 추가 시
# dependencies:
#   - name: redis
#     version: "~18.x"
#     repository: https://charts.bitnami.com/bitnami
#     condition: redis.enabled
```

### `charts/ps-dashboard/values.yaml`
```yaml
# ── 공통 ──
namespace: ps-dashboard

# ── 백엔드 ──
backend:
  image:
    repository: ghcr.io/ssafy15-data/study-dashboard-backend
    tag: latest
    pullPolicy: IfNotPresent
  replicas: 1
  port: 8000
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"
    limits:
      memory: "256Mi"
      cpu: "500m"

# ── 프론트엔드 ──
frontend:
  image:
    repository: ghcr.io/ssafy15-data/study-dashboard-frontend
    tag: latest
    pullPolicy: IfNotPresent
  replicas: 1
  port: 80          # nginx
  resources:
    requests:
      memory: "64Mi"
      cpu: "50m"
    limits:
      memory: "128Mi"
      cpu: "200m"

# ── 앱 설정 (ConfigMap) ──
config:
  githubOwner: "ssafy15-data"
  githubRepo: "python_codingtest"
  studyMembers: "dong99u,JiseokLee0106,minjun069,hyo-4,holmane333,kjin5341-blip,us4c0d3,watermell0n"
  refreshIntervalMinutes: "15"

# ── 시크릿 ──
secret:
  githubToken: ""    # --set secret.githubToken=ghp_xxx

# ── Ingress ──
ingress:
  enabled: true
  className: traefik  # "nginx" 전환 가능
  host: dashboard.example.com
  tls: false          # Cloudflare Tunnel이 TLS 종단

# ── Phase 2 ──
redis:
  enabled: false
```

### `charts/ps-dashboard/values-prod.yaml`
```yaml
ingress:
  host: dashboard.실제도메인.com

backend:
  image:
    tag: "abc123"  # backend-tag  (CI가 commit SHA로 갱신)

frontend:
  image:
    tag: "abc123"  # frontend-tag (CI가 commit SHA로 갱신)
```

### 주요 템플릿

#### `templates/_helpers.tpl`
```yaml
{{- define "ps-dashboard.fullname" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "ps-dashboard.labels" -}}
app.kubernetes.io/name: ps-dashboard
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
```

#### `templates/backend-deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "ps-dashboard.fullname" . }}-backend
  namespace: {{ .Values.namespace }}
  labels:
    {{- include "ps-dashboard.labels" . | nindent 4 }}
    app.kubernetes.io/component: backend
spec:
  replicas: {{ .Values.backend.replicas }}
  selector:
    matchLabels:
      app.kubernetes.io/name: ps-dashboard
      app.kubernetes.io/component: backend
  template:
    metadata:
      labels:
        app.kubernetes.io/name: ps-dashboard
        app.kubernetes.io/component: backend
    spec:
      containers:
        - name: backend
          image: "{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}"
          imagePullPolicy: {{ .Values.backend.image.pullPolicy }}
          ports:
            - containerPort: {{ .Values.backend.port }}
              protocol: TCP
          env:
            - name: GITHUB_TOKEN
              valueFrom:
                secretKeyRef:
                  name: {{ include "ps-dashboard.fullname" . }}-secret
                  key: github-token
          envFrom:
            - configMapRef:
                name: {{ include "ps-dashboard.fullname" . }}-config
          livenessProbe:
            httpGet:
              path: /api/health
              port: {{ .Values.backend.port }}
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /api/health
              port: {{ .Values.backend.port }}
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            {{- toYaml .Values.backend.resources | nindent 12 }}
```

#### `templates/frontend-deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "ps-dashboard.fullname" . }}-frontend
  namespace: {{ .Values.namespace }}
  labels:
    {{- include "ps-dashboard.labels" . | nindent 4 }}
    app.kubernetes.io/component: frontend
spec:
  replicas: {{ .Values.frontend.replicas }}
  selector:
    matchLabels:
      app.kubernetes.io/name: ps-dashboard
      app.kubernetes.io/component: frontend
  template:
    metadata:
      labels:
        app.kubernetes.io/name: ps-dashboard
        app.kubernetes.io/component: frontend
    spec:
      containers:
        - name: frontend
          image: "{{ .Values.frontend.image.repository }}:{{ .Values.frontend.image.tag }}"
          imagePullPolicy: {{ .Values.frontend.image.pullPolicy }}
          ports:
            - containerPort: {{ .Values.frontend.port }}
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /
              port: {{ .Values.frontend.port }}
            initialDelaySeconds: 5
            periodSeconds: 30
          resources:
            {{- toYaml .Values.frontend.resources | nindent 12 }}
```

#### `templates/ingress.yaml`
```yaml
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "ps-dashboard.fullname" . }}-ingress
  namespace: {{ .Values.namespace }}
  labels:
    {{- include "ps-dashboard.labels" . | nindent 4 }}
  annotations:
    {{- if eq .Values.ingress.className "traefik" }}
    traefik.ingress.kubernetes.io/router.entrypoints: web
    {{- end }}
    {{- if eq .Values.ingress.className "nginx" }}
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    {{- end }}
spec:
  ingressClassName: {{ .Values.ingress.className }}
  rules:
    - host: {{ .Values.ingress.host }}
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: {{ include "ps-dashboard.fullname" . }}-backend
                port:
                  number: {{ .Values.backend.port }}
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "ps-dashboard.fullname" . }}-frontend
                port:
                  number: {{ .Values.frontend.port }}
{{- end }}
```

#### `templates/configmap.yaml`
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "ps-dashboard.fullname" . }}-config
  namespace: {{ .Values.namespace }}
data:
  GITHUB_OWNER: {{ .Values.config.githubOwner | quote }}
  GITHUB_REPO: {{ .Values.config.githubRepo | quote }}
  STUDY_MEMBERS: {{ .Values.config.studyMembers | quote }}
  REFRESH_INTERVAL_MINUTES: {{ .Values.config.refreshIntervalMinutes | quote }}
```

#### `templates/secret.yaml`
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "ps-dashboard.fullname" . }}-secret
  namespace: {{ .Values.namespace }}
type: Opaque
data:
  github-token: {{ .Values.secret.githubToken | b64enc | quote }}
```

---

## 9. 프론트엔드 상세 설계 (Vue 3 + Vite)

### 라우터 구성
```typescript
// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
  { path: '/member/:id', name: 'member', component: () => import('@/views/MemberView.vue') },  // Phase 2
  { path: '/stats', name: 'stats', component: () => import('@/views/StatsView.vue') },          // Phase 2
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
```

### API 클라이언트
```typescript
// src/lib/api.ts
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
})

export default api
```

### Composable (vue-query)
```typescript
// src/composables/useMatrix.ts
import { useQuery } from '@tanstack/vue-query'
import api from '@/lib/api'
import type { MatrixResponse } from '@/types'

export function useMatrix(milestoneId: Ref<number | null>) {
  return useQuery({
    queryKey: ['matrix', milestoneId],
    queryFn: () => api.get<MatrixResponse>(`/api/matrix/${milestoneId.value}`).then(r => r.data),
    enabled: () => milestoneId.value !== null,
    refetchInterval: 60_000,  // 1분마다 자동 refetch
  })
}
```

### 핵심 컴포넌트 — ScoreBoard.vue
```vue
<!-- src/components/ScoreBoard.vue -->
<script setup lang="ts">
import { computed } from 'vue'
import StatusCell from './StatusCell.vue'
import PlatformBadge from './PlatformBadge.vue'
import type { MatrixResponse } from '@/types'

const props = defineProps<{ data: MatrixResponse }>()

// 멤버를 제출 수 내림차순 정렬
const sortedMembers = computed(() => {
  return [...props.data.members].sort((a, b) => {
    const countA = Object.values(props.data.matrix[a]).filter(v => v.status === 'merged').length
    const countB = Object.values(props.data.matrix[b]).filter(v => v.status === 'merged').length
    return countB - countA
  })
})
</script>

<template>
  <div class="overflow-x-auto">
    <table class="min-w-full border-collapse">
      <thead>
        <tr>
          <th class="sticky left-0 bg-white z-10 px-4 py-3 text-left">멤버</th>
          <th v-for="problem in data.problems" :key="problem.issue_number" class="px-3 py-3 text-center">
            <a :href="problem.url" target="_blank" class="hover:underline">
              <PlatformBadge :platform="problem.platform" />
              <span class="block text-xs mt-1">{{ problem.platform_number }}</span>
            </a>
          </th>
          <th class="px-3 py-3 text-center">제출</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="member in sortedMembers" :key="member" class="border-t hover:bg-gray-50">
          <td class="sticky left-0 bg-white px-4 py-3 font-medium">
            {{ member }}
          </td>
          <td v-for="problem in data.problems" :key="problem.issue_number" class="px-3 py-3 text-center">
            <StatusCell
              :status="data.matrix[member]?.[String(problem.issue_number)]?.status ?? 'not_submitted'"
              :pr-url="data.matrix[member]?.[String(problem.issue_number)]?.pr_url"
              :is-overdue="data.milestone.is_overdue"
            />
          </td>
          <td class="px-3 py-3 text-center font-mono text-sm">
            {{ Object.values(data.matrix[member] || {}).filter(v => v.status === 'merged').length }}
            / {{ data.problems.length }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
```

### 타입 정의
```typescript
// src/types/index.ts
export interface Milestone {
  id: number
  title: string
  due_on: string
  state: string
  is_overdue: boolean
  days_left: number
  total_issues: number
  closed_issues: number
}

export interface Problem {
  issue_number: number
  title: string
  platform: string
  platform_number: string
  difficulty: string
  url: string
}

export interface CellStatus {
  status: 'merged' | 'open_pr' | 'not_submitted'
  pr_number?: number
  pr_url?: string
}

export interface MatrixResponse {
  milestone: Milestone
  problems: Problem[]
  members: string[]
  matrix: Record<string, Record<string, CellStatus>>
  summary: {
    total_submissions: number
    total_possible: number
    submission_rate: number
  }
}

export interface Member {
  github_id: string
  avatar_url: string
  total_solved: number
  total_possible: number
  attendance_rate: number
}
```

### 환경변수
```env
# frontend/.env
VITE_API_URL=/api
```
- 프로덕션: Ingress가 `/api` → backend, `/` → frontend로 라우팅하므로 상대 경로 `/api` 사용
- 로컬 개발: `VITE_API_URL=http://localhost:8000` 오버라이드

### nginx.conf (SPA 라우팅 + API 프록시 불필요)
```nginx
# frontend/nginx.conf
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Vue Router history mode — 모든 경로를 index.html로
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 정적 자산 캐싱 (Vite 해시 파일명이라 장기 캐시 안전)
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 헬스체크
    location /healthz {
        return 200 'ok';
        add_header Content-Type text/plain;
    }
}
```

---

## 10. Dockerfile

### Backend
```dockerfile
FROM python:3.12-slim AS base
WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY app/ ./app/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend (Vue 3 + Vite → nginx)
```dockerfile
# ── 빌드 스테이지 ──
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build    # → dist/

# ── 서빙 스테이지 ──
FROM nginx:alpine AS runner
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Next.js 대비 장점**: Node.js 런타임 불필요, nginx:alpine 이미지 약 40MB, 메모리 사용 극소.

---

## 11. CI/CD 파이프라인

### 11-1. PR 검증 — `.github/workflows/ci.yaml`
```yaml
name: CI
on:
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: pytest

  frontend-lint:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - run: npm run lint
      - run: npm run build

  helm-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-helm@v3
      - run: helm lint charts/ps-dashboard
      - run: helm template test charts/ps-dashboard | kubectl apply --dry-run=client -f -
```

### 11-2. 빌드 & 배포 — `.github/workflows/build-deploy.yaml`
```yaml
name: Build & Deploy
on:
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  BACKEND_IMAGE: ghcr.io/ssafy15-data/study-dashboard-backend
  FRONTEND_IMAGE: ghcr.io/ssafy15-data/study-dashboard-frontend

jobs:
  build-backend:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-qemu-action@v3
        with:
          platforms: arm64
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: backend
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            ${{ env.BACKEND_IMAGE }}:${{ github.sha }}
            ${{ env.BACKEND_IMAGE }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  build-frontend:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-qemu-action@v3
        with:
          platforms: arm64
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: frontend
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            ${{ env.FRONTEND_IMAGE }}:${{ github.sha }}
            ${{ env.FRONTEND_IMAGE }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  update-helm-values:
    needs: [build-backend, build-frontend]
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - name: Update image tags in values-prod.yaml
        run: |
          cd charts/ps-dashboard
          sed -i "s|tag:.*# backend-tag|tag: \"${{ github.sha }}\"  # backend-tag|" values-prod.yaml
          sed -i "s|tag:.*# frontend-tag|tag: \"${{ github.sha }}\"  # frontend-tag|" values-prod.yaml
      - name: Commit & push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add charts/
          git diff --cached --quiet || git commit -m "chore: update image tags to ${{ github.sha }}"
          git push
```

### 11-3. GitOps 흐름
```
push main
  → GitHub Actions
    → pytest + lint + helm lint
    → docker buildx (amd64 + arm64) → ghcr.io
    → values-prod.yaml image tag → commit SHA 갱신 → push
  → ArgoCD 감지
    → helm upgrade → K3s 클러스터 자동 배포
```

### 11-4. ArgoCD Application
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ps-dashboard
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/ssafy15-data/study_dashboard.git
    targetRevision: main
    path: charts/ps-dashboard
    helm:
      valueFiles:
        - values.yaml
        - values-prod.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: ps-dashboard
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

---

## 12. Cloudflare Tunnel 연동

TLS 종단은 Cloudflare Edge에서 처리, 클러스터 내부는 HTTP.

```
사용자 → dashboard.도메인.com (HTTPS)
  → Cloudflare Edge (TLS 종단)
  → Cloudflare Tunnel (cloudflared)
  → K3s Ingress (Traefik/Nginx, HTTP)
  → /api/* → backend Service
  → /*     → frontend Service
```

### cloudflared 설정 예시
```yaml
tunnel: <터널 ID>
credentials-file: /etc/cloudflared/<터널 ID>.json

ingress:
  - hostname: dashboard.도메인.com
    service: http://traefik.kube-system.svc:80
  - service: http_status:404
```

---

## 13. 멀티 아키텍처 빌드 상세

### 왜 필요한가
Pod가 ARM(OCI) 또는 x86(Proxmox) 어디든 스케줄링될 수 있다.
단일 아키텍처 이미지 → 해당 아키텍처 아닌 노드에서 `exec format error`.

### CI에서의 처리
- `docker/setup-qemu-action`: ARM64 에뮬레이션
- `docker buildx build --platform linux/amd64,linux/arm64`: 동시 빌드
- `cache-from/to: type=gha`: 빌드 시간 단축

### 베이스 이미지 호환성
| 이미지 | multi-arch | 비고 |
|--------|-----------|------|
| `python:3.12-slim` | ✅ amd64 + arm64 | 문제 없음 |
| `node:20-alpine` | ✅ amd64 + arm64 | 빌드 스테이지만 |
| `nginx:alpine` | ✅ amd64 + arm64 | 서빙 스테이지 |

---

## 14. API 설계

### `GET /api/health`
```json
{ "status": "ok", "last_refresh": "2026-05-15T12:30:00Z" }
```

### `GET /api/milestones`
```json
[
  {
    "id": 5,
    "title": "260519 스터디",
    "due_on": "2026-05-19T15:00:00Z",
    "state": "open",
    "is_overdue": false,
    "days_left": 4,
    "total_issues": 3,
    "closed_issues": 0
  }
]
```

### `GET /api/matrix/{milestone_id}`
```json
{
  "milestone": {
    "id": 5, "title": "260519 스터디",
    "due_on": "2026-05-19T15:00:00Z",
    "is_overdue": false, "days_left": 4
  },
  "problems": [
    {
      "issue_number": 116,
      "title": "Check If Word Is Valid After Substitutions",
      "platform": "LeetCode",
      "platform_number": "1003",
      "difficulty": "Med.",
      "url": "https://github.com/ssafy15-data/python_codingtest/issues/116"
    }
  ],
  "members": ["dong99u", "minjun069", "us4c0d3"],
  "matrix": {
    "dong99u": {
      "116": { "status": "merged", "pr_number": 114, "pr_url": "..." },
      "117": { "status": "not_submitted" }
    }
  },
  "summary": {
    "total_submissions": 5,
    "total_possible": 24,
    "submission_rate": 0.208
  }
}
```

### `GET /api/members`
```json
[
  {
    "github_id": "dong99u",
    "avatar_url": "https://avatars.githubusercontent.com/...",
    "total_solved": 12,
    "total_possible": 15,
    "attendance_rate": 0.80
  }
]
```

### `POST /api/refresh` → 204 No Content
### Phase 2: `GET /api/member/{id}`, `GET /api/stats`, `POST /webhook/github`

---

## 15. 핵심 데이터 수집 로직

```python
import re
from collections import defaultdict

def parse_issue_numbers(body: str | None) -> list[int]:
    """PR body 첫 줄에서 이슈 번호 파싱. 패턴: Issue: #100, #101"""
    if not body:
        return []
    first_line = body.strip().split("\n")[0]
    match = re.match(r"^Issue:\s*(#\d+(?:,\s*#\d+)*)", first_line)
    if not match:
        return []
    return [int(x.strip().lstrip("#")) for x in match.group(1).split(",")]


def parse_issue_title(title: str) -> tuple[str, str, str]:
    """이슈 제목 → (platform, number, name)"""
    match = re.match(r"^\[(\w+)\s+(\d+)\]\s*(.+)$", title)
    if not match:
        return ("Unknown", "", title)
    return (match.group(1), match.group(2), match.group(3).strip())


async def build_matrix(client, milestone_id: int, members: list[str]) -> dict:
    issues = await client.get_issues(milestone=milestone_id, state="all")

    issue_member_map = defaultdict(dict)
    for pr in await client.get_pulls(state="all"):
        author = pr["user"]["login"]
        if author not in members:
            continue
        is_merged = pr.get("merged_at") is not None
        for num in parse_issue_numbers(pr.get("body")):
            existing = issue_member_map[num].get(author)
            if existing and existing["status"] == "merged":
                continue
            issue_member_map[num][author] = {
                "status": "merged" if is_merged else "open_pr",
                "pr_number": pr["number"],
                "pr_url": pr["html_url"],
            }

    matrix = {}
    for member in members:
        matrix[member] = {}
        for issue in issues:
            num = issue["number"]
            if member in issue_member_map.get(num, {}):
                matrix[member][str(num)] = issue_member_map[num][member]
            else:
                matrix[member][str(num)] = {"status": "not_submitted"}

    return matrix
```

---

## 16. 환경변수

### 백엔드 필수
```env
GITHUB_TOKEN=ghp_xxxx
GITHUB_OWNER=ssafy15-data
GITHUB_REPO=python_codingtest
STUDY_MEMBERS=dong99u,JiseokLee0106,minjun069,...
REFRESH_INTERVAL_MINUTES=15
```

### 백엔드 Phase 2
```env
GITHUB_CLIENT_ID=xxxx
GITHUB_CLIENT_SECRET=xxxx
WEBHOOK_SECRET=xxxx
REDIS_URL=redis://redis:6379
```

### 프론트엔드
```env
VITE_API_URL=/api
```

---

## 17. 구현 체크리스트

### Phase 1 — MVP
- [ ] `study_dashboard` 레포 생성, README, .gitignore
- [ ] **백엔드**
  - [ ] pyproject.toml + FastAPI 뼈대
  - [ ] config.py (pydantic-settings)
  - [ ] github_client.py (httpx async, rate limit)
  - [ ] data_collector.py (parse_issue_numbers, parse_issue_title, build_matrix)
  - [ ] cache.py (thread-safe in-memory)
  - [ ] scheduler.py (APScheduler 15분)
  - [ ] models.py (Pydantic 응답)
  - [ ] routers/ (milestones, matrix, members, system)
  - [ ] CORS 설정
  - [ ] tests/ (단위 + 통합)
  - [ ] Dockerfile (multi-arch 호환)
- [ ] **프론트엔드**
  - [ ] Vue 3 + Vite + Tailwind 초기화
  - [ ] Vue Router (history mode)
  - [ ] @tanstack/vue-query 설정
  - [ ] composables/ (useMatrix, useMilestones, useMembers)
  - [ ] components/ (ScoreBoard, MilestoneSelector, StatusCell, PlatformBadge, StatsCards, LastUpdated)
  - [ ] views/DashboardView.vue
  - [ ] lib/api.ts (axios + 타입)
  - [ ] types/index.ts
  - [ ] nginx.conf (SPA fallback)
  - [ ] Dockerfile (Vite build → nginx:alpine)
- [ ] **Helm 차트**
  - [ ] Chart.yaml, values.yaml, values-prod.yaml
  - [ ] templates/ (deployments, services, ingress, configmap, secret, _helpers)
  - [ ] `helm lint` + `helm template --dry-run` 통과
- [ ] **CI/CD**
  - [ ] ci.yaml (PR: pytest, lint, helm lint)
  - [ ] build-deploy.yaml (멀티아키 빌드 → ghcr.io → tag 갱신)
- [ ] **ArgoCD**
  - [ ] Application 매니페스트 등록
  - [ ] 첫 sync 및 배포 확인

### Phase 2
- [ ] 멤버 프로필 + 통계 페이지 (vue-chartjs)
- [ ] GitHub OAuth
- [ ] Webhook
- [ ] Redis (Helm dependency: bitnami/redis)
- [ ] Nginx Ingress 전환 테스트

---

## 18. 보안

| 항목 | 처리 |
|------|------|
| GitHub PAT | k8s Secret, `helm install --set secret.githubToken=xxx` |
| ghcr.io 인증 | Actions의 `GITHUB_TOKEN` 자동 제공 |
| API 접근 | MVP는 read-only 공개, Phase 2에서 OAuth |
| Webhook | HMAC-SHA256 (`X-Hub-Signature-256`) |
| TLS | Cloudflare Edge에서 종단, 클러스터 내부 HTTP |
| CORS | 프론트엔드 origin만 허용 |
| Secret in git | `.gitignore`에 실제 시크릿 제외, SealedSecret 권장 |

---

## 19. 에이전틱 코딩 가이드

### 시작 프롬프트

```
이 PRD를 기반으로 ssafy15-data/study_dashboard 레포의 코드를 구현해줘.

구현 순서:
1. backend/ — FastAPI 앱 전체
   config.py → github_client.py → data_collector.py → cache.py
   → scheduler.py → models.py → routers/ → main.py → tests/
2. frontend/ — Vue 3 + Vite SPA
   main.ts → router → composables (vue-query) → components → views
   nginx.conf 포함
3. Dockerfile 2개 (backend: python-slim, frontend: node build → nginx:alpine)
4. charts/ps-dashboard/ — Helm 차트 전체
5. .github/workflows/ — CI + build-deploy (멀티 아키텍처 빌드)

핵심:
- GitHub API는 httpx async, rate limit 핸들링 필수
- parse_issue_numbers()는 PR body 첫 줄 "Issue: #100, #101"
- parse_issue_title()는 "[LeetCode 1003] 제목"
- 프론트엔드는 Vue 3 Composition API (<script setup>), Tailwind CSS
- 데이터 패칭은 @tanstack/vue-query의 useQuery
- SPA이므로 nginx.conf에 try_files fallback 필수
- Docker 이미지는 linux/amd64 + linux/arm64 멀티 아키텍처
- Helm values.yaml로 설정 관리, values-prod.yaml로 프로덕션 오버라이드
- ArgoCD가 charts/ 변경 감지하여 K3s 클러스터에 자동 배포
- Ingress className은 traefik 기본, nginx 전환 대비
- 외부 접속은 Cloudflare Tunnel (클러스터 내부 HTTP)
```

### 분할 구현 시 PR 단위
1. **PR #1**: 백엔드 뼈대 (config, github_client, data_collector, tests)
2. **PR #2**: 백엔드 라우터 + 캐시 + 스케줄러
3. **PR #3**: 프론트엔드 전체 (Vue 3 + Vite + Tailwind)
4. **PR #4**: Dockerfile (multi-arch) + Helm 차트
5. **PR #5**: GitHub Actions CI/CD
