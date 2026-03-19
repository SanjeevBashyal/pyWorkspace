import os
import sys

def open_explorer():
    """
    Callback function to execute when the hotkey is pressed.
    Opens the default Windows Explorer.
    """
    try:
        # Opens explorer at the default 'My Computer' / 'Quick Access' location
        os.startfile('explorer.exe')
    except Exception as e:
        print(f"Error opening explorer: {e}")

def main():
    try:
        import keyboard
    except ImportError:
        print("The 'keyboard' library is required.")
        print("Please install it running: pip install keyboard")
        sys.exit(1)

    # 1. Register the hotkey combinations
    # You can bind the hotkey to the function created above.
    keyboard.add_hotkey('ctrl+shift+e', open_explorer)
    
    # Example: You can bind other shortcuts for pyworkspace class methods
    # e.g., keyboard.add_hotkey('ctrl+shift+w', session.resume)

    # 2. Block the script from exiting and run indefinitely
    # The script will listen in the background until 'ctrl+shift+q' is pressed.
    keyboard.wait('ctrl+shift+q')

if __name__ == '__main__':
    main()
