# 测试脚本
import sys
sys.path.insert(0, r"C:\Users\Administrator\.openclaw\workspace\twitter_gui")

try:
    import gui
    print("导入成功")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
