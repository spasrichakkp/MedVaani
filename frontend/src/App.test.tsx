import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';

// Mock the WebSocket service
jest.mock('@/services/webSocketService', () => ({
  webSocketService: {
    connect: jest.fn(() => Promise.resolve()),
    disconnect: jest.fn(),
    on: jest.fn(),
    off: jest.fn(),
    getConnectionState: jest.fn(() => 'connected'),
    isConnected: jest.fn(() => true),
  },
}));

// Mock the API service
jest.mock('@/services/apiService', () => ({
  apiService: {
    submitTextConsultation: jest.fn(() => Promise.resolve({
      consultation_id: 'test-id',
      analysis: {
        urgency: 'LOW',
        confidence: 0.85,
        is_emergency: false,
        recommendations: ['Rest and hydration'],
        red_flags: [],
        patient_friendly_response: 'Your symptoms appear to be mild.',
        model_used: 'test-model',
      },
    })),
    getHealthStatus: jest.fn(() => Promise.resolve({
      status: 'healthy',
      services: {
        api: { status: 'up', last_check: new Date().toISOString() },
      },
      system_metrics: {
        cpu_usage: 25,
        memory_usage: 60,
        disk_usage: 40,
      },
    })),
  },
}));

describe('App Component', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  test('renders main application', () => {
    render(<App />);
    
    // Check if main elements are present
    expect(screen.getByText('🩺 MedVaani')).toBeInTheDocument();
    expect(screen.getByText('Medical Research AI')).toBeInTheDocument();
    expect(screen.getByText('Medical Consultation')).toBeInTheDocument();
  });

  test('renders tab navigation', () => {
    render(<App />);
    
    // Check if all tabs are present
    expect(screen.getByText('📝 Text Input')).toBeInTheDocument();
    expect(screen.getByText('🎤 Voice Input')).toBeInTheDocument();
    expect(screen.getByText('⚡ Enhanced')).toBeInTheDocument();
  });

  test('switches between tabs', () => {
    render(<App />);
    
    // Initially text tab should be active
    const textTab = screen.getByText('📝 Text Input');
    const voiceTab = screen.getByText('🎤 Voice Input');
    
    expect(textTab.closest('button')).toHaveClass('bg-blue-100');
    
    // Click voice tab
    fireEvent.click(voiceTab);
    
    // Voice tab should now be active
    expect(voiceTab.closest('button')).toHaveClass('bg-blue-100');
    expect(screen.getByText('Voice Consultation')).toBeInTheDocument();
  });

  test('displays consultation form in text tab', () => {
    render(<App />);
    
    // Check if consultation form elements are present
    expect(screen.getByLabelText(/describe your symptoms/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/age/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/gender/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/medical history/i)).toBeInTheDocument();
  });

  test('displays results panel', () => {
    render(<App />);
    
    // Check if results panel is present
    expect(screen.getByText('Analysis Results')).toBeInTheDocument();
    expect(screen.getByText('Enter symptoms to begin analysis')).toBeInTheDocument();
  });

  test('displays system health panel', () => {
    render(<App />);
    
    // Check if health panel is present
    expect(screen.getByText('System Health')).toBeInTheDocument();
  });

  test('shows connection status', async () => {
    render(<App />);
    
    // Should show connected status
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
  });

  test('handles consultation form submission', async () => {
    render(<App />);
    
    // Fill out the form
    const symptomsInput = screen.getByLabelText(/describe your symptoms/i);
    const submitButton = screen.getByText(/analyze symptoms/i);
    
    fireEvent.change(symptomsInput, {
      target: { value: 'I have a headache and feel tired' },
    });
    
    // Submit the form
    fireEvent.click(submitButton);
    
    // Should show loading state
    expect(screen.getByText(/analyzing/i)).toBeInTheDocument();
    
    // Wait for results to appear
    await waitFor(() => {
      expect(screen.getByText('Your symptoms appear to be mild.')).toBeInTheDocument();
    });
  });

  test('displays consultation results', async () => {
    render(<App />);
    
    // Fill and submit form
    const symptomsInput = screen.getByLabelText(/describe your symptoms/i);
    const submitButton = screen.getByText(/analyze symptoms/i);
    
    fireEvent.change(symptomsInput, {
      target: { value: 'I have a headache and feel tired' },
    });
    fireEvent.click(submitButton);
    
    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('LOW')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText('Rest and hydration')).toBeInTheDocument();
    });
  });

  test('clears results when clear button is clicked', async () => {
    render(<App />);
    
    // Submit a consultation first
    const symptomsInput = screen.getByLabelText(/describe your symptoms/i);
    const submitButton = screen.getByText(/analyze symptoms/i);
    
    fireEvent.change(symptomsInput, {
      target: { value: 'I have a headache and feel tired' },
    });
    fireEvent.click(submitButton);
    
    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('Your symptoms appear to be mild.')).toBeInTheDocument();
    });
    
    // Click clear button
    const clearButton = screen.getByText('Clear');
    fireEvent.click(clearButton);
    
    // Results should be cleared
    expect(screen.getByText('Enter symptoms to begin analysis')).toBeInTheDocument();
  });
});
