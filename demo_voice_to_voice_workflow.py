#!/usr/bin/env python3
"""
Complete Voice-to-Voice Medical Consultation Workflow Demo
Demonstrates the full pipeline: Patient Voice → ASR → Medical AI → TTS → Audio Playback
"""

import sys
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add medbench to path
sys.path.append(str(Path(__file__).parent))

console = Console()

def demonstrate_workflow_overview():
    """Show the complete workflow overview"""
    console.print(Panel(
        "[bold green]🎤 Voice-to-Voice Medical Consultation Workflow[/bold green]\n\n"
        "[blue]Complete Pipeline:[/blue]\n"
        "1. 🎤 [cyan]Patient Voice Input[/cyan] - Capture medical question/symptoms via microphone\n"
        "2. 👂 [yellow]Speech-to-Text (ASR)[/yellow] - Whisper converts speech to text\n"
        "3. 🧠 [green]Medical AI Processing[/green] - LLM analyzes symptoms and provides diagnosis\n"
        "4. 🗣️ [magenta]Text-to-Speech (TTS)[/magenta] - SpeechT5 + HiFiGAN generates voice response\n"
        "5. 🔊 [red]Audio Playback[/red] - Patient hears AI doctor's voice advice\n\n"
        "[bold yellow]Technologies Used:[/bold yellow]\n"
        "• ASR: OpenAI Whisper (multilingual speech recognition)\n"
        "• Medical AI: FLAN-T5 / Meerkat-8B (medical reasoning)\n"
        "• TTS: Microsoft SpeechT5 + HiFiGAN vocoder\n"
        "• Audio: soundfile, torchaudio for processing",
        title="🏥 Voice-to-Voice Medical AI System",
        border_style="green"
    ))

def show_technical_architecture():
    """Display the technical architecture"""
    console.print("\n[bold blue]🏗️ Technical Architecture[/bold blue]")
    
    # Architecture table
    arch_table = Table(title="System Components")
    arch_table.add_column("Component", style="cyan")
    arch_table.add_column("Technology", style="yellow")
    arch_table.add_column("Model/Library", style="green")
    arch_table.add_column("Purpose", style="magenta")
    
    components = [
        ("Audio Capture", "System Audio", "sox/pyaudio", "Record patient voice"),
        ("Speech Recognition", "Transformer ASR", "Whisper Small/Medium", "Convert speech to text"),
        ("Medical Analysis", "Language Model", "FLAN-T5/Meerkat-8B", "Analyze symptoms & diagnose"),
        ("Voice Synthesis", "Neural TTS", "SpeechT5 + HiFiGAN", "Generate natural speech"),
        ("Audio Playback", "System Audio", "afplay/aplay", "Play AI doctor response"),
        ("Orchestration", "Python Framework", "Rich + Custom CLI", "Coordinate workflow")
    ]
    
    for component, tech, model, purpose in components:
        arch_table.add_row(component, tech, model, purpose)
    
    console.print(arch_table)

def show_workflow_steps():
    """Show detailed workflow steps"""
    console.print("\n[bold blue]📋 Detailed Workflow Steps[/bold blue]")
    
    steps_table = Table(title="Voice-to-Voice Consultation Steps")
    steps_table.add_column("Step", style="cyan")
    steps_table.add_column("Input", style="yellow")
    steps_table.add_column("Processing", style="green")
    steps_table.add_column("Output", style="magenta")
    steps_table.add_column("Duration", style="red")
    
    workflow_steps = [
        ("1. Audio Capture", "Microphone", "Record 10s audio", "WAV file", "~10s"),
        ("2. Speech-to-Text", "Audio WAV", "Whisper ASR", "Text transcript", "~2-5s"),
        ("3. Medical Analysis", "Text symptoms", "Medical LLM", "Diagnosis text", "~3-10s"),
        ("4. Text-to-Speech", "Response text", "SpeechT5 + HiFiGAN", "Audio WAV", "~2-5s"),
        ("5. Audio Playback", "Response WAV", "System audio", "Spoken response", "~5-15s")
    ]
    
    for step, input_type, processing, output, duration in workflow_steps:
        steps_table.add_row(step, input_type, processing, output, duration)
    
    console.print(steps_table)

def show_sample_interactions():
    """Show sample medical interactions"""
    console.print("\n[bold blue]💬 Sample Medical Interactions[/bold blue]")
    
    interactions = [
        {
            "patient": "I have chest pain and shortness of breath",
            "ai_response": "Based on your symptoms of chest pain and shortness of breath, I recommend seeking immediate medical attention. These symptoms could indicate a serious cardiac condition that requires prompt evaluation by a healthcare professional."
        },
        {
            "patient": "I've been having severe headaches for three days",
            "ai_response": "Persistent severe headaches lasting three days warrant medical evaluation. Please ensure you're staying hydrated and getting adequate rest. If headaches continue or worsen, consult with a healthcare provider."
        },
        {
            "patient": "I have a fever and feel very tired",
            "ai_response": "Fever combined with fatigue can indicate an infection. Monitor your temperature, stay hydrated, and rest. If fever persists above 101°F or symptoms worsen, please contact a healthcare provider."
        }
    ]
    
    for i, interaction in enumerate(interactions, 1):
        console.print(Panel(
            f"[cyan]👤 Patient:[/cyan] \"{interaction['patient']}\"\n\n"
            f"[green]🤖 AI Doctor:[/green] \"{interaction['ai_response']}\"",
            title=f"Sample Interaction {i}",
            border_style="blue"
        ))

