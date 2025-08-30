#!/usr/bin/env python3
"""
Live Medical AI Testing Script
Comprehensive real-time testing of medical AI models across clinical scenarios
"""

import json
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from medbench.scenarios.diagnosis import build_input as build_diagnosis_input, run_case as run_diagnosis
from medbench.scenarios.drug_interactions import build_input as build_drug_input, run_case as run_drug
from medbench.scenarios.summarization import build_input as build_summary_input, run_case as run_summary
from medbench.scenarios.cds import build_input as build_cds_input, run_case as run_cds
from medbench.models import load_pipeline
from medbench.config import load_model_config

console = Console()

def create_test_cases():
    """Create realistic medical test cases for each scenario"""
    
    # Diagnosis Test Cases
    diagnosis_cases = [
        {
            "id": "diagnosis_1a",
            "name": "Complex Cardiac Case",
            "patient": {"age": 68, "sex": "M"},
            "symptoms": ["chest pain radiating to left arm", "shortness of breath on exertion", "diaphoresis", "nausea"],
            "history": ["hypertension", "diabetes mellitus type 2", "hyperlipidemia", "smoking history 40 pack-years"],
            "medications": ["metformin", "lisinopril", "atorvastatin"],
            "expected_diagnoses": ["acute coronary syndrome", "myocardial infarction", "unstable angina"]
        },
        {
            "id": "diagnosis_1b", 
            "name": "Neurological Case",
            "patient": {"age": 45, "sex": "F"},
            "symptoms": ["severe headache", "photophobia", "neck stiffness", "fever"],
            "history": ["migraine", "no recent travel"],
            "medications": ["sumatriptan PRN"],
            "expected_diagnoses": ["meningitis", "subarachnoid hemorrhage", "severe migraine"]
        }
    ]
    
    # Drug Interaction Test Cases
    drug_cases = [
        {
            "id": "drug_1a",
            "name": "Polypharmacy Elderly Patient",
            "patient": {"age": 78, "sex": "F"},
            "medications": ["warfarin 5mg daily", "amiodarone 200mg daily", "digoxin 0.25mg daily", "furosemide 40mg BID"],
            "comorbidities": ["atrial fibrillation", "heart failure", "chronic kidney disease"],
            "new_medication": "clarithromycin 500mg BID",
            "expected_interactions": ["warfarin-clarithromycin", "digoxin-clarithromycin"]
        },
        {
            "id": "drug_1b",
            "name": "Psychiatric Medication Interaction",
            "patient": {"age": 34, "sex": "M"},
            "medications": ["sertraline 100mg daily", "lithium 900mg BID", "lorazepam 1mg PRN"],
            "comorbidities": ["bipolar disorder", "anxiety disorder"],
            "new_medication": "tramadol 50mg QID",
            "expected_interactions": ["sertraline-tramadol serotonin syndrome", "lithium-tramadol"]
        }
    ]
    
    # Clinical Summarization Test Cases
    summary_cases = [
        {
            "id": "summary_1a",
            "name": "Emergency Department Note",
            "clinical_note": """
            CHIEF COMPLAINT: Chest pain
            
            HISTORY OF PRESENT ILLNESS: 
            65-year-old male with history of hypertension and diabetes presents with acute onset chest pain that started 2 hours ago while mowing the lawn. Pain is described as crushing, substernal, radiating to left arm and jaw. Associated with diaphoresis, nausea, and shortness of breath. No relief with rest. Patient took 3 sublingual nitroglycerin tablets with minimal improvement.
            
            PAST MEDICAL HISTORY: Hypertension, Type 2 diabetes mellitus, hyperlipidemia
            MEDICATIONS: Metformin 1000mg BID, Lisinopril 10mg daily, Atorvastatin 40mg daily
            SOCIAL HISTORY: 30 pack-year smoking history, quit 5 years ago
            
            PHYSICAL EXAM:
            Vitals: BP 160/95, HR 110, RR 22, O2 sat 94% on RA, Temp 98.6F
            General: Diaphoretic, anxious appearing male in moderate distress
            Cardiovascular: Tachycardic, regular rhythm, no murmurs
            Pulmonary: Bilateral crackles at bases
            
            ASSESSMENT AND PLAN:
            Acute coronary syndrome, likely STEMI. Cardiology consulted. Patient started on dual antiplatelet therapy, heparin, and prepared for emergent cardiac catheterization.
            """,
            "expected_summary_points": ["ACS/STEMI", "cardiac catheterization", "dual antiplatelet therapy"]
        }
    ]
    
    # Clinical Decision Support Test Cases  
    cds_cases = [
        {
            "id": "cds_1a",
            "name": "Sepsis Alert Case",
            "chief_complaint": "fever and confusion",
            "vitals": {"temperature": 102.3, "heart_rate": 125, "blood_pressure": "85/50", "respiratory_rate": 28, "oxygen_saturation": 91},
            "findings": ["altered mental status", "hypotension", "tachycardia", "tachypnea", "hypoxemia"],
            "labs": {"wbc": 18500, "lactate": 4.2, "procalcitonin": 8.5},
            "expected_alerts": ["sepsis", "septic shock", "SIRS criteria"]
        }
    ]
    
    return {
        "diagnosis": diagnosis_cases,
        "drug_interactions": drug_cases, 
        "summarization": summary_cases,
        "cds": cds_cases
    }

