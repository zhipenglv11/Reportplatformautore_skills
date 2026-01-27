import uvicorn
import os
import sys

if __name__ == "__main__":
    # 确保当前目录在 path 中
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    print("Starting backend server...")
    try:
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    except Exception as e:
        print(f"Server failed to start: {e}")
        input("Press Enter to exit...")
