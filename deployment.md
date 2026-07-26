# Deployment Guide: Entropy Deceleration App

This guide outlines the step-by-step process to deploy the **Entropy Deceleration Dashboard** on a server using **Podman** and **Nginx** as a reverse proxy.

---

## Prerequisites

Before starting, ensure your target server has the following installed:
* **Podman** (version 4.0+)
* **Nginx**
* **Git** (to clone the codebase)

---

## 1. Project Directory & Database Setup

1. Clone or copy your project files to the server. Place them in a directory where your user has permissions (e.g., `~/entropy` or `/home/yourusername/entropy`):
   ```bash
   git clone <repository_url> ~/entropy
   cd ~/entropy
   ```

2. Initialize the SQLite database structure (this creates `entropy.db` with the correct tables):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   make init-db
   ```

---

## 2. Deploying with Podman

Podman will run the Streamlit dashboard in a container.

### Step A: Build the Container Image
Run the following command in the root directory (`~/entropy`):
```bash
make podman-build
```
*Alternative (manual command):*
```bash
podman build -t entropy-app -f Containerfile .
```

### Step B: Environment Variables Security
Create an `.env` file on your server to securely store your API Key. **Do not put this file in the Git repository.**
```bash
nano /secure/path/on/host/.env
```
Add your API key:
```ini
API_KEY="my-super-secret-key-123"
```

### Step C: Run the Containers (API & Dashboard)
You need to run both the FastAPI backend (for triggering the pipeline via API) and the Streamlit frontend. 

Run the Dashboard container (passing the `.env` file for security):
```bash
podman run -d \
  -p 8501:8501 \
  --name entropy-dashboard \
  --env-file /secure/path/on/host/.env \
  -v $(pwd)/entropy.db:/app/entropy.db:U \
  entropy-app \
  streamlit run app/ui/dashboard/main.py --server.port=8501 --server.address=0.0.0.0
```

Run the API container (using the same image and `.env` file, but a different command):
```bash
podman run -d \
  -p 8000:8000 \
  --name entropy-api \
  --env-file /secure/path/on/host/.env \
  -v $(pwd)/entropy.db:/app/entropy.db:U \
  entropy-app \
  uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

### Step C: Verify the Container Status
Make sure the container is running and didn't crash:
```bash
# Check if container is running:
podman ps

# Check the container logs for errors:
podman logs entropy-dashboard
```

---

## 3. Configuring Nginx as a Reverse Proxy

Since public traffic usually comes in on port `80` (HTTP) or `443` (HTTPS), we use Nginx to forward web requests to the running Streamlit container on port `8501`.

### Step A: Create the Nginx Configuration File
Create a new configuration file under the Nginx `sites-available` directory:
```bash
sudo nano /etc/nginx/sites-available/entropy
```

Paste the following configuration into the file (be sure to replace `your_server_ip_or_domain` with your actual IP address or domain):
```nginx
server {
    listen 80;
    server_name your_server_ip_or_domain; # E.g., 123.45.67.89 or dashboard.domain.com

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        
        # Streamlit requires WebSockets to work. These headers are CRITICAL:
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Standard proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
*Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).*

### Step B: Enable the Configuration
Enable the configuration by creating a symbolic link in the `sites-enabled` directory:
```bash
sudo ln -s /etc/nginx/sites-available/entropy /etc/nginx/sites-enabled/
```

### Step C: Disable the Default Nginx Page
To prevent conflicts with Nginx's default welcome page on port `80`, remove the default symbolic link:
```bash
sudo rm /etc/nginx/sites-enabled/default
```

### Step D: Test and Restart Nginx
Validate the configuration syntax:
```bash
sudo nginx -t
```
If the test reports `syntax is ok` and `test is successful`, restart Nginx:
```bash
sudo systemctl restart nginx
```

---

## 4. Keeping the Container Running After Logout (Linger & Auto-start)

Because Podman runs in **rootless mode**, systemd may terminate your container when you close your SSH connection. 

### Step A: Enable User Lingering
To keep the container running after you disconnect:
```bash
sudo loginctl enable-linger $USER
```
Verify lingering is active (should output `Linger=yes`):
```bash
loginctl show-user $USER | grep Linger
```

### Step B: Run as a systemd Service (Auto-start on Boot using Quadlets)
To ensure the containers automatically boot up if the server restarts, we use Podman's modern **Quadlet** manager.

1. Create the systemd config directory for containers:
   ```bash
   mkdir -p ~/.config/containers/systemd/
   ```

2. Create the Dashboard Quadlet file:
   ```bash
   nano ~/.config/containers/systemd/entropy-dashboard.container
   ```
   Paste the following:
   ```ini
   [Container]
   Image=localhost/entropy-app
   ContainerName=entropy-dashboard
   PublishPort=8501:8501
   Volume=%h/entropy-deceleration-app/entropy.db:/app/entropy.db:U
   EnvironmentFile=/secure/path/on/host/.env
   Exec=streamlit run app/ui/dashboard/main.py --server.port=8501 --server.address=0.0.0.0

   [Service]
   Restart=always

   [Install]
   WantedBy=default.target
   ```

3. Create the API Quadlet file:
   ```bash
   nano ~/.config/containers/systemd/entropy-api.container
   ```
   Paste the following:
   ```ini
   [Container]
   Image=localhost/entropy-app
   ContainerName=entropy-api
   PublishPort=8000:8000
   Volume=%h/entropy-deceleration-app/entropy.db:/app/entropy.db:U
   EnvironmentFile=/secure/path/on/host/.env
   Exec=uvicorn app.api.main:app --host 0.0.0.0 --port 8000

   [Service]
   Restart=always

   [Install]
   WantedBy=default.target
   ```
   *(Note: `%h` is a systemd variable representing your home directory, e.g., `/home/ubuntu`).*

4. Reload systemd and start the new services:
   ```bash
   systemctl --user daemon-reload
   systemctl --user start entropy-dashboard.service
   systemctl --user start entropy-api.service
   ```

---

## 5. Useful Operations & Troubleshooting

### Controlling the Service
When running as a systemd service, you should control the container using standard `systemctl` commands:
```bash
# Stop the app
systemctl --user stop entropy-dashboard.service

# Start the app
systemctl --user start entropy-dashboard.service

# Restart the app
systemctl --user restart entropy-dashboard.service

# Check systemd status
systemctl --user status entropy-dashboard.service
```

### Viewing Real-time App Logs
To monitor active user connections or stream errors live:
```bash
journalctl --user -xeu entropy-dashboard.service -f
```

### Database Permissions Error
If you receive a `Database is locked` or `Access Denied` error while writing/reading data in the container:
1. Ensure the SQLite file (`entropy.db`) on your host has read/write permissions for your user.
2. Confirm you ran the container with the `:U` flag (`Volume=%h/entropy/entropy.db:/app/entropy.db:U`).

### Triggering the Pipeline remotely
Now that the backend CLI is deprecated in favor of the API, you upload your data directly to the server remotely using `curl`:
```bash
curl -X POST "http://your_server_ip_or_domain:8000/api/v1/pipeline/import" \
     -H "X-API-Key: my-super-secret-key-123" \
     -F "file=@local_data.xlsx" \
     -F "dataset_type=research"

curl -X POST "http://your_server_ip_or_domain:8000/api/v1/pipeline/categorize" \
     -H "X-API-Key: my-super-secret-key-123" \
     -F "dataset_type=research"
```
