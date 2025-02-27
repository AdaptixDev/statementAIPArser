"""Script to run the FastAPI server."""

import uvicorn
import argparse

def main():
    """Run the FastAPI server."""
    parser = argparse.ArgumentParser(description="Run the FastAPI server.")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    uvicorn.run(
        "backend.src.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main() 