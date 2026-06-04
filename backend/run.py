"""EduAI Assistant — Flask Backend Entry Point.

Run with: python run.py
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print("  EduAI Assistant -- Backend API Server")
    print("  Address: http://localhost:5000")
    print("  Health: http://localhost:5000/api/health")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
