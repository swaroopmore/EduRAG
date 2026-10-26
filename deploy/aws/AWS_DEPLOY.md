# Deploying EduRAG on AWS (one EC2 server)

**What you will build**

| Piece | AWS service | Notes |
|---|---|---|
| API (FastAPI + AI models) | **EC2** `t3.medium`, Docker | 4 GB RAM is the practical minimum for the embedding + reranker models |
| HTTPS | **Caddy** container on the same server | Gets and renews the certificate automatically |
| Database | **RDS PostgreSQL** | Automatic daily backups |
| Uploads + vector index | **EBS** disk mounted at `/data` | Survives reboots and redeploys |
| Frontend | **S3 + CloudFront** | HTTPS, fast, cheap |

Estimated cost is roughly $45-60 per month in total, mostly EC2 and RDS. Check the AWS pricing pages for your region. You can stop the EC2 instance and RDS database when you are not using them.

These files were checked for syntax here, but I could not run them on a real AWS account. If a step fails, send me the step number and the exact message.

Pick a region close to your users (for example `ap-south-1` Mumbai) and use the **same region for every step**.

---

## Part 1 - Security groups (AWS firewalls)

EC2 console > **Security Groups** > **Create security group** (default VPC), twice:

1. `edurag-web`
   - Inbound: HTTP 80 from `0.0.0.0/0`, HTTPS 443 from `0.0.0.0/0`, SSH 22 from **My IP**.
2. `edurag-db`
   - Inbound: PostgreSQL 5432, source = the `edurag-web` security group (not an IP address).

## Part 2 - Database (RDS)

RDS > **Create database**:

- Standard create > **PostgreSQL** (version 16).
- Template: **Dev/Test** (or Free tier if offered).
- DB instance identifier: `edurag-db`. Master username: `edurag`.
- Master password: use **letters and digits only**, and save it.
- Instance: `db.t4g.micro`. Storage: 20 GB gp3.
- Connectivity: default VPC, **Public access: No**, security group `edurag-db`.
- Additional configuration: **Initial database name = `edurag`**, backup retention 7 days.

When it is available, copy the **Endpoint** (like `edurag-db.abc123.ap-south-1.rds.amazonaws.com`).

## Part 3 - Server (EC2)

EC2 > **Launch instance**:

- Name: `edurag-server`. Image: **Amazon Linux 2023**. Type: **t3.medium**.
- Key pair: create a new one and keep the `.pem` file safe.
- Network: security group `edurag-web`.
- Storage: root volume **30 GiB gp3**, then **Add new volume** of **20 GiB gp3** (this is the data disk for uploads and the vector index).
- Advanced details > **Termination protection: Enable**.

Then EC2 > **Elastic IPs** > **Allocate** > **Associate** with `edurag-server`. This fixed IP survives restarts.

## Part 4 - A web address for the API

The API needs an HTTPS hostname. Choose one:

- **You own a domain:** add an `A` record, for example `api.yourdomain.com`, pointing to the Elastic IP.
- **No domain:** use `IP-WITH-DASHES.sslip.io`. For example, for `3.90.12.34` the name is `3-90-12-34.sslip.io`, and it resolves to that IP automatically. Free, no signup.

## Part 5 - Set up the server

Connect from PowerShell on your computer (Windows 10/11 has `ssh` built in). Use the `.pem` key from Part 3 and the Elastic IP:

```powershell
icacls "C:\path\to\edurag-key.pem" /inheritance:r /grant:r "$($env:USERNAME):(R)"
ssh -i "C:\path\to\edurag-key.pem" ec2-user@YOUR_ELASTIC_IP
```

(The `icacls` line only restricts who can read the key file. SSH refuses keys that other users can read.) If the connection times out, your home IP changed: edit the SSH rule in `edurag-web` and set it to **My IP** again.

Once connected, run:

```bash
sudo dnf install -y git
git clone -b upgrade-edurag https://github.com/swaroopmore/EduRAG.git
cd EduRAG/deploy/aws
lsblk
```

If the repository is private, GitHub will ask for a username and a personal access token instead of a password. Use `main` instead of `upgrade-edurag` once you have merged.

`lsblk` lists disks. The **20 GB disk with no mount point** (usually `nvme1n1`) is the data disk. Run:

```bash
bash ec2-bootstrap.sh /dev/nvme1n1
```

The script installs Docker, formats the data disk **only if it is empty**, mounts it at `/data`, and adds swap. When it finishes, type `exit` and connect again with SSH (so the Docker permission applies).

## Part 6 - Configure and start

```bash
cd ~/EduRAG/deploy/aws
cp .env.prod.example .env.prod
nano .env.prod
```

Fill in:

