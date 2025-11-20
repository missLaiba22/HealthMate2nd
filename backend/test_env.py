import os
print("Checking environment variables...")
print(f"OPENAI_API_KEY found: {'OPENAI_API_KEY' in os.environ}")
if 'OPENAI_API_KEY' in os.environ:
    # Print first few characters to verify it's there without exposing the full key
    print(f"Key starts with: {os.environ['OPENAI_API_KEY'][:5]}...")