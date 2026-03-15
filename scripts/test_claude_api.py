"""
Test Claude API Script
Verifies your API key works

RUN THIS FIRST:
python scripts/test_claude_api.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

def test_api():
    """Test Claude API connection"""
    print("🧪 Testing Claude API connection...")
    print("-" * 50)
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not found in .env file")
        print("📝 Create .env file with: ANTHROPIC_API_KEY=sk-ant-...")
        return False
    
    print(f"✅ API key found: {api_key[:20]}...")
    
    # Test API call
    try:
        print("🤖 Calling Claude API...")
        
        client = Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Say 'VerifAI is ready!' if you can read this."}
            ]
        )
        
        response_text = message.content[0].text
        print(f"✅ Claude response: {response_text}")
        print(f"📊 Tokens used: {message.usage.input_tokens} input, {message.usage.output_tokens} output")
        
        # Calculate cost
        cost = (message.usage.input_tokens / 1_000_000 * 0.25 + 
                message.usage.output_tokens / 1_000_000 * 1.25)
        print(f"💰 Cost: ${cost:.6f}")
        
        print("-" * 50)
        print("🎉 SUCCESS! Claude API is working!")
        print("✅ You're ready to run the demo")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("📝 Check your API key and internet connection")
        return False

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)