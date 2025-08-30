// Patient-related types
export interface Patient {
  id?: string;
  age?: number;
  gender?: 'male' | 'female' | 'other' | 'prefer_not_to_say';
  medical_history?: string[];
  current_medications?: string[];
  allergies?: string[];
  emergency_contact?: {
    name: string;
    phone: string;
    relationship: string;
  };
}

export interface PatientFormData {
  age: string;
  gender: string;
  medical_history: string;
  current_medications?: string;
  allergies?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  emergency_contact_relationship?: string;
}

export interface Symptoms {
  description: string;
  severity: 1 | 2 | 3 | 4 | 5;
  duration: string;
  onset: 'sudden' | 'gradual';
  triggers?: string[];
  relieving_factors?: string[];
  associated_symptoms?: string[];
}

export interface ConsultationSession {
  id: string;
  patient: Patient;
  symptoms: Symptoms;
  consultation_type: 'text' | 'voice' | 'enhanced';
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  created_at: string;
  updated_at: string;
  results?: ConsultationResponse;
}
