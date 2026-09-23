# EduRAG frontend

Static site (no build step, no framework) served by Vercel.

```
index.html            landing page
pages/*.html          app pages (thin HTML shells; JS renders them)
css/                  tokens -> base -> components -> shell -> features (+ auth, landing)
js/config.js          API URL + client-side limits
js/core/              api client, auth, shell (nav/topbar), ui helpers, safe markdown renderer
js/pages/             one module per page
vendor/               self-hosted Inter + Bootstrap Icons (no third-party requests)
```

## Run locally

```bash
cd frontend
python -m http.server 5500      # or: npx serve .
# open http://localhost:5500
```

On `localhost` the app calls `http://localhost:8000`. To point at another backend while developing:
`localStorage.setItem("edurag_api_url", "http://localhost:9000")`.

## Deploy (Vercel)

Import the repo with **Root Directory = `frontend`**. `vercel.json` sets the build command and security headers.
Optionally set the environment variable `EDURAG_API_URL` (e.g. `https://your-backend.up.railway.app`) —
it is baked into `js/config.js` at build time. If unset, the default in `js/config.js` is used.

Remember to add your Vercel URL to the backend's `CORS_ORIGINS`.
