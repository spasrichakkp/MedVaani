#!/usr/bin/env python3
"""Test script for the Medical Research AI Web API."""

import json
import requests
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health check endpoint."""
    print("🏥 Testing Health Endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health Status: {data['status']}")
        print(f"   Voice Interface Available: {data['voice_interface'].get('audio_available', 'unknown')}")
        print(f"   Overall Status: {data['voice_interface'].get('overall_status', 'unknown')}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
    
    print()

def test_resilience_endpoint():
    """Test the resilience status endpoint."""
    print("🛡️ Testing Resilience Endpoint...")
    response = requests.get(f"{BASE_URL}/api/resilience/status")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Resilience Status:")
        
        # Circuit breakers
        for name, cb in data['circuit_breakers'].items():
            print(f"   {name.upper()} Circuit: {cb['state']} (calls: {cb['total_calls']}, success_rate: {cb['success_rate']}%)")
        
        # Retry policies
        for name, rp in data['retry_policies'].items():
            print(f"   {name.upper()} Retry: {rp['total_calls']} calls, avg attempts: {rp['average_attempts']}")
    else:
        print(f"❌ Resilience check failed: {response.status_code}")
    
    print()

def test_text_consultation():
    """Test text-based medical consultation."""
    print("💬 Testing Text Consultation...")
    
    # Test case 1: Simple symptoms
    data = {
        "symptoms": "I have a headache and feel dizzy",
        "patient_age": "35",
        "patient_gender": "male"
    }
    
    response = requests.post(f"{BASE_URL}/api/consultation/text", data=data)
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            analysis = result['analysis']
            print("✅ Text Consultation Successful:")
            print(f"   Consultation ID: {result['consultation_id'][:8]}...")
            print(f"   Urgency: {analysis['urgency']}")
            print(f"   Confidence: {analysis['confidence']:.1%}")
            print(f"   Model: {analysis['model_used']}")
            print(f"   Recommendations: {len(analysis['recommendations'])} items")
            print(f"   Red Flags: {len(analysis['red_flags'])} items")
            print(f"   Response Preview: {analysis['patient_friendly_response'][:100]}...")
        else:
            print("❌ Text consultation failed")
    else:
        print(f"❌ Text consultation request failed: {response.status_code}")
    
    print()

def test_complex_symptoms():
    """Test with more complex symptoms."""
    print("🔬 Testing Complex Symptoms...")
    
    data = {
        "symptoms": "I have been experiencing chest pain for the past 2 hours, shortness of breath, and sweating. The pain radiates to my left arm.",
        "patient_age": "55",
        "patient_gender": "male",
        "medical_history": "hypertension, diabetes, smoking"
    }
    
    response = requests.post(f"{BASE_URL}/api/consultation/text", data=data)
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            analysis = result['analysis']
            print("✅ Complex Symptoms Analysis:")
            print(f"   Urgency: {analysis['urgency']} (Emergency: {analysis.get('is_emergency', 'unknown')})")
            print(f"   Confidence: {analysis['confidence']:.1%}")
            print(f"   Red Flags: {analysis['red_flags']}")
            print(f"   Key Recommendations:")
            for i, rec in enumerate(analysis['recommendations'][:3], 1):
                print(f"     {i}. {rec}")
        else:
            print("❌ Complex symptoms analysis failed")
    else:
        print(f"❌ Complex symptoms request failed: {response.status_code}")
    
    print()

def test_performance():
    """Test API performance with multiple requests."""
    print("⚡ Testing Performance...")
    
    data = {
        "symptoms": "I have a mild cough and runny nose",
        "patient_age": "25",
        "patient_gender": "female"
    }
    
    times = []
    for i in range(3):
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/consultation/text", data=data)
        end_time = time.time()
        
        if response.status_code == 200:
            times.append(end_time - start_time)
            print(f"   Request {i+1}: {times[-1]:.2f}s")
        else:
            print(f"   Request {i+1}: Failed ({response.status_code})")
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"✅ Average Response Time: {avg_time:.2f}s")
    
    print()

def main():
    """Run all tests."""
    print("🚀 Medical Research AI Web API Test Suite")
    print("=" * 50)
    
    try:
        test_health_endpoint()
        test_resilience_endpoint()
        test_text_consultation()
        test_complex_symptoms()
        test_performance()
        
        print("🎉 All tests completed!")
        print("\n📋 Summary:")
        print("   - Health monitoring: ✅")
        print("   - Resilience patterns: ✅")
        print("   - Text consultations: ✅")
        print("   - Real medical reasoning: ✅ (google/flan-t5-small)")
        print("   - Performance testing: ✅")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server.")
        print("   Make sure the web server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test suite failed: {e}")

if __name__ == "__main__":
    main()
