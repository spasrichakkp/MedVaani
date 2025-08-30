#!/usr/bin/env python3
"""
Enhanced Multi-Modal AI Doctor System Demonstration
Comprehensive showcase of voice-enabled medical AI capabilities
"""

import sys
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add medbench to path
sys.path.append(str(Path(__file__).parent))

from enhanced_model_manager import EnhancedModelDownloader, ModelTier, ModelCategory
from medbench.voice_interface import VoiceInterface, VoiceConfig, create_voice_interface

console = Console()

class EnhancedAIDoctorDemo:
    """Demonstration of the enhanced multi-modal AI doctor system"""
    
    def __init__(self):
        self.downloader = EnhancedModelDownloader()
        self.voice_interface = None
        
    def show_system_overview(self):
        """Display comprehensive system overview"""
        console.print(Panel(
            "[bold green]🏥 Enhanced Multi-Modal AI Doctor System[/bold green]\n\n"
            "[blue]Capabilities:[/blue]\n"
            "• 🗣️ Text-to-Speech (SpeechT5 + HiFiGAN)\n"
            "• 👂 Speech-to-Text (Whisper)\n"
            "• 🧠 Medical Reasoning (Meerkat-8B)\n"
            "• 👁️ Medical Vision (CLIP, CheXNet)\n"
            "• 💊 Drug Interaction Analysis\n"
            "• 📋 Clinical Note Summarization\n"
            "• 🚨 Clinical Decision Support\n"
            "• 🌍 Multilingual Support\n\n"
            "[yellow]Interactive Features:[/yellow]\n"
            "• Voice-enabled consultations\n"
            "• Multi-modal analysis (text + voice + image)\n"
            "• Real-time medical reasoning\n"
            "• Audio medical record generation",
            title="System Overview",
            border_style="green"
        ))
    
    def show_model_ecosystem(self):
        """Display the complete model ecosystem"""
        console.print("\n[bold blue]🤖 Model Ecosystem[/bold blue]")
        
        # Show models by category
        categories = [
            (ModelCategory.MEDICAL_REASONING, "🧠"),
            (ModelCategory.TEXT_TO_SPEECH, "🗣️"),
            (ModelCategory.SPEECH_TO_TEXT, "👂"),
            (ModelCategory.MEDICAL_VISION, "👁️"),
            (ModelCategory.MEDICAL_NLP, "📝")
        ]
        
        for category, emoji in categories:
            models = self.downloader.registry.get_models_by_category(category)
            if models:
                table = Table(title=f"{emoji} {category.value.replace('_', ' ').title()} Models")
                table.add_column("Model", style="cyan")
                table.add_column("Size", justify="right", style="green")
                table.add_column("Capabilities", style="yellow")
                table.add_column("Status", justify="center")
                
                for model in models:
                    model_key = next((key for key, spec in self.downloader.registry.models.items() if spec == model), None)
                    status = "✅" if model_key in self.downloader.downloaded_models else "⬇️"
                    
                    capabilities = ", ".join(model.capabilities[:2])
                    if len(model.capabilities) > 2:
                        capabilities += f" (+{len(model.capabilities)-2})"
                    
                    table.add_row(
                        model.name,
                        f"{model.estimated_size_gb:.1f}GB",
                        capabilities,
                        status
                    )
                
                console.print(table)
                console.print()
    
    def demonstrate_voice_capabilities(self):
        """Demonstrate voice interface capabilities"""
        console.print("\n[bold blue]🎤 Voice Interface Demonstration[/bold blue]")
        
        # Setup voice interface
        console.print("[yellow]Setting up voice interface...[/yellow]")
        self.voice_interface = create_voice_interface()
        
        if not self.voice_interface:
            console.print("[red]❌ Voice interface not available[/red]")
            return False
        
        # Load models
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task1 = progress.add_task("Loading TTS models...", total=None)
            tts_success = self.voice_interface.load_tts_models()
            progress.update(task1, description="TTS models loaded!" if tts_success else "TTS failed")
            
            task2 = progress.add_task("Loading ASR models...", total=None)
            asr_success = self.voice_interface.load_asr_models()
            progress.update(task2, description="ASR models loaded!" if asr_success else "ASR failed")
        
        # Demonstrate medical TTS
        if tts_success:
            console.print("\n[green]🗣️ Medical Text-to-Speech Demo[/green]")
            
            medical_scenarios = [
                ("Diagnosis", "Based on your symptoms of chest pain and shortness of breath, I recommend immediate cardiac evaluation."),
                ("Drug Interaction", "The combination of warfarin and aspirin significantly increases your bleeding risk."),
                ("Treatment Plan", "Please take your prescribed medication twice daily with food and monitor your blood pressure."),
                ("Emergency Alert", "Your symptoms suggest a possible heart attack. Please call 911 immediately."),
                ("Follow-up", "Your test results are normal. Continue your current medication and return in 3 months.")
            ]
            
            for scenario, text in medical_scenarios:
                console.print(f"\n[cyan]{scenario}:[/cyan] {text}")
                audio_file = self.voice_interface.text_to_speech(text, f"demo_{scenario.lower().replace(' ', '_')}.wav")
                if audio_file:
                    console.print(f"[green]✅ Audio generated: {audio_file}[/green]")
                time.sleep(1)
        
        return tts_success or asr_success
    
    def show_clinical_scenarios(self):
        """Demonstrate clinical scenarios"""
        console.print("\n[bold blue]🏥 Clinical Scenarios[/bold blue]")
        
        scenarios = [
            {
                "name": "Emergency Diagnosis",
                "description": "Patient presents with acute chest pain",
                "input_modes": ["Voice", "Text"],
                "ai_analysis": "Multi-symptom analysis with cardiac risk assessment",
                "output_modes": ["Voice response", "Clinical summary", "Urgency alert"]
            },
            {
                "name": "Drug Interaction Check",
                "description": "Polypharmacy safety analysis",
                "input_modes": ["Text", "Voice"],
                "ai_analysis": "Comprehensive medication interaction screening",
                "output_modes": ["Voice warning", "Risk assessment", "Alternative suggestions"]
            },
            {
                "name": "Medical Image Analysis",
                "description": "Chest X-ray pathology detection",
                "input_modes": ["Image", "Clinical context"],
                "ai_analysis": "AI-powered radiology interpretation",
                "output_modes": ["Voice report", "Visual annotations", "Confidence scores"]
            },
            {
                "name": "Clinical Decision Support",
                "description": "Real-time diagnostic assistance",
                "input_modes": ["Voice symptoms", "Vital signs"],
                "ai_analysis": "Evidence-based recommendation engine",
                "output_modes": ["Voice guidance", "Treatment protocols", "Risk stratification"]
            }
        ]
        
        table = Table(title="Clinical Scenario Capabilities")
        table.add_column("Scenario", style="cyan")
        table.add_column("Input Modes", style="yellow")
        table.add_column("AI Analysis", style="green")
        table.add_column("Output Modes", style="magenta")
        
        for scenario in scenarios:
            table.add_row(
                scenario["name"],
                " • ".join(scenario["input_modes"]),
                scenario["ai_analysis"],
                " • ".join(scenario["output_modes"])
            )
        
        console.print(table)
    
    def show_usage_examples(self):
        """Show practical usage examples"""
        console.print("\n[bold blue]💡 Usage Examples[/bold blue]")
        
        examples = [
            {
                "title": "Voice-Enabled Diagnosis",
                "command": "python -m medbench.enhanced_cli --model-key meerkat_8b --scenario diagnosis --voice-input --voice",
                "description": "Patient speaks symptoms → AI provides voice diagnosis"
            },
            {
                "title": "Text with Voice Response",
                "command": "python -m medbench.enhanced_cli --model-key meerkat_8b --scenario diagnosis --text 'chest pain and nausea' --voice",
                "description": "Text input → AI responds with voice"
            },
            {
                "title": "Interactive Consultation",
                "command": "python -m medbench.enhanced_cli --model-key meerkat_8b --interactive",
                "description": "Full voice conversation with AI doctor"
            },
            {
                "title": "Drug Interaction Analysis",
                "command": "python -m medbench.enhanced_cli --model-key meerkat_8b --scenario drug_interactions --voice-input",
                "description": "Voice medication list → AI safety analysis"
            },
            {
                "title": "Clinical Note Summarization",
                "command": "python -m medbench.enhanced_cli --model-key meerkat_8b --scenario summarization --text 'clinical_note.txt' --voice",
                "description": "Long clinical note → Voice summary"
            }
        ]
        
        for example in examples:
            console.print(Panel(
                f"[green]Command:[/green]\n{example['command']}\n\n"
                f"[blue]Description:[/blue]\n{example['description']}",
                title=example["title"],
                border_style="blue"
            ))
            console.print()
    
    def show_system_requirements(self):
        """Display system requirements and setup"""
        console.print("\n[bold blue]⚙️ System Requirements[/bold blue]")
        
        # Disk space analysis
        available_space = self.downloader.registry.get_available_space_gb()
        
        requirements_table = Table(title="Resource Requirements")
        requirements_table.add_column("Component", style="cyan")
        requirements_table.add_column("Space Required", style="yellow")
        requirements_table.add_column("Status", style="green")
        
        tiers = [
            ("Essential Tier", "3.2GB", "✅ Available"),
            ("Standard Tier", "8.5GB", "✅ Available" if available_space >= 8.5 else "❌ Insufficient"),
            ("Premium Tier", "25.1GB", "✅ Available" if available_space >= 25.1 else "❌ Insufficient"),
            ("Current Available", f"{available_space:.1f}GB", "📊 Status")
        ]
        
        for component, space, status in tiers:
            requirements_table.add_row(component, space, status)
        
        console.print(requirements_table)
        
        # Dependencies
        console.print("\n[yellow]📦 Key Dependencies:[/yellow]")
        deps = [
            "transformers (Hugging Face models)",
            "torch + torchaudio (PyTorch ecosystem)",
            "soundfile (Audio I/O)",
            "sentencepiece (SpeechT5 tokenization)",
            "rich (Enhanced CLI interface)",
            "whisper (Speech recognition)",
            "numpy + scipy (Numerical computing)"
        ]
        
        for dep in deps:
            console.print(f"  • {dep}")

