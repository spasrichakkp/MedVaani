#!/usr/bin/env python3
"""
Test script for voice interface functionality
"""

import sys
from pathlib import Path

# Add medbench to path
sys.path.append(str(Path(__file__).parent))

from medbench.voice_interface import VoiceInterface, VoiceConfig, create_voice_interface
from rich.console import Console

console = Console()

def test_voice_interface():
    """Test the voice interface components"""
    
    console.print("[bold blue]🧪 Testing Voice Interface[/bold blue]")
    console.print("=" * 50)
    
    # Create voice interface
    console.print("\n[yellow]1. Creating voice interface...[/yellow]")
    voice_config = VoiceConfig(
        tts_model="microsoft/speecht5_tts",
        asr_model="openai/whisper-small",
        sample_rate=16000
    )
    
    voice_interface = create_voice_interface(voice_config)
    if not voice_interface:
        console.print("[red]❌ Failed to create voice interface[/red]")
        return False
    
    console.print("[green]✅ Voice interface created[/green]")
    
    # Test TTS model loading
    console.print("\n[yellow]2. Loading TTS models...[/yellow]")
    tts_success = voice_interface.load_tts_models()
    if tts_success:
        console.print("[green]✅ TTS models loaded successfully[/green]")
    else:
        console.print("[red]❌ Failed to load TTS models[/red]")
    
    # Test ASR model loading
    console.print("\n[yellow]3. Loading ASR models...[/yellow]")
    asr_success = voice_interface.load_asr_models()
    if asr_success:
        console.print("[green]✅ ASR models loaded successfully[/green]")
    else:
        console.print("[red]❌ Failed to load ASR models[/red]")
    
    # Test TTS functionality
    if tts_success:
        console.print("\n[yellow]4. Testing text-to-speech...[/yellow]")
        test_text = "Hello, I am your AI medical assistant. How can I help you today?"
        
        try:
            audio_file = voice_interface.text_to_speech(test_text)
            if audio_file:
                console.print(f"[green]✅ TTS test successful! Audio saved to: {audio_file}[/green]")
            else:
                console.print("[red]❌ TTS test failed[/red]")
        except Exception as e:
            console.print(f"[red]❌ TTS test error: {e}[/red]")
    
    # Summary
    console.print("\n[bold blue]📊 Test Summary[/bold blue]")
    console.print(f"TTS Models: {'✅ Working' if tts_success else '❌ Failed'}")
    console.print(f"ASR Models: {'✅ Working' if asr_success else '❌ Failed'}")
    
    if tts_success or asr_success:
        console.print("\n[green]🎉 Voice interface is functional![/green]")
        console.print("[blue]You can now use voice features in MedBench[/blue]")
        return True
    else:
        console.print("\n[red]❌ Voice interface not working[/red]")
        return False

def test_medical_tts():
    """Test TTS with medical content"""
    console.print("\n[bold blue]🏥 Testing Medical TTS[/bold blue]")
    
    voice_interface = create_voice_interface()
    if not voice_interface or not voice_interface.load_tts_models():
        console.print("[red]❌ Cannot test medical TTS - models not available[/red]")
        return
    
    medical_texts = [
        "Based on your symptoms of chest pain and shortness of breath, I recommend immediate medical evaluation.",
        "Your blood pressure reading of 140 over 90 indicates stage 1 hypertension.",
        "The medication interaction between warfarin and aspirin may increase bleeding risk.",
        "Please take your prescribed medication twice daily with food.",
        "Your symptoms suggest a possible respiratory infection. Please see a doctor."
    ]
    
    for i, text in enumerate(medical_texts, 1):
        console.print(f"\n[yellow]Medical TTS Test {i}:[/yellow]")
        console.print(f"Text: {text}")
        
        try:
            audio_file = voice_interface.text_to_speech(text, f"medical_tts_test_{i}.wav")
            if audio_file:
                console.print(f"[green]✅ Audio generated: {audio_file}[/green]")
            else:
                console.print("[red]❌ Failed to generate audio[/red]")
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")

if __name__ == "__main__":
    try:
        # Basic voice interface test
        success = test_voice_interface()
        
        if success:
            # Medical TTS test
            test_medical_tts()
            
            console.print("\n[bold green]🎯 Voice Interface Testing Complete![/bold green]")
            console.print("\n[blue]Next steps:[/blue]")
            console.print("• Use the enhanced CLI with --voice flag for TTS output")
            console.print("• Use --voice-input flag for speech recognition")
            console.print("• Use --interactive for full voice consultation")
            console.print("\nExample commands:")
            console.print("python -m medbench.enhanced_cli --model-key flan_t5_small --scenario diagnosis --text 'chest pain' --voice")
            console.print("python -m medbench.enhanced_cli --model-key flan_t5_small --scenario diagnosis --voice-input")
            console.print("python -m medbench.enhanced_cli --model-key flan_t5_small --interactive")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Testing interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Testing failed: {e}[/red]")
        import traceback
        traceback.print_exc()
