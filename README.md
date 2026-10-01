# TripGenie AI

An AI-powered travel planner that coordinates specialized agents to create trip plans from a travel request.

## Features

- Planner, Research, Budget, Itinerary, and Validation agents coordinated by a supervisor
- Gemini-first provider flow with Groq fallback and bounded retries
- Server-sent agent progress events
- Destination recommendations with live-verification caveats
- Budget breakdown and day-by-day itinerary
- Client-generated PDF travel plan with embedded Unicode fonts

Research recommendations are AI-generated. Current prices, schedules, availability, weather, and bookings require independent live verification; this repository does not currently integrate an external web research source.

## Stack

- React and Vite frontend
- FastAPI backend
- Python agent orchestration
- Gemini and Groq providers
- SSE for agent progress
- jsPDF for client-side PDF export

## Local Setup

Requirements: Python, Node.js, and npm.

1. Create a local backend environment file from the example:

   ```powershell
   Copy-Item backend/.env.example backend/.env
   ```

2. Add provider keys to `backend/.env`. Never commit this file.

3. Install backend dependencies and start FastAPI from the project root:

   ```powershell
   python -m pip install -r backend/requirements.txt
   python -m uvicorn backend.main:app --reload --app-dir backend --env-file backend/.env
   ```

4. In a second terminal, install and start the frontend:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

5. Open the Vite URL printed by the frontend server. The local frontend API URL currently targets `http://127.0.0.1:8000`.

## Verification

From the project root:

```powershell
python -m compileall backend
```

From `frontend/`:

```powershell
npm run build
```
