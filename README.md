# Entropy Deceleration App

A dashboard and ML pipeline for analyzing research and community service projects that implement entropy deceleration.

## Requirements

- Python 3.11+ (or running via Podman)
- Podman (for containerized deployment)

## Local Setup

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

2. Seed the configurations and database:
   ```bash
   make init-db
   make seed-config
   ```

3. Run the categorization pipeline:
   ```bash
   make categorize
   ```

4. Launch the local Streamlit dashboard:
   ```bash
   make run
   ```

---

## Container Deployment with Podman

To build and run the application inside a container using Podman, navigate to the project root directory and use the helper `Makefile` targets:

### 1. Build the Podman Image
```bash
make podman-build
```
*Manual command:*
```bash
podman build -t entropy-app -f Containerfile .
```

### 2. Run the Podman Container
```bash
make podman-run
```
*Manual command:*
```bash
podman run -d -p 8501:8501 --name entropy-dashboard -v $(pwd)/entropy.db:/app/entropy.db:U entropy-app
```
> [!IMPORTANT]
> The `:U` flag in the volume mount (`-v ...:U`) is crucial for **rootless Podman**. It instructs Podman to automatically map the ownership of the host database file (`entropy.db`) to the container user context, preventing SQLite database permission errors.

### 3. Stop and Remove the Container
```bash
make podman-stop
```
*Manual command:*
```bash
podman stop entropy-dashboard && podman rm entropy-dashboard
```
