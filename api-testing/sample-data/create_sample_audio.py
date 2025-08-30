#!/usr/bin/env python3
"""
Create a sample WAV file for testing the voice consultation endpoint.
This creates a simple sine wave audio file that can be used for API testing.
"""

import wave
import numpy as np
import struct

def create_sample_wav(filename, duration=2.0, sample_rate=16000, frequency=440):
    """
    Create a simple sine wave WAV file for testing purposes.
    
    Args:
        filename: Output WAV file path
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        frequency: Sine wave frequency in Hz
    """
    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave_data = np.sin(2 * np.pi * frequency * t)
    
    # Convert to 16-bit integers
    wave_data = (wave_data * 32767).astype(np.int16)
    
    # Write WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data.tobytes())
    
    print(f"Created sample audio file: {filename}")
    print(f"Duration: {duration}s, Sample rate: {sample_rate}Hz")

if __name__ == "__main__":
    # Create sample audio files for different test scenarios
    create_sample_wav("sample_patient_symptoms.wav", duration=3.0, frequency=440)
    create_sample_wav("emergency_symptoms.wav", duration=4.0, frequency=523)  # Higher pitch for urgency
    create_sample_wav("routine_checkup.wav", duration=2.5, frequency=349)     # Lower pitch for calm
    
    print("\nSample audio files created for API testing:")
    print("- sample_patient_symptoms.wav: General symptoms")
    print("- emergency_symptoms.wav: Emergency scenario")
    print("- routine_checkup.wav: Routine consultation")
    print("\nThese files can be used with the Voice Consultation endpoint in Insomnia.")
