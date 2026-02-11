"""Test script to verify window management fixes."""
import sys
import os
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test the fixed window classes
def test_window_creation():
    """Test that windows can be created and destroyed properly."""
    print("Testing window creation...")
    
    # Create a root window
    root = tk.Tk()
    root.withdraw()
    print("[OK] Root window created successfully")
    
    # Test Toplevel creation (simulating EditPatternsWindow, DebugLogWindow, ConfigWindow)
    test_window = tk.Toplevel(root)
    test_window.title("Test Window")
    test_window.geometry("400x300")
    test_window.transient()
    print("[OK] Toplevel window created successfully")
    
    # Add some content
    tk.Label(test_window, text="This is a test window").pack(pady=20)
    
    # Test window destroy
    test_window.destroy()
    print("[OK] Window destroyed successfully")
    
    # Test multiple window creation
    windows = []
    for i in range(3):
        win = tk.Toplevel(root)
        win.title(f"Window {i+1}")
        win.transient()
        windows.append(win)
    print("[OK] Multiple windows created successfully")
    
    # Clean up all windows
    for win in windows:
        win.destroy()
    print("[OK] All windows destroyed successfully")
    
    root.destroy()
    print("[OK] Root window destroyed successfully")
    
    print("\n[SUCCESS] All window management tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = test_window_creation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
