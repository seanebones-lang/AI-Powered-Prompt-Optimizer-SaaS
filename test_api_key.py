#!/usr/bin/env python3
"""
Quick test script to verify xAI API key and configuration.
Run this to test your API key before deploying.
"""
import os
import sys
import httpx

def test_xai_api():
    """Test xAI API connectivity and key."""
    
    # Get API key from environment
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        print("❌ XAI_API_KEY not found in environment variables")
        print("\nSet it with: export XAI_API_KEY='your_key_here'")
        print("Or create a .env file with: XAI_API_KEY=your_key_here")
        sys.exit(1)
    
    # Configuration
    base_url = "https://api.x.ai/v1"
    model = os.getenv("XAI_MODEL", "grok-4-1-fast-reasoning")
    
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Say 'API test successful' if you can read this."}
        ],
        "max_tokens": 50
    }
    
    print("🧪 Testing xAI API...")
    print(f"   Model: {model}")
    print(f"   Endpoint: {url}")
    print(f"   API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '***'}")
    print()
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            
            print(f"📡 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print("✅ API Key is VALID!")
                print(f"   Response: {content}")
                print("\n🎉 Your API key is working correctly!")
                return True
            else:
                error_text = response.text
                print(f"❌ API Error ({response.status_code})")
                
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", error_text)
                    print(f"   Error: {error_msg}")
                except (ValueError, KeyError):
                    print(f"   Error: {error_text}")
                
                if response.status_code == 401:
                    print("\n💡 Possible issues:")
                    print("   - API key is incorrect or expired")
                    print("   - Regenerate key at https://console.x.ai/api-keys")
                elif response.status_code == 400:
                    print("\n💡 Possible issues:")
                    print("   - Model name might be wrong (should be grok-4-1-fast-reasoning)")
                    print("   - Check your XAI_MODEL environment variable")
                
                return False
                
    except httpx.TimeoutException:
        print("❌ Request timed out")
        print("   Check your internet connection")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Try to load from .env if python-dotenv is available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # Not required
    
    success = test_xai_api()
    sys.exit(0 if success else 1)
