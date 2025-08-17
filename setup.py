#!/usr/bin/env python3
"""
Setup script for Medium List Scraper

This script handles the installation of dependencies and initialization
of the environment for the Medium scraping project.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description=""):
    """Run a shell command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def create_directories():
    """Create necessary directories"""
    print("📁 Creating output directories...")
    
    directories = ["output", "output/logs", "output/checkpoints", "output/data"]
    
    for dir_name in directories:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
        print(f"   Created: {dir_name}")
    
    print("✅ Directories created successfully")
    return True

def install_python_dependencies():
    """Install Python packages from requirements.txt"""
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python dependencies"
    )

def install_playwright_browsers():
    """Install Playwright browser binaries"""
    return run_command(
        f"{sys.executable} -m playwright install chromium",
        "Installing Playwright Chromium browser"
    )

def create_env_file():
    """Create .env file with default configuration"""
    env_path = Path(".env")
    
    if env_path.exists():
        print("ℹ️  .env file already exists, skipping creation")
        return True
    
    print("📝 Creating .env configuration file...")
    
    env_content = """# Medium Scraper Configuration

# Browser settings
HEADLESS=false
BROWSER_TIMEOUT=30000

# Rate limiting
MAX_REQUESTS_PER_HOUR=400
DELAY_MIN=1.5
DELAY_MAX=2.5

# Output settings
OUTPUT_DIR=output
LOG_LEVEL=INFO

# Scraping settings
SAVE_INTERVAL=50
CHECKPOINT_INTERVAL=300

# Optional: Proxy settings (uncomment if needed)
# ENABLE_PROXY=false
# PROXY_LIST=

# Optional: Custom selectors (uncomment if Medium changes their layout)
# CUSTOM_SELECTORS=false
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {str(e)}")
        return False

def verify_installation():
    """Verify that all components are installed correctly"""
    print("🔍 Verifying installation...")
    
    # Test imports
    test_imports = [
        ("playwright", "playwright.async_api"),
        ("pandas", "pandas"),
        ("aiofiles", "aiofiles"),
        ("fake_useragent", "fake_useragent"),
        ("colorlog", "colorlog"),
        ("tqdm", "tqdm"),
        ("dotenv", "dotenv")
    ]
    
    failed_imports = []
    
    for module_name, import_name in test_imports:
        try:
            __import__(import_name)
            print(f"   ✅ {module_name}")
        except ImportError:
            print(f"   ❌ {module_name}")
            failed_imports.append(module_name)
    
    if failed_imports:
        print(f"❌ Failed to import: {', '.join(failed_imports)}")
        return False
    
    print("✅ All modules imported successfully")
    return True

def show_usage_instructions():
    """Display usage instructions"""
    print("\n" + "="*60)
    print("🎉 Setup completed successfully!")
    print("="*60)
    print("\n📋 Quick Start Instructions:")
    print("\n1. Run the scraper:")
    print("   python medium_scraper.py")
    print("\n2. Or use the interactive mode:")
    print("   python -c \"import asyncio; from medium_scraper import main; asyncio.run(main())\"")
    print("\n3. Monitor progress:")
    print("   - Check 'output/' directory for saved data")
    print("   - Check 'output/logs/' for detailed logs")
    print("   - Scraper saves progress every 50 articles")
    print("\n4. Resume interrupted scraping:")
    print("   - The scraper automatically resumes from checkpoints")
    print("   - Delete 'output/checkpoint.json' to start fresh")
    print("\n📊 Expected Results:")
    print("   - Target: 2600+ articles from the coding list")
    print("   - Output: JSON and CSV files with article data")
    print("   - Rate limited: ~400 requests per hour")
    print("   - Estimated time: 6-8 hours for full extraction")
    print("\n⚙️  Configuration:")
    print("   - Edit 'config.py' for advanced settings")
    print("   - Edit '.env' for environment variables")
    print("   - Check 'output/logs/' for debugging")
    print("\n🛑 To stop scraping:")
    print("   - Press Ctrl+C to interrupt gracefully")
    print("   - Progress is automatically saved")
    print("="*60)

def main():
    """Main setup function"""
    print("🚀 Medium List Scraper Setup")
    print("="*40)
    
    setup_steps = [
        ("Checking Python version", check_python_version),
        ("Creating directories", create_directories),
        ("Installing Python dependencies", install_python_dependencies),
        ("Installing Playwright browsers", install_playwright_browsers),
        ("Creating configuration file", create_env_file),
        ("Verifying installation", verify_installation)
    ]
    
    failed_steps = []
    
    for step_name, step_function in setup_steps:
        if not step_function():
            failed_steps.append(step_name)
    
    if failed_steps:
        print(f"\n❌ Setup failed at: {', '.join(failed_steps)}")
        print("Please fix the errors and run setup again.")
        sys.exit(1)
    
    show_usage_instructions()

if __name__ == "__main__":
    main()