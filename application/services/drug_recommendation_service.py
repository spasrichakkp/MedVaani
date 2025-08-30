"""
Drug Recommendation Service for Indian Healthcare Context.

This service provides medication recommendations with focus on:
- Indian generic drug availability
- Local brand name mapping
- Dosage guidance appropriate for Indian population
- Cost-effective alternatives
- Safety considerations
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from domain.entities.patient import Patient
from domain.value_objects.medical_symptoms import MedicalSymptoms
from infrastructure.logging.medical_logger import MedicalLogger


class DrugCategory(Enum):
    """Categories of drugs for organization."""
    ANALGESIC = "analgesic"
    ANTIBIOTIC = "antibiotic"
    ANTIPYRETIC = "antipyretic"
    ANTACID = "antacid"
    ANTIHISTAMINE = "antihistamine"
    VITAMIN = "vitamin"
    COUGH_COLD = "cough_cold"
    DIGESTIVE = "digestive"
    TOPICAL = "topical"


class SafetyLevel(Enum):
    """Safety levels for drug recommendations."""
    SAFE = "safe"
    CAUTION = "caution"
    PRESCRIPTION_REQUIRED = "prescription_required"
    CONTRAINDICATED = "contraindicated"


@dataclass
class IndianDrugInfo:
    """Information about a drug in Indian market."""
    generic_name: str
    brand_names: List[str]
    category: DrugCategory
    dosage_forms: List[str]  # tablet, syrup, injection, etc.
    standard_dosage: str
    frequency: str
    duration: str
    route: str
    safety_level: SafetyLevel
    contraindications: List[str]
    side_effects: List[str]
    drug_interactions: List[str]
    pregnancy_category: Optional[str] = None
    pediatric_dosage: Optional[str] = None
    geriatric_considerations: Optional[str] = None
    cost_range_inr: Optional[str] = None
    availability_score: float = 1.0  # 0-1, how easily available
    
    def is_safe_for_patient(self, patient: Optional[Patient]) -> Tuple[bool, List[str]]:
        """Check if drug is safe for specific patient."""
        warnings = []
        
        if not patient:
            return True, warnings
        
        # Age-based checks
        if patient.age and patient.age < 18 and not self.pediatric_dosage:
            warnings.append("Pediatric dosage not established")
        
        if patient.age and patient.age > 65 and self.geriatric_considerations:
            warnings.append(f"Geriatric consideration: {self.geriatric_considerations}")
        
        # Pregnancy checks
        if (hasattr(patient, 'is_pregnant') and patient.is_pregnant and 
            self.pregnancy_category in ['D', 'X']):
            warnings.append("Not recommended during pregnancy")
            return False, warnings
        
        # Allergy checks
        if hasattr(patient, 'allergies') and patient.allergies:
            for allergy in patient.allergies:
                if allergy.lower() in self.generic_name.lower():
                    warnings.append(f"Patient allergic to {allergy}")
                    return False, warnings
        
        # Current medication interactions
        if hasattr(patient, 'current_medications') and patient.current_medications:
            for medication in patient.current_medications:
                for interaction in self.drug_interactions:
                    if medication.lower() in interaction.lower():
                        warnings.append(f"Interaction with {medication}")
        
        return len(warnings) == 0 or self.safety_level != SafetyLevel.CONTRAINDICATED, warnings


class DrugRecommendationService:
    """
    Service for providing drug recommendations in Indian healthcare context.
    
    Features:
    1. Indian generic drug database
    2. Brand name mapping
    3. Dosage recommendations
    4. Safety checks
    5. Cost considerations
    6. Availability scoring
    """
    
    def __init__(self, logger: Optional[MedicalLogger] = None):
        """
        Initialize the drug recommendation service.
        
        Args:
            logger: Optional medical logger instance
        """
        self.logger = logger or MedicalLogger(__name__)
        
        # Indian drug database
        self._drug_database = self._initialize_indian_drug_database()
        
        # Condition to drug mapping
        self._condition_drug_mapping = self._initialize_condition_mapping()
        
        # Symptom to drug mapping
        self._symptom_drug_mapping = self._initialize_symptom_mapping()
    
    def _initialize_indian_drug_database(self) -> Dict[str, IndianDrugInfo]:
        """Initialize comprehensive Indian drug database."""
        
        drugs = {}
        
        # Analgesics/Antipyretics
        drugs["paracetamol"] = IndianDrugInfo(
            generic_name="Paracetamol",
            brand_names=["Crocin", "Dolo", "Calpol", "Metacin", "Pyrigesic"],
            category=DrugCategory.ANTIPYRETIC,
            dosage_forms=["tablet", "syrup", "drops"],
            standard_dosage="500mg",
            frequency="Every 6-8 hours",
            duration="As needed, max 3 days",
            route="Oral",
            safety_level=SafetyLevel.SAFE,
            contraindications=["Severe liver disease"],
            side_effects=["Rare: liver damage with overdose"],
            drug_interactions=["Warfarin (increased bleeding risk)"],
            pregnancy_category="B",
            pediatric_dosage="10-15mg/kg every 6 hours",
            cost_range_inr="₹2-8 per tablet",
            availability_score=1.0
        )
        
        drugs["ibuprofen"] = IndianDrugInfo(
            generic_name="Ibuprofen",
            brand_names=["Brufen", "Combiflam", "Advil", "Ibugesic"],
            category=DrugCategory.ANALGESIC,
            dosage_forms=["tablet", "syrup", "gel"],
            standard_dosage="400mg",
            frequency="Every 6-8 hours",
            duration="As needed, max 5 days",
            route="Oral",
            safety_level=SafetyLevel.CAUTION,
            contraindications=["Peptic ulcer", "kidney disease", "heart failure"],
            side_effects=["Stomach upset", "kidney problems", "increased bleeding"],
            drug_interactions=["Warfarin", "ACE inhibitors", "Lithium"],
            pregnancy_category="C",
            pediatric_dosage="5-10mg/kg every 6-8 hours",
            geriatric_considerations="Use lowest effective dose",
            cost_range_inr="₹3-12 per tablet",
            availability_score=0.9
        )
        
        # Antibiotics
        drugs["amoxicillin"] = IndianDrugInfo(
            generic_name="Amoxicillin",
            brand_names=["Novamox", "Amoxil", "Moxikind", "Amoxyclav"],
            category=DrugCategory.ANTIBIOTIC,
            dosage_forms=["capsule", "tablet", "syrup"],
            standard_dosage="500mg",
            frequency="Every 8 hours",
            duration="5-7 days",
            route="Oral",
            safety_level=SafetyLevel.PRESCRIPTION_REQUIRED,
            contraindications=["Penicillin allergy"],
            side_effects=["Diarrhea", "nausea", "rash", "yeast infections"],
            drug_interactions=["Methotrexate", "Oral contraceptives"],
            pregnancy_category="B",
            pediatric_dosage="20-40mg/kg/day divided into 3 doses",
            cost_range_inr="₹5-15 per capsule",
            availability_score=0.95
        )
        
        drugs["azithromycin"] = IndianDrugInfo(
            generic_name="Azithromycin",
            brand_names=["Azithral", "Zithromax", "Azee", "Azax"],
            category=DrugCategory.ANTIBIOTIC,
            dosage_forms=["tablet", "syrup"],
            standard_dosage="500mg",
            frequency="Once daily",
            duration="3-5 days",
            route="Oral",
            safety_level=SafetyLevel.PRESCRIPTION_REQUIRED,
            contraindications=["Liver disease", "QT prolongation"],
            side_effects=["Nausea", "diarrhea", "abdominal pain"],
            drug_interactions=["Warfarin", "Digoxin", "Antacids"],
            pregnancy_category="B",
            pediatric_dosage="10mg/kg once daily",
            cost_range_inr="₹15-25 per tablet",
            availability_score=0.9
        )
        
        # Vitamins and Supplements
        drugs["vitamin_c"] = IndianDrugInfo(
            generic_name="Vitamin C (Ascorbic Acid)",
            brand_names=["Limcee", "Celin", "Redoxon", "C-Vit"],
            category=DrugCategory.VITAMIN,
            dosage_forms=["tablet", "chewable", "effervescent"],
            standard_dosage="500mg",
            frequency="Once daily",
            duration="5-10 days",
            route="Oral",
            safety_level=SafetyLevel.SAFE,
            contraindications=["Kidney stones (high doses)"],
            side_effects=["Stomach upset (high doses)", "diarrhea"],
            drug_interactions=["Iron supplements (enhances absorption)"],
            pregnancy_category="A",
            pediatric_dosage="100-200mg daily",
            cost_range_inr="₹1-5 per tablet",
            availability_score=1.0
        )
        
        # Digestive
        drugs["omeprazole"] = IndianDrugInfo(
            generic_name="Omeprazole",
            brand_names=["Omez", "Prilosec", "Omepraz", "Ocid"],
            category=DrugCategory.ANTACID,
            dosage_forms=["capsule", "tablet"],
            standard_dosage="20mg",
            frequency="Once daily before breakfast",
            duration="2-4 weeks",
            route="Oral",
            safety_level=SafetyLevel.CAUTION,
            contraindications=["Severe liver disease"],
            side_effects=["Headache", "nausea", "diarrhea", "vitamin B12 deficiency"],
            drug_interactions=["Clopidogrel", "Warfarin", "Phenytoin"],
            pregnancy_category="C",
            pediatric_dosage="0.7-3.3mg/kg daily",
            geriatric_considerations="Monitor for bone fractures with long-term use",
            cost_range_inr="₹8-20 per capsule",
            availability_score=0.95
        )
        
        # Cough and Cold
        drugs["cetirizine"] = IndianDrugInfo(
            generic_name="Cetirizine",
            brand_names=["Zyrtec", "Alerid", "Cetrizine", "Okacet"],
            category=DrugCategory.ANTIHISTAMINE,
            dosage_forms=["tablet", "syrup"],
            standard_dosage="10mg",
            frequency="Once daily",
            duration="As needed",
            route="Oral",
            safety_level=SafetyLevel.SAFE,
            contraindications=["Severe kidney disease"],
            side_effects=["Drowsiness", "dry mouth", "fatigue"],
            drug_interactions=["Alcohol", "CNS depressants"],
            pregnancy_category="B",
            pediatric_dosage="2.5-5mg daily (age dependent)",
            geriatric_considerations="May cause more drowsiness",
            cost_range_inr="₹2-8 per tablet",
            availability_score=0.95
        )
        
        return drugs
    
    def _initialize_condition_mapping(self) -> Dict[str, List[str]]:
        """Initialize mapping from conditions to recommended drugs."""
        
        return {
            "common_cold": ["paracetamol", "vitamin_c", "cetirizine"],
            "viral_infection": ["paracetamol", "vitamin_c"],
            "fever": ["paracetamol", "ibuprofen"],
            "headache": ["paracetamol", "ibuprofen"],
            "body_ache": ["paracetamol", "ibuprofen"],
            "bacterial_infection": ["amoxicillin", "azithromycin"],
            "respiratory_infection": ["azithromycin", "amoxicillin"],
            "gastritis": ["omeprazole"],
            "acidity": ["omeprazole"],
            "allergic_reaction": ["cetirizine"],
            "runny_nose": ["cetirizine"],
            "sneezing": ["cetirizine"]
        }
    
    def _initialize_symptom_mapping(self) -> Dict[str, List[str]]:
        """Initialize mapping from symptoms to recommended drugs."""
        
        return {
            "fever": ["paracetamol", "ibuprofen"],
            "headache": ["paracetamol", "ibuprofen"],
            "pain": ["paracetamol", "ibuprofen"],
            "cough": ["vitamin_c"],
            "cold": ["paracetamol", "vitamin_c", "cetirizine"],
            "runny_nose": ["cetirizine"],
            "sneezing": ["cetirizine"],
            "stomach_pain": ["omeprazole"],
            "acidity": ["omeprazole"],
            "nausea": ["omeprazole"],
            "allergy": ["cetirizine"],
            "itching": ["cetirizine"]
        }
    
    async def get_drug_recommendations(
        self,
        diagnosis: str,
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient] = None,
        max_recommendations: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get drug recommendations based on diagnosis and symptoms.
        
        Args:
            diagnosis: Primary diagnosis
            symptoms: Patient symptoms
            patient_context: Optional patient information
            max_recommendations: Maximum number of recommendations
            
        Returns:
            List of drug recommendations with safety information
        """
        try:
            self.logger.info(f"Generating drug recommendations for: {diagnosis}")
            
            # Get candidate drugs
            candidate_drugs = self._get_candidate_drugs(diagnosis, symptoms)
            
            # Filter and rank drugs
            recommendations = []
            for drug_name in candidate_drugs[:max_recommendations * 2]:  # Get more candidates
                if drug_name in self._drug_database:
                    drug_info = self._drug_database[drug_name]
                    
                    # Check safety for patient
                    is_safe, warnings = drug_info.is_safe_for_patient(patient_context)
                    
                    recommendation = {
                        "generic_name": drug_info.generic_name,
                        "brand_names": drug_info.brand_names[:3],  # Top 3 brands
                        "category": drug_info.category.value,
                        "dosage": drug_info.standard_dosage,
                        "frequency": drug_info.frequency,
                        "duration": drug_info.duration,
                        "route": drug_info.route,
                        "safety_level": drug_info.safety_level.value,
                        "is_safe": is_safe,
                        "warnings": warnings,
                        "contraindications": drug_info.contraindications,
                        "side_effects": drug_info.side_effects[:3],  # Top 3 side effects
                        "cost_range": drug_info.cost_range_inr,
                        "availability_score": drug_info.availability_score,
                        "prescription_required": drug_info.safety_level == SafetyLevel.PRESCRIPTION_REQUIRED
                    }
                    
                    # Add pediatric dosage if applicable
                    if patient_context and patient_context.age and patient_context.age < 18:
                        if drug_info.pediatric_dosage:
                            recommendation["pediatric_dosage"] = drug_info.pediatric_dosage
                    
                    recommendations.append(recommendation)
            
            # Sort by safety and availability
            recommendations.sort(
                key=lambda x: (x["is_safe"], x["availability_score"], -len(x["warnings"])),
                reverse=True
            )
            
            return recommendations[:max_recommendations]
            
        except Exception as e:
            self.logger.error(f"Failed to generate drug recommendations: {e}")
            return []
    
    def _get_candidate_drugs(self, diagnosis: str, symptoms: MedicalSymptoms) -> List[str]:
        """Get candidate drugs based on diagnosis and symptoms."""
        
        candidate_drugs = set()
        diagnosis_lower = diagnosis.lower()
        
        # Check condition mapping
        for condition, drugs in self._condition_drug_mapping.items():
            if condition in diagnosis_lower:
                candidate_drugs.update(drugs)
        
        # Check symptom mapping
        for symptom in symptoms.extracted_symptoms:
            symptom_lower = symptom.lower()
            for symptom_key, drugs in self._symptom_drug_mapping.items():
                if symptom_key in symptom_lower:
                    candidate_drugs.update(drugs)
        
        # Check raw text for additional symptoms
        raw_text_lower = symptoms.raw_text.lower()
        for symptom_key, drugs in self._symptom_drug_mapping.items():
            if symptom_key in raw_text_lower:
                candidate_drugs.update(drugs)
        
        return list(candidate_drugs)
    
    async def get_drug_interactions(
        self,
        drug_names: List[str],
        patient_medications: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Check for drug interactions."""
        
        interactions = []
        warnings = []
        
        # Check interactions between recommended drugs
        for i, drug1 in enumerate(drug_names):
            for drug2 in drug_names[i+1:]:
                if drug1 in self._drug_database and drug2 in self._drug_database:
                    drug1_info = self._drug_database[drug1]
                    drug2_info = self._drug_database[drug2]
                    
                    # Check if drugs interact
                    for interaction in drug1_info.drug_interactions:
                        if drug2_info.generic_name.lower() in interaction.lower():
                            interactions.append(f"{drug1_info.generic_name} + {drug2_info.generic_name}: {interaction}")
        
        # Check interactions with current medications
        if patient_medications:
            for drug_name in drug_names:
                if drug_name in self._drug_database:
                    drug_info = self._drug_database[drug_name]
                    for medication in patient_medications:
                        for interaction in drug_info.drug_interactions:
                            if medication.lower() in interaction.lower():
                                interactions.append(f"{drug_info.generic_name} + {medication}: {interaction}")
        
        return {
            "interactions": interactions,
            "warnings": warnings,
            "risk_level": "high" if interactions else "low"
        }
    
    async def get_drug_alternatives(
        self,
        drug_name: str,
        reason: str = "cost"
    ) -> List[Dict[str, Any]]:
        """Get alternative drugs for cost or safety reasons."""
        
        if drug_name not in self._drug_database:
            return []
        
        original_drug = self._drug_database[drug_name]
        alternatives = []
        
        # Find drugs in same category
        for name, drug_info in self._drug_database.items():
            if (name != drug_name and 
                drug_info.category == original_drug.category and
                drug_info.safety_level != SafetyLevel.CONTRAINDICATED):
                
                alternatives.append({
                    "generic_name": drug_info.generic_name,
                    "brand_names": drug_info.brand_names[:2],
                    "cost_range": drug_info.cost_range_inr,
                    "availability_score": drug_info.availability_score,
                    "safety_level": drug_info.safety_level.value,
                    "reason_for_alternative": reason
                })
        
        # Sort by cost if that's the reason
        if reason == "cost":
            # Simple cost sorting (would need more sophisticated parsing in real implementation)
            alternatives.sort(key=lambda x: x["availability_score"], reverse=True)
        
        return alternatives[:3]
