# Run EduRAG for free: your PC + a free ngrok tunnel + Vercel

**How it works.** The frontend stays on Vercel (free). The backend runs on your Windows PC, the same way you ran it during testing. ngrok's free plan gives you a permanent HTTPS address that forwards to your PC, and the Vercel frontend calls that address.

**Honest limits.**

- The site works **only while your PC is on, awake, online, and the two windows from step 5 are open**. When it is off, the frontend loads but sign-in and chat show a connection error.
- ngrok's free plan allows **1 GB of transfer and 20,000 requests per month** (as documented by ngrok at the time of writing). That is plenty for a demo or a class project, not for many users.
- Your uploaded documents and the database live on your PC. Back them up.
- I could not test the ngrok tunnel itself (it needs your account). The frontend change for ngrok was tested with a simulated tunnel address, and the start script was not run on Windows. If chat answers appear all at once instead of streaming, that is the tunnel buffering. It still works.

## Step 1. Make sure the backend runs locally

You already did this when testing. In PowerShell:

```powershell
cd C:\Users\91880\OneDrive\Desktop\EduRAG\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/health. If it works, press `Ctrl+C`. Postgres must be running on your PC too (the same way as during testing).

## Step 2. Free ngrok account and install

1. Sign up at https://ngrok.com (free) and sign in to the dashboard.
2. Install ngrok. In PowerShell: `winget install ngrok.ngrok` (or `choco install ngrok` from an Administrator prompt). Open a **new** PowerShell window afterwards.
3. Dashboard > **Your Authtoken**, copy it and run: `ngrok config add-authtoken YOUR_TOKEN`. Do not share the token.
4. Dashboard > **Domains**. Your free **dev domain** is listed there, like `jumpy-red-mollusk.ngrok-free.app`. If none exists, click **Create domain**. Copy it.

## Step 3. Allow your Vercel site to call the backend (CORS)

Edit `backend\.env` and set (use your real Vercel address, no trailing slash):

```
CORS_ORIGINS=https://YOUR-APP.vercel.app,http://localhost:5500
ENVIRONMENT=production
```

Also check that `SECRET_KEY` in that file is a long random string, because the API will be reachable from the internet.

## Step 4. Point the Vercel frontend at your tunnel

Vercel > your project > **Settings** > **Environment Variables** > add:

- Name: `EDURAG_API_URL`
- Value: `https://jumpy-red-mollusk.ngrok-free.app` (your own domain)

Then **Deployments** > the latest one > **Redeploy**. (The address is baked in at build time, so the redeploy is required.) Make sure the Vercel project's root directory is `frontend`.

## Step 5. Start it

```powershell
cd C:\Users\91880\OneDrive\Desktop\EduRAG\deploy\laptop
powershell -ExecutionPolicy Bypass -File .\start-edurag.ps1 -Domain jumpy-red-mollusk.ngrok-free.app
```

Two windows open: the API and the tunnel. Open `https://YOUR-DOMAIN.ngrok-free.app/health` in a browser. If ngrok shows a warning page, click **Visit Site**. The app itself does not see that page.

## Step 6. Test

Open your Vercel address, then register or sign in, upload a document, chat, and generate notes. If sign-in fails, press F12 > Console. A message about CORS means step 3 has the wrong Vercel address. A network error means the windows are closed or the domain in step 4 is wrong.

## Keeping it online

- Windows: Settings > System > Power > set "Screen and sleep" to **Never** while plugged in, or the PC will sleep and take the site offline.
- After a restart, run step 5 again. The address stays the same, so Vercel needs no change.
- To go offline, close both windows.

## Later: a real always-on option

If you want it online without your PC, the Oracle Cloud "Always Free" server is the free route I found that fits this app. Ask me and I will turn the AWS kit in `deploy/aws` into a version for it.
