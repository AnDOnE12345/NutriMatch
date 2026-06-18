"""
NutriMatch - Personalized Supplement Recommendation Platform
Start script: launches backend API and seeds database.
"""
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def install_backend_deps():
    """Install Python backend dependencies."""
    req_file = os.path.join(BASE_DIR, "backend", "requirements.txt")
    print("📦 Installing backend dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], check=True)


def seed_database():
    """Seed the database with sample supplement data."""
    print("🌱 Seeding database...")
    subprocess.run([sys.executable, "-m", "backend.seed_data"], cwd=BASE_DIR, check=True)


def start_backend():
    """Start the FastAPI backend server."""
    print("🚀 Starting backend server at http://localhost:8000")
    print("📖 API docs available at http://localhost:8000/docs")
    print("💡 Run 'cd frontend && npm install && npm run dev' for the React frontend")
    print("-" * 50)
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"],
        cwd=BASE_DIR,
    )


if __name__ == "__main__":
    install_backend_deps()
    seed_database()
    start_backend()
