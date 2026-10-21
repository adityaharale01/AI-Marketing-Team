# AI Marketing Team — Angular frontend

## Run locally
1. Install Node.js compatible with the Angular version in `package.json`.
2. From this folder run `npm ci`.
3. Start FastAPI at `http://127.0.0.1:8000`.
4. Run `npm start` and open the local Angular URL shown in the terminal.

## Backend URL
Change `API_BASE_URL` in `src/app/core/services/api.service.ts` if FastAPI uses another host or port.

## What's included
- Existing landing, register, login, business setup and dashboard flows.
- Authenticated workspace route at `/workspace`.
- Product, sales and campaign list/search/create/update/delete flows.
- AI business performance, business knowledge indexing, RAG ask/search/add and AI test actions.
- Requests use the configured FastAPI backend and existing bearer-token interceptor. Responses and API validation errors are displayed in the UI.

For create/update forms, enter JSON with the exact field names required by your FastAPI Pydantic schemas. Use `/docs` on the running FastAPI server to verify request bodies. Endpoints under `/ai-predictions` were not given as exact paths/schemas in the supplied frontend archive, so they are not guessed in this build.
