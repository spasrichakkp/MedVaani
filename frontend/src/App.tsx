import React, { useState } from 'react';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ConsultationForm } from '@/components/consultation/ConsultationForm';
import { useHealthMonitor } from '@/hooks/useWebSocket';
import { ConsultationResponse, EnhancedConsultationResponse } from '@/types/api';

function App() {
  const [consultationResult, setConsultationResult] = useState<ConsultationResponse | EnhancedConsultationResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'text' | 'voice' | 'enhanced'>('text');
  
  // Health monitoring
  const { healthStatus, isConnected, error: healthError } = useHealthMonitor(true);

  const handleConsultationSuccess = (result: ConsultationResponse | EnhancedConsultationResponse) => {
    setConsultationResult(result);
  };

  const handleConsultationError = (error: any) => {
    console.error('Consultation error:', error);
    // Error is already handled by the consultation components
  };

  const clearResults = () => {
    setConsultationResult(null);
  };

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold text-gray-900">
                  🩺 MedVaani
                </h1>
                <span className="ml-3 text-sm text-gray-500">
                  Medical Research AI
                </span>
              </div>
              
              {/* Connection Status */}
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${
                    isConnected ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <span className="text-sm text-gray-600">
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                
                {healthStatus && (
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${
                      healthStatus.status === 'healthy' ? 'bg-green-500' :
                      healthStatus.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                    }`} />
                    <span className="text-sm text-gray-600 capitalize">
                      {healthStatus.status}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Consultation Form */}
            <div className="lg:col-span-2">
              <div className="space-y-6">
                {/* Tab Navigation */}
                <div className="bg-white rounded-lg shadow-sm p-1">
                  <nav className="flex space-x-1">
                    <button
                      onClick={() => setActiveTab('text')}
                      className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
                        activeTab === 'text'
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      📝 Text Input
                    </button>
                    <button
                      onClick={() => setActiveTab('voice')}
                      className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
                        activeTab === 'voice'
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      🎤 Voice Input
                    </button>
                    <button
                      onClick={() => setActiveTab('enhanced')}
                      className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
                        activeTab === 'enhanced'
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      ⚡ Enhanced
                    </button>
                  </nav>
                </div>

                {/* Consultation Forms */}
                {activeTab === 'text' && (
                  <ConsultationForm
                    onSuccess={handleConsultationSuccess}
                    onError={handleConsultationError}
                  />
                )}

                {activeTab === 'voice' && (
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">🎤</div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        Voice Consultation
                      </h3>
                      <p className="text-gray-600">
                        Voice consultation feature is coming soon!
                      </p>
                    </div>
                  </div>
                )}

                {activeTab === 'enhanced' && (
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">⚡</div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        Enhanced Consultation
                      </h3>
                      <p className="text-gray-600">
                        Enhanced consultation with interactive diagnosis is coming soon!
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Right Column - Results and Health */}
            <div className="space-y-6">
              {/* Results Panel */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Analysis Results
                  </h2>
                  {consultationResult && (
                    <button
                      onClick={clearResults}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      Clear
                    </button>
                  )}
                </div>

                {consultationResult ? (
                  <div className="space-y-4">
                    {/* Urgency Level */}
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-gray-700">Urgency:</span>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        consultationResult.analysis.urgency === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                        consultationResult.analysis.urgency === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                        consultationResult.analysis.urgency === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {consultationResult.analysis.urgency}
                      </span>
                    </div>

                    {/* Confidence */}
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-gray-700">Confidence:</span>
                      <span className="text-sm text-gray-600">
                        {Math.round(consultationResult.analysis.confidence * 100)}%
                      </span>
                    </div>

                    {/* Emergency Flag */}
                    {consultationResult.analysis.is_emergency && (
                      <div className="bg-red-50 border border-red-200 rounded-md p-3">
                        <div className="flex items-center">
                          <span className="text-red-400 mr-2">🚨</span>
                          <span className="text-sm font-medium text-red-800">
                            Emergency Situation Detected
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Patient-Friendly Response */}
                    <div>
                      <h3 className="text-sm font-medium text-gray-700 mb-2">Analysis:</h3>
                      <p className="text-sm text-gray-600 leading-relaxed">
                        {consultationResult.analysis.patient_friendly_response}
                      </p>
                    </div>

                    {/* Recommendations */}
                    {consultationResult.analysis.recommendations.length > 0 && (
                      <div>
                        <h3 className="text-sm font-medium text-gray-700 mb-2">Recommendations:</h3>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {consultationResult.analysis.recommendations.map((rec, index) => (
                            <li key={index} className="flex items-start">
                              <span className="text-blue-500 mr-2">•</span>
                              {rec}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Red Flags */}
                    {consultationResult.analysis.red_flags.length > 0 && (
                      <div>
                        <h3 className="text-sm font-medium text-red-700 mb-2">Warning Signs:</h3>
                        <ul className="text-sm text-red-600 space-y-1">
                          {consultationResult.analysis.red_flags.map((flag, index) => (
                            <li key={index} className="flex items-start">
                              <span className="text-red-500 mr-2">⚠️</span>
                              {flag}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Model Used */}
                    <div className="text-xs text-gray-400 pt-2 border-t">
                      Model: {consultationResult.analysis.model_used}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">🩺</div>
                    <p className="text-gray-500">
                      Enter symptoms to begin analysis
                    </p>
                  </div>
                )}
              </div>

              {/* System Health Panel */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  System Health
                </h2>
                
                {healthStatus ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Overall Status</span>
                      <div className={`w-2 h-2 rounded-full ${
                        healthStatus.status === 'healthy' ? 'bg-green-500' :
                        healthStatus.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                      }`} />
                    </div>
                    
                    {Object.entries(healthStatus.services).map(([service, status]) => (
                      <div key={service} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 capitalize">
                          {service.replace('_', ' ')}
                        </span>
                        <div className={`w-2 h-2 rounded-full ${
                          status.status === 'up' ? 'bg-green-500' :
                          status.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                        }`} />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center justify-center py-4">
                    <LoadingSpinner size="sm" text="Loading health status..." />
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </ErrorBoundary>
  );
}

export default App;
