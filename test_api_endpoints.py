#!/usr/bin/env python3
"""
Test script to verify all API endpoints are working correctly
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health endpoint."""
    print("🏥 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Status: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_text_consultation():
    """Test the text consultation endpoint."""
    print("\n💬 Testing Text Consultation...")
    try:
        data = {
            "symptoms": "I have severe chest pain radiating to my left arm, shortness of breath, and I'm sweating profusely",
            "patient_age": "55",
            "patient_gender": "male",
            "medical_history": "hypertension,diabetes"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/consultation/text",
            data=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Text consultation successful!")
            print(f"   Urgency: {result['analysis']['urgency']}")
            print(f"   Model: {result['analysis']['model_used']}")
            print(f"   Recommendations: {len(result['analysis']['recommendations'])}")
            print(f"   Red Flags: {len(result['analysis']['red_flags'])}")
            return True
        else:
            print(f"❌ Text consultation failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Text consultation failed: {e}")
        return False

def test_voice_consultation():
    """Test the voice consultation endpoint."""
    print("\n🎤 Testing Voice Consultation...")
    try:
        # Create a dummy audio file for testing
        dummy_audio = b"dummy audio content for testing"
        
        files = {
            'audio_file': ('test.wav', dummy_audio, 'audio/wav')
        }
        data = {
            "patient_age": "45",
            "patient_gender": "female",
            "medical_history": "none"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/consultation/voice",
            files=files,
            data=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Voice consultation successful!")
            print(f"   Consultation ID: {result.get('consultation_id', 'N/A')}")
            return True
        else:
            print(f"❌ Voice consultation failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Voice consultation failed: {e}")
        return False

def test_resilience_status():
    """Test the resilience status endpoint."""
    print("\n🛡️ Testing Resilience Status...")
    try:
        response = requests.get(f"{BASE_URL}/api/resilience/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Resilience status retrieved successfully!")
            print(f"   Circuit Breakers: {len(data.get('circuit_breakers', {}))}")
            print(f"   Retry Policies: {len(data.get('retry_policies', {}))}")
            return True
        else:
            print(f"❌ Resilience status failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Resilience status failed: {e}")
        return False

def main():
    """Run all API tests."""
    print("🚀 Medical Research AI API Test Suite")
    print("=" * 50)
    
    # Test if server is running
    if not test_health_endpoint():
        print("\n❌ Server is not running. Please start the web server first.")
        print("   Run: cd web && uvicorn main:app --reload")
        return
    
    # Run all tests
    tests = [
        test_text_consultation,
        test_voice_consultation,
        test_resilience_status
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The API is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
