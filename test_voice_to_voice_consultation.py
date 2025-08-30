#!/usr/bin/env python3
"""
Test Voice-to-Voice Medical Consultation Workflow
Complete end-to-end testing of the voice consultation pipeline
"""

import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Add medbench to path
sys.path.append(str(Path(__file__).parent))

try:
    from medbench.voice_consultation import create_voice_consultation
    CONSULTATION_AVAILABLE = True
except ImportError as e:
    CONSULTATION_AVAILABLE = False
    print(f"Voice consultation not available: {e}")

console = Console()

def test_voice_consultation_workflow(model_key: str = "flan_t5_small", scenario: str = "diagnosis"):
    """Test the complete voice-to-voice consultation workflow"""
    
    if not CONSULTATION_AVAILABLE:
        console.print("[red]❌ Voice consultation system not available[/red]")
        return False
    
    console.print("[bold green]🧪 Testing Voice-to-Voice Medical Consultation[/bold green]")
    console.print("=" * 70)
    
    # Create consultation system
    console.print("\n[yellow]1. Creating voice consultation system...[/yellow]")
    consultation = create_voice_consultation(model_key, scenario)
    
    if not consultation:
        console.print("[red]❌ Failed to create consultation system[/red]")
        return False
    
    console.print("[green]✅ Voice consultation system created[/green]")
    
    # Show instructions
    console.print(Panel(
        "[bold blue]🎤 Voice Consultation Test Instructions[/bold blue]\n\n"
        "[yellow]What to expect:[/yellow]\n"
        "1. You'll be prompted to speak for 10 seconds\n"
        "2. The system will transcribe your speech\n"
        "3. Medical AI will analyze your symptoms\n"
        "4. AI will generate a voice response\n"
        "5. You'll hear the AI doctor's advice\n\n"
        "[green]Sample medical questions to try:[/green]\n"
        "• 'I have chest pain and shortness of breath'\n"
        "• 'I've been having severe headaches for three days'\n"
        "• 'I have a fever and feel very tired'\n"
        "• 'My stomach hurts and I feel nauseous'\n\n"
        "[red]Important:[/red] This is for testing only, not real medical advice!",
        title="Test Instructions",
        border_style="blue"
    ))
    
    # Ask user if ready to proceed
    try:
        ready = input("\n🎤 Are you ready to start the voice consultation test? (y/n): ").lower().strip()
        if ready != 'y':
            console.print("[yellow]Test cancelled by user[/yellow]")
            return False
    except KeyboardInterrupt:
        console.print("\n[yellow]Test cancelled by user[/yellow]")
        return False
    
    # Run the consultation
    console.print("\n[green]🚀 Starting voice-to-voice consultation test...[/green]")
    
    try:
        success = consultation.run_consultation()
        
        if success:
            console.print("\n[bold green]🎉 Voice consultation test completed successfully![/bold green]")
            
            # Show next steps
            console.print(Panel(
                "[bold blue]🎯 Test Results[/bold blue]\n\n"
                "[green]✅ Complete voice-to-voice workflow functional[/green]\n"
                "[green]✅ Speech recognition working[/green]\n"
                "[green]✅ Medical AI analysis working[/green]\n"
                "[green]✅ Voice synthesis working[/green]\n"
                "[green]✅ Audio playback working[/green]\n\n"
                "[yellow]Next steps:[/yellow]\n"
                "• Test with different medical scenarios\n"
                "• Try various accents and speaking styles\n"
                "• Test in different acoustic environments\n"
                "• Integrate with actual medical models",
                title="🏥 Voice Consultation Test Results",
                border_style="green"
            ))
            return True
        else:
            console.print("\n[red]❌ Voice consultation test failed[/red]")
            return False
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrupted by user[/yellow]")
        return False
    except Exception as e:
        console.print(f"\n[red]❌ Test failed with error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

def test_individual_components():
    """Test individual components of the voice consultation system"""
    console.print("\n[bold blue]🔧 Testing Individual Components[/bold blue]")
    
    # Test voice interface availability
    try:
        from medbench.voice_interface import create_voice_interface
        voice_interface = create_voice_interface()
        if voice_interface:
            console.print("[green]✅ Voice interface available[/green]")
            
            # Test TTS
            tts_success = voice_interface.load_tts_models()
            console.print(f"[{'green' if tts_success else 'red'}]{'✅' if tts_success else '❌'} TTS models: {'Working' if tts_success else 'Failed'}[/{'green' if tts_success else 'red'}]")
            
            # Test ASR
            asr_success = voice_interface.load_asr_models()
            console.print(f"[{'green' if asr_success else 'red'}]{'✅' if asr_success else '❌'} ASR models: {'Working' if asr_success else 'Failed'}[/{'green' if asr_success else 'red'}]")
            
        else:
            console.print("[red]❌ Voice interface not available[/red]")
    except Exception as e:
        console.print(f"[red]❌ Voice interface error: {e}[/red]")
    
    # Test medical models
    try:
        from medbench.models import load_pipeline
        from medbench.config import load_model_config
        
        models_config = load_model_config("configs/models.yaml")
        console.print("[green]✅ Model configuration loaded[/green]")
        
        # Test with lightweight model
        try:
            model = load_pipeline("flan_t5_small", models_config)
            console.print("[green]✅ Medical model pipeline working[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Medical model not available: {e}[/yellow]")
            
    except Exception as e:
        console.print(f"[red]❌ Medical model error: {e}[/red]")

def simulate_voice_consultation():
    """Simulate a voice consultation with text input for testing"""
    console.print("\n[bold blue]🎭 Simulated Voice Consultation[/bold blue]")
    console.print("(Using text input to simulate the voice workflow)")
    
    try:
        from medbench.voice_consultation import create_voice_consultation
        
        consultation = create_voice_consultation()
        if not consultation:
            console.print("[red]❌ Cannot create consultation system[/red]")
            return
        
        # Setup system
        if not consultation.setup_system():
            console.print("[red]❌ System setup failed[/red]")
            return
        
        # Simulate patient input
        patient_input = "I have chest pain and shortness of breath"
        console.print(f"[cyan]Simulated patient input: '{patient_input}'[/cyan]")
        
        # Step 3: Medical analysis (skip audio steps)
        success, medical_response = consultation.analyze_with_medical_ai(patient_input)
        if not success:
            console.print("[red]❌ Medical analysis failed[/red]")
            return
        
        # Step 4: Generate voice response
        success, response_audio = consultation.generate_voice_response(medical_response)
        if success:
            console.print(f"[green]✅ Voice response generated: {response_audio}[/green]")
            
            # Try to play the response
            consultation.play_ai_response(response_audio)
        
        console.print("[green]✅ Simulated consultation completed[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Simulation failed: {e}[/red]")

def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test Voice-to-Voice Medical Consultation")
    parser.add_argument("--model-key", default="flan_t5_small", help="Medical model to use")
    parser.add_argument("--scenario", default="diagnosis", help="Medical scenario to test")
    parser.add_argument("--components-only", action="store_true", help="Test individual components only")
    parser.add_argument("--simulate", action="store_true", help="Run simulated consultation with text")
    parser.add_argument("--full-test", action="store_true", help="Run complete voice consultation test")
    
    args = parser.parse_args()
    
    console.print("[bold green]🏥 Voice-to-Voice Medical Consultation Test Suite[/bold green]")
    console.print("=" * 70)
    
    if args.components_only:
        test_individual_components()
    elif args.simulate:
        simulate_voice_consultation()
    elif args.full_test:
        test_voice_consultation_workflow(args.model_key, args.scenario)
    else:
        # Run all tests
        console.print("\n[blue]Running comprehensive test suite...[/blue]")
        
        # Test components
        test_individual_components()
        
        # Run simulation
        simulate_voice_consultation()
        
        # Ask if user wants to run full voice test
        try:
            full_test = input("\n🎤 Would you like to run the full voice consultation test? (y/n): ").lower().strip()
            if full_test == 'y':
                test_voice_consultation_workflow(args.model_key, args.scenario)
        except KeyboardInterrupt:
            console.print("\n[yellow]Test suite completed[/yellow]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Testing interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Test suite failed: {e}[/red]")
        import traceback
        traceback.print_exc()
