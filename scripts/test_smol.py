"""smolagents import test"""
import sys
sys.path.insert(0, '/home/administrator/dijital-varlik')

try:
    from smolagents import CodeAgent, LiteLLMModel
    print("smolagents import OK")
    print(f"  CodeAgent: {CodeAgent}")
    print(f"  LiteLLMModel: {LiteLLMModel}")
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
