# RecSys Lab — Frontend

Next.js + Tailwind UI for the RecSys Lab FastAPI backend. Side-by-side comparison
and offline evaluation of six recommenders across MovieLens-100K and MIND-small.

## Run

```bash
npm install
npm run dev          # http://localhost:3000
```

## Configuration

Set the backend URL via `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`):

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Build

```bash
npm run lint
npm run build
npm start
```

## Pages

| Route | Purpose |
| --- | --- |
| `/` | Landing — domain cards, algorithm list, backend status |
| `/[domain]` | Domain overview — stats, algorithms, quick actions |
| `/[domain]/users` | User picker with searchable list and history panel |
| `/[domain]/compare?user_id=…` | Side-by-side top-K reclists across selected algorithms |
| `/[domain]/evaluation` | Precision / Recall / NDCG / Coverage / Diversity / Novelty |

`[domain]` is `movies` or `news`.
