"""Quick health check script."""
import sys

def check_python_version():
    """Check if Python version is compatible."""
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 11):
        return f"Python {major}.{minor} found. Required: Python 3.11+"
    return f"Python {major}.{minor} - OK ✅"

def check_dependencies():
    """Check if required packages are installed."""
    imports = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('psycopg2', 'psycopg2-binary'),
        ('jinja2', 'Jinja2'),
    ]
    
    missing = []
    for module, name in imports:
        try:
            __import__(module)
        except ImportError:
            missing.append(name)
    
    if missing:
        return f"Missing dependencies: {', '.join(missing)}\nRun: pip install -r requirements.txt"
    return "All dependencies installed ✅"

def check_docker():
    """Check if Docker is available."""
    import subprocess
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        return result.stdout.strip()
    except FileNotFoundError:
        return "Docker not found. Install from https://docker.com"

def main():
    """Run all checks."""
    print("=" * 60)
    print("  Crew Scheduler - System Check")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version()),
        ("Dependencies", check_dependencies()),
        ("Docker", check_docker()),
    ]
    
    for name, result in checks:
        print(f"{name}:")
        print(f"  {result}")
        print()
    
    print("=" * 60)
    if "Missing dependencies" in checks[1][1] or "Docker not found" in checks[2][1]:
        print("❌ Some requirements are missing. Please install them.")
    else:
        print("✅ All systems ready! Run 'docker-compose up -d' to start.")
    print("=" * 60)

if __name__ == "__main__":
    main()