- `API_DOMAIN`: from Part 4.
- `DATABASE_URL`: `postgresql://edurag:YOUR_DB_PASSWORD@YOUR_RDS_ENDPOINT:5432/edurag?sslmode=require`
- `SECRET_KEY`: run `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` and paste the result.
- `GEMINI_API_KEY`: your key.
- `CORS_ORIGINS`: leave for now (Part 8).

Save with `Ctrl+O`, `Enter`, `Ctrl+X`. Then:

```bash
bash deploy.sh upgrade-edurag
```

The first build takes 10-20 minutes (it downloads the AI libraries and models). When it prints `API is up`, open `https://YOUR_API_DOMAIN/health` in your browser.

## Part 7 - Frontend (S3 + CloudFront)

**7a. Point the frontend at your API.** On your computer, in the `frontend` folder (PowerShell):

```powershell
$env:EDURAG_API_URL = "https://YOUR_API_DOMAIN"
node scripts/generate-config.mjs
```

This edits `frontend/js/config.js`. Do not commit that change if you also deploy the same code on Vercel. Run `git checkout frontend/js/config.js` afterwards.

**7b. Create the bucket.** S3 > **Create bucket**, any unique name, **Block all public access = ON**.

**7c. Upload.** Open the bucket > **Upload** > add the contents of the `frontend` folder (`index.html`, `pages`, `css`, `js`, `vendor`, `icons`, `manifest.webmanifest`). Do **not** upload `scripts`, `vercel.json` or `README.md`. If you use the AWS CLI instead:
`aws s3 sync . s3://YOUR_BUCKET --exclude "scripts/*" --exclude "vercel.json" --exclude "README.md"`

**7d. Create the CloudFront distribution.**

- Origin: your S3 bucket. Origin access: **Origin access control (OAC)**, create a new one, and when prompted **copy the bucket policy** into the bucket's Permissions > Bucket policy.
- Viewer protocol: **Redirect HTTP to HTTPS**. Default root object: `index.html`.
- Cache policy: `CachingOptimized`.
- Response headers policy: create a custom policy with these headers (the same as `vercel.json`):
  - `Content-Security-Policy`: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self' https:; manifest-src 'self'; frame-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'`
  - `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`

When it is deployed, copy the **Distribution domain name** (`dxxxxxxxx.cloudfront.net`). Whenever you re-upload frontend files, create an **Invalidation** with the path `/*`.

## Part 8 - Let the frontend call the API (CORS)

On the server:

```bash
cd ~/EduRAG/deploy/aws
nano .env.prod          # CORS_ORIGINS=https://dxxxxxxxx.cloudfront.net   (no trailing slash)
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

## Part 9 - Test

Open `https://dxxxxxxxx.cloudfront.net` and check:

1. Register and sign in.
2. Create a subject and upload a PDF (status should reach Ready).
3. Ask a question in AI Chat (the answer should stream in, with sources).
4. Generate Notes, Flashcards, a Quiz and a Study Plan.
5. **Persistence test:** on the server run `bash deploy.sh upgrade-edurag` again, then ask about the same document. It must still answer.

## Part 10 - Your existing data (optional)

The new AWS site starts **empty**. Two options:

- Start fresh and re-upload your documents (simplest).
- Move the data: `pg_dump` your Railway database and restore it into RDS with `psql`, then copy the Railway `uploads` and `vector_db` folders into `/data/edurag/`. After that, click **Re-index** on each document.

## Running it

| Task | Command (in `~/EduRAG/deploy/aws`) |
|---|---|
| See API logs | `docker compose -f docker-compose.prod.yml logs -f --tail=100 backend` |
| Update to the latest code | `bash deploy.sh main` |
| Restart | `docker compose -f docker-compose.prod.yml --env-file .env.prod restart` |
| Backup uploads + index | `bash backup.sh` (schedule it with `crontab -e`) |

Also turn on **EBS snapshots** for the data disk (EC2 > Lifecycle Manager), and set a **billing alarm** in AWS Billing.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `/health` times out | Security group `edurag-web` is missing 80/443, or the DNS name does not point to the Elastic IP |
| Browser says certificate error | DNS not ready yet. Wait a few minutes and check `docker compose ... logs caddy` |
| API restarts in a loop, logs mention the database | Wrong `DATABASE_URL` (password, endpoint, missing `?sslmode=require`) or `edurag-db` does not allow `edurag-web` |
| Login fails with CORS error in the browser console | `CORS_ORIGINS` does not exactly match the CloudFront URL |
| Build is killed / "Killed" | Server too small. Use `t3.medium` or larger |
| Old page after a frontend update | Create a CloudFront invalidation for `/*` |