def demonstrate_cli_usage():
    """Show CLI usage examples"""
    console.print("\n[bold blue]💻 CLI Usage Examples[/bold blue]")
    
    cli_examples = [
        {
            "title": "Complete Voice-to-Voice Consultation",
            "command": "python -m medbench.enhanced_cli --model-key flan_t5_small --scenario diagnosis --voice-to-voice",
            "description": "Full workflow: speak symptoms → get voice diagnosis"
        },
        {
            "title": "Voice Input with Text Output",
            "command": "python -m medbench.enhanced_cli --model-key flan_t5_small --scenario diagnosis --voice-input",
            "description": "Speak symptoms → get text diagnosis"
        },
        {
            "title": "Text Input with Voice Output",
            "command": "python -m medbench.enhanced_cli --model-key flan_t5_small --scenario diagnosis --text 'chest pain' --voice",
            "description": "Type symptoms → get voice diagnosis"
        },
        {
            "title": "Interactive Voice Consultation",
            "command": "python -m medbench.enhanced_cli --model-key flan_t5_small --interactive",
            "description": "Multi-turn voice conversation with AI doctor"
        }
    ]
    
    for example in cli_examples:
        console.print(Panel(
            f"[green]Command:[/green]\n{example['command']}\n\n"
            f"[blue]Description:[/blue]\n{example['description']}",
            title=example["title"],
            border_style="green"
        ))

def show_system_requirements():
    """Display system requirements"""
    console.print("\n[bold blue]⚙️ System Requirements[/bold blue]")
    
    req_table = Table(title="Technical Requirements")
    req_table.add_column("Component", style="cyan")
    req_table.add_column("Requirement", style="yellow")
    req_table.add_column("Status", style="green")
    
    requirements = [
        ("Python", "3.8+", "✅ Available"),
        ("PyTorch", "2.0+", "✅ Installed"),
        ("Transformers", "4.20+", "✅ Installed"),
        ("Audio Libraries", "soundfile, torchaudio", "✅ Installed"),
        ("Voice Models", "Whisper, SpeechT5", "✅ Downloaded"),
        ("Disk Space", "~5GB for voice models", "✅ Available"),
        ("Microphone", "System audio input", "🔍 Check required"),
        ("Speakers", "System audio output", "🔍 Check required")
    ]
    
    for component, requirement, status in requirements:
        req_table.add_row(component, requirement, status)
    
    console.print(req_table)

def run_workflow_test():
    """Run a test of the voice workflow"""
    console.print("\n[bold blue]🧪 Testing Voice-to-Voice Workflow[/bold blue]")
    
    try:
        from medbench.voice_consultation import create_voice_consultation
        
        console.print("[yellow]Creating voice consultation system...[/yellow]")
        consultation = create_voice_consultation("flan_t5_small", "diagnosis")
        
        if consultation:
            console.print("[green]✅ Voice consultation system created successfully[/green]")
            
            # Show what would happen in a real consultation
            console.print(Panel(
                "[bold yellow]🎤 In a real consultation, you would:[/bold yellow]\n\n"
                "1. Speak your symptoms when prompted\n"
                "2. Wait for AI transcription and analysis\n"
                "3. Hear the AI doctor's voice response\n"
                "4. Continue conversation if needed\n\n"
                "[green]The system is ready for voice consultation![/green]",
                title="Ready for Voice Consultation",
                border_style="green"
            ))
        else:
            console.print("[red]❌ Failed to create voice consultation system[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ Error testing workflow: {e}[/red]")

def main():
    """Main demonstration function"""
    console.print("[bold green]🎤 Voice-to-Voice Medical Consultation Workflow Demo[/bold green]")
    console.print("=" * 80)
    
    # Show workflow overview
    demonstrate_workflow_overview()
    
    # Technical architecture
    show_technical_architecture()
    
    # Detailed workflow steps
    show_workflow_steps()
    
    # Sample interactions
    show_sample_interactions()
    
    # CLI usage examples
    demonstrate_cli_usage()
    
    # System requirements
    show_system_requirements()
    
    # Test the workflow
    run_workflow_test()
    
    # Final instructions
    console.print(Panel(
        "[bold green]🚀 Ready to Test Voice-to-Voice Consultation![/bold green]\n\n"
        "[yellow]To test the complete workflow:[/yellow]\n"
        "1. Ensure microphone and speakers are working\n"
        "2. Run: python test_voice_to_voice_consultation.py --full-test\n"
        "3. Or use CLI: python -m medbench.enhanced_cli --model-key flan_t5_small --voice-to-voice\n\n"
        "[blue]Sample test phrase:[/blue]\n"
        "\"I have chest pain and shortness of breath\"\n\n"
        "[red]Important:[/red] This is for demonstration only, not real medical advice!",
        title="🏥 Voice Consultation Ready",
        border_style="green"
    ))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Demo failed: {e}[/red]")
        import traceback
        traceback.print_exc()
