#!/usr/bin/env python3
"""
Validation script for the Medical Research AI Insomnia Collection.
Tests all endpoints to ensure they're working correctly before using the collection.
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health check endpoint."""
    print("🏥 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check successful - Status: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"   ❌ Health check failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False

def test_resilience_endpoint():
    """Test the resilience status endpoint."""
    print("🔄 Testing Resilience Status...")
    try:
        response = requests.get(f"{BASE_URL}/api/resilience/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Resilience status successful")
            return True
        else:
            print(f"   ❌ Resilience status failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Resilience status error: {e}")
        return False

def test_text_consultation():
    """Test the text consultation endpoint."""
    print("💬 Testing Text Consultation...")
    try:
        data = {
            "symptoms": "I have a mild headache and runny nose for 2 days",
            "patient_age": "28",
            "patient_gender": "female",
            "medical_history": "seasonal_allergies"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/consultation/text",
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                model_used = result.get("analysis", {}).get("model_used", "unknown")
                urgency = result.get("analysis", {}).get("urgency", "unknown")
                print(f"   ✅ Text consultation successful - Model: {model_used}, Urgency: {urgency}")
                return True
            else:
                print(f"   ❌ Text consultation failed - Response indicates failure")
                return False
        else:
            print(f"   ❌ Text consultation failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Text consultation error: {e}")
        return False

def test_voice_consultation():
    """Test the voice consultation endpoint with sample audio."""
    print("🎤 Testing Voice Consultation...")
    try:
        # Check if sample audio file exists
        audio_file = Path("sample-data/sample_patient_symptoms.wav")
        if not audio_file.exists():
            print(f"   ⚠️  Sample audio file not found: {audio_file}")
            print("   ℹ️  Run 'python sample-data/create_sample_audio.py' to create test files")
            return False
        
        with open(audio_file, 'rb') as f:
            files = {'audio_file': ('test.wav', f, 'audio/wav')}
            data = {
                'patient_age': '30',
                'patient_gender': 'female',
                'medical_history': 'none'
            }
            
            response = requests.post(
                f"{BASE_URL}/api/consultation/voice",
                files=files,
                data=data,
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                consultation_id = result.get("consultation_id", "unknown")
                has_audio = result.get("has_audio_response", False)
                print(f"   ✅ Voice consultation successful - ID: {consultation_id[:12]}..., Audio: {has_audio}")
                return True
            else:
                print(f"   ❌ Voice consultation failed - Response indicates failure")
                return False
        else:
            print(f"   ❌ Voice consultation failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Voice consultation error: {e}")
        return False

def validate_collection():
    """Run all validation tests."""
    print("🔍 Validating Medical Research AI Collection...")
    print(f"📍 Testing against: {BASE_URL}")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Resilience Status", test_resilience_endpoint),
        ("Text Consultation", test_text_consultation),
        ("Voice Consultation", test_voice_consultation),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
        time.sleep(1)  # Brief pause between tests
    
    print("=" * 50)
    print("📊 Validation Results:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Summary: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! The Insomnia collection is ready to use.")
        print("\n📋 Next steps:")
        print("   1. Import 'insomnia-collections/Medical_Research_AI_Collection.json' into Insomnia")
        print("   2. Start testing with the pre-configured endpoints")
        print("   3. Use the sample scenarios in 'sample-data/test_scenarios.json'")
    else:
        print("⚠️  Some tests failed. Please check the server status and try again.")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure the server is running: uvicorn main:app --host 0.0.0.0 --port 8000")
        print("   2. Check server logs for errors")
        print("   3. Verify environment variables are set correctly")
    
    return passed == len(tests)

if __name__ == "__main__":
    validate_collection()