def test_scenario(scenario_name, test_cases, model_pipeline, gen_defaults):
    """Test a specific medical scenario with given test cases"""
    
    console.print(f"\n[bold blue]🧪 Testing {scenario_name.upper()} Scenario[/bold blue]")
    
    results = []
    
    for i, case in enumerate(test_cases, 1):
        console.print(f"\n[yellow]Test Case {i}: {case['name']}[/yellow]")
        
        # Build input based on scenario
        if scenario_name == "diagnosis":
            input_text = build_diagnosis_input(case)
            result = run_diagnosis(model_pipeline, case, gen_defaults)
        elif scenario_name == "drug_interactions":
            input_text = build_drug_input(case)
            result = run_drug(model_pipeline, case, gen_defaults)
        elif scenario_name == "summarization":
            input_text = build_summary_input(case)
            result = run_summary(model_pipeline, case, gen_defaults)
        elif scenario_name == "cds":
            input_text = build_cds_input(case)
            result = run_cds(model_pipeline, case, gen_defaults)
        
        # Display results
        console.print(Panel(input_text, title="[green]Input to Model[/green]", border_style="green"))
        console.print(Panel(result['output'], title="[blue]Model Output[/blue]", border_style="blue"))
        console.print(f"[magenta]Score: {result['score']:.2f}[/magenta]")
        
        results.append({
            "case_id": case["id"],
            "case_name": case["name"],
            "input": input_text,
            "output": result['output'],
            "score": result['score']
        })
        
        time.sleep(1)  # Brief pause between tests
    
    return results

def main():
    """Main testing function"""
    
    console.print("[bold green]🏥 MedBench Live Medical AI Testing[/bold green]")
    console.print("=" * 60)
    
    # Load model configuration
    console.print("\n[yellow]Loading model configuration...[/yellow]")
    models_cfg = load_model_config('configs/models.yaml')
    gen_defaults = models_cfg.defaults.get('generation', {})
    
    # Create test cases
    console.print("[yellow]Creating realistic medical test cases...[/yellow]")
    test_cases = create_test_cases()
    
    # For demonstration, let's use T5-small first (faster)
    model_key = "flan_t5_small"  # Change to "meerkat_8b" for full testing
    
    console.print(f"[yellow]Loading {model_key} model...[/yellow]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Loading model...", total=None)
        model_pipeline = load_pipeline(model_key, models_cfg)
        progress.update(task, description="Model loaded!")
    
    # Test each scenario
    all_results = {}
    
    for scenario_name, cases in test_cases.items():
        if cases:  # Only test scenarios with cases
            try:
                results = test_scenario(scenario_name, cases, model_pipeline, gen_defaults)
                all_results[scenario_name] = results
            except Exception as e:
                console.print(f"[red]Error testing {scenario_name}: {e}[/red]")
                continue
    
    # Summary table
    console.print("\n[bold green]📊 Testing Summary[/bold green]")
    table = Table(title="Medical AI Test Results")
    table.add_column("Scenario", style="cyan")
    table.add_column("Test Cases", justify="center")
    table.add_column("Avg Score", justify="center")
    table.add_column("Status", justify="center")
    
    for scenario, results in all_results.items():
        if results:
            avg_score = sum(r['score'] for r in results) / len(results)
            status = "✅ Pass" if avg_score > 0.5 else "⚠️ Review"
            table.add_row(scenario.title(), str(len(results)), f"{avg_score:.2f}", status)
    
    console.print(table)
    
    # Save results
    output_file = Path("live_test_results.json")
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    console.print(f"\n[green]Results saved to {output_file}[/green]")

if __name__ == "__main__":
    main()
