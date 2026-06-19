# 🚀 FinQorp Quick Start Guide

## One-Command Startup (Recommended)

### Using the startup script
```bash
./start.sh
```

This will:
- ✅ Start both backend and frontend servers automatically
- ✅ Run them in a tmux session for easy management
- ✅ Keep both servers running in the background

### Managing the servers

**View running servers:**
```bash
tmux attach -t finqorp
```

**Detach from tmux (keep servers running):**
Press `Ctrl+B` then `D`

**Stop all servers:**
```bash
tmux kill-session -t finqorp
```

---

## Manual Startup (Alternative)

If you prefer to run servers manually:

### Terminal 1: Backend
```bash
cd /Users/adnanquraishee/Downloads/finqorp
source .venv/bin/activate
uvicorn api:app --reload --port 8000
```

### Terminal 2: Frontend
```bash
cd /Users/adnanquraishee/Downloads/finqorp/frontend
npm run dev
```

---

## Access Points

- 🌐 **Frontend:** http://localhost:5173
- 🔧 **Backend API:** http://localhost:8000
- 📚 **API Docs:** http://localhost:8000/docs

---

## Troubleshooting

### Blank White Screen
If you see a blank screen in the frontend:
1. Stop the frontend server (Ctrl+C or `pkill -f vite`)
2. Restart it: `cd frontend && npm run dev`
3. Hard refresh the browser (Cmd+Shift+R)

### Port Already in Use
If port 8000 or 5173 is in use:
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

### Backend Not Responding
1. Ensure you've activated the virtual environment: `source .venv/bin/activate`
2. Check if all dependencies are installed: `pip install -r requirements.txt`
3. Verify Python version: `python --version` (should be 3.11+)

---

## First Time Setup

If this is your first time running FinQorp:

1. **Install backend dependencies:**
   ```bash
   cd /Users/adnanquraishee/Downloads/finqorp
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   # Set Google Gemini API key for AI insights
   export GOOGLE_API_KEY="your-api-key-here"
   ```

4. **Run the startup script:**
   ```bash
   ./start.sh
   ```