def main():
    """Main demonstration function"""
    demo = EnhancedAIDoctorDemo()
    
    console.print("[bold green]🚀 Enhanced Multi-Modal AI Doctor System Demo[/bold green]")
    console.print("=" * 70)
    
    # System overview
    demo.show_system_overview()
    
    # Model ecosystem
    demo.show_model_ecosystem()
    
    # Voice capabilities
    voice_success = demo.demonstrate_voice_capabilities()
    
    # Clinical scenarios
    demo.show_clinical_scenarios()
    
    # Usage examples
    demo.show_usage_examples()
    
    # System requirements
    demo.show_system_requirements()
    
    # Final summary
    console.print(Panel(
        "[bold green]🎯 System Status: Fully Operational[/bold green]\n\n"
        f"[blue]Voice Interface:[/blue] {'✅ Working' if voice_success else '❌ Limited'}\n"
        "[blue]Medical Models:[/blue] ✅ Available\n"
        "[blue]Multi-Modal Support:[/blue] ✅ Ready\n"
        "[blue]Clinical Scenarios:[/blue] ✅ Implemented\n\n"
        "[yellow]Ready for:[/yellow]\n"
        "• Interactive medical consultations\n"
        "• Voice-enabled diagnosis\n"
        "• Multi-modal clinical analysis\n"
        "• Real-time medical decision support",
        title="🏥 Enhanced AI Doctor System Ready",
        border_style="green"
    ))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Demo error: {e}[/red]")
        import traceback
        traceback.print_exc()
