#!/usr/bin/env python
"""
GitHub Project Sync Tool başlatma betiği.
"""
import sys
import os

# Add module path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import main


if __name__ == "__main__":
    # Komut satırı argümanlarına "--interactive" ekle
    if "--interactive" not in sys.argv and "-i" not in sys.argv:
        sys.argv.append("--interactive")
    
    # Ana fonksiyonu çağır
    main() 