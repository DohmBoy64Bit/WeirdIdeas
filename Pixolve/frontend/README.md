# Pixolve Frontend (Development)

This folder contains a minimal React frontend for Pixolve. It uses Vite for development and build.

Getting started:

1. Install dependencies

   ```bash
   cd frontend
   npm install
   ```

2. Start dev server (proxies API/WebSocket calls to http://localhost:8000)

   ```bash
   npm run dev
   ```

3. Open the site at http://localhost:5173 (Vite default)

Notes:
- The dev server is configured to proxy `/lobbies`, `/auth`, `/categories` and `/ws` to `http://localhost:8000`. If your backend runs on a different host or port, update `vite.config.js`.
- Production build: `npm run build` and then `npm run preview` to preview the built assets.
