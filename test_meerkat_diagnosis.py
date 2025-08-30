#!/usr/bin/env python3
"""
Direct test of Meerkat-8B model for medical diagnosis
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from rich.console import Console
from rich.panel import Panel

console = Console()

def test_meerkat_diagnosis():
    """Test Meerkat-8B model directly for medical diagnosis"""
    
    console.print("[bold green]🧪 Testing Meerkat-8B for Medical Diagnosis[/bold green]")
    
    # Load model and tokenizer
    model_name = "dmis-lab/llama-3-meerkat-8b-v1.0"
    
    console.print(f"[yellow]Loading {model_name}...[/yellow]")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        low_cpu_mem_usage=True
    )
    
    # Set pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    console.print("[green]✓ Model loaded successfully![/green]")
    
    # Test Case 1: Cardiac Case
    test_case_1 = """
Patient: 68-year-old male
Chief Complaint: Chest pain
History: The patient presents with acute onset chest pain that started 2 hours ago. Pain is described as crushing, substernal, radiating to left arm and jaw. Associated with diaphoresis, nausea, and shortness of breath.
Past Medical History: Hypertension, diabetes mellitus type 2, hyperlipidemia, 40 pack-year smoking history
Current Medications: Metformin, lisinopril, atorvastatin

Question: What are the 3 most likely diagnoses for this patient? Provide brief rationales and recommended initial tests.
"""
    
    console.print(Panel(test_case_1.strip(), title="[green]Test Case 1: Cardiac Emergency[/green]", border_style="green"))
    
    # Generate response
    console.print("[yellow]Generating response...[/yellow]")
    
    inputs = tokenizer(test_case_1, return_tensors="pt", padding=True, truncation=True, max_length=512)
    
    with torch.no_grad():
        outputs = model.generate(
            inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_new_tokens=200,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    # Decode response
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract only the generated part (after the input)
    generated_text = response[len(test_case_1):].strip()
    
    console.print(Panel(generated_text, title="[blue]Meerkat-8B Response[/blue]", border_style="blue"))
    
    # Test Case 2: Neurological Case
    test_case_2 = """
Patient: 45-year-old female
Chief Complaint: Severe headache
History: Patient presents with sudden onset severe headache, described as "worst headache of my life." Associated with photophobia, neck stiffness, and fever of 101.5°F. No recent trauma.
Past Medical History: Migraine headaches
Current Medications: Sumatriptan PRN

Question: What are the 3 most likely diagnoses? What immediate tests should be ordered?
"""
    
    console.print(Panel(test_case_2.strip(), title="[green]Test Case 2: Neurological Emergency[/green]", border_style="green"))
    
    # Generate response for case 2
    console.print("[yellow]Generating response...[/yellow]")
    
    inputs2 = tokenizer(test_case_2, return_tensors="pt", padding=True, truncation=True, max_length=512)
    
    with torch.no_grad():
        outputs2 = model.generate(
            inputs2.input_ids,
            attention_mask=inputs2.attention_mask,
            max_new_tokens=200,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    # Decode response
    response2 = tokenizer.decode(outputs2[0], skip_special_tokens=True)
    generated_text2 = response2[len(test_case_2):].strip()
    
    console.print(Panel(generated_text2, title="[blue]Meerkat-8B Response[/blue]", border_style="blue"))
    
    console.print("[bold green]✅ Testing completed![/bold green]")

if __name__ == "__main__":
    test_meerkat_diagnosis()
