"""
GitHub Project Management Tool - Main Application Module
"""
import sys
import os
import argparse
import traceback

# Add module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.cli import main as cli_main
from app.interactive_cli import main as interactive_main

# Define Colors class here since it's no longer imported
class Colors:
    RESET = "\033[0m"
    INFO = "\033[93m"  # Yellow for information messages
    SUCCESS = "\033[92m"  # Green for GitHub operations
    APP = "\033[94m"  # Blue for application operations
    ERROR = "\033[91m"  # Red for error messages
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def handle_exception(exc_type, exc_value, exc_traceback):
    """Custom exception handler to display errors in red."""
    # Print the error in red
    print(f"{Colors.ERROR}Error: {exc_value}{Colors.RESET}")
    
    # Print traceback for debugging
    print(f"{Colors.ERROR}Traceback:{Colors.RESET}")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    print(f"\n{Colors.INFO}If you're encountering authentication issues, please check your GitHub token.{Colors.RESET}")
    print(f"{Colors.INFO}For other issues, please report the problem with the above error details.{Colors.RESET}")


def main():
    """Main function."""
    # Set custom exception handler
    sys.excepthook = handle_exception
    
    parser = argparse.ArgumentParser(description="GitHub Project Management Tool")
    parser.add_argument("--interactive", "-i", action="store_true", help="Use interactive mode")
    
    # Parse arguments
    args, remaining_args = parser.parse_known_args()
    
    try:
        if args.interactive:
            # Start interactive mode
            interactive_main()
        else:
            # Start command line mode
            sys.argv = [sys.argv[0]] + remaining_args
            cli_main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.INFO}Program terminated by user.{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.ERROR}An unexpected error occurred: {str(e)}{Colors.RESET}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 