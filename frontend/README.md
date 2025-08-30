# MedVaani Frontend

A modern React application for the Medical Research AI system, providing a user-friendly interface for medical consultations with voice-to-voice capabilities.

## 🚀 Features

- **Text Consultation**: Input symptoms via text for medical analysis
- **Voice Consultation**: Record audio for voice-based medical consultation (coming soon)
- **Enhanced Consultation**: Interactive diagnosis with follow-up questions (coming soon)
- **Real-time Health Monitoring**: WebSocket-based system health monitoring
- **Progress Tracking**: Real-time consultation progress updates
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **Error Handling**: Comprehensive error boundaries and user feedback
- **TypeScript**: Full type safety for better development experience

## 🛠️ Technology Stack

- **React 18** - Modern React with hooks and functional components
- **TypeScript** - Type safety and better developer experience
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API communication
- **React Hook Form** - Form handling with validation
- **WebSocket API** - Real-time communication
- **React Query** - Server state management (planned)

## 📦 Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env.local
   ```
   
   Edit `.env.local` with your configuration:
   ```
   REACT_APP_API_URL=http://localhost:8000
   REACT_APP_WS_URL=ws://localhost:8000/ws/health
   ```

## 🚀 Development

1. **Start the development server:**
   ```bash
   npm start
   ```
   
   The app will open at [http://localhost:3000](http://localhost:3000)

2. **Run tests:**
   ```bash
   npm test
   ```

3. **Build for production:**
   ```bash
   npm run build
   ```

4. **Lint and format code:**
   ```bash
   npm run lint
   npm run format
   ```

## 🏗️ Project Structure

```
frontend/
├── public/                 # Static files
├── src/
│   ├── components/         # React components
│   │   ├── common/         # Reusable components
│   │   ├── consultation/   # Consultation-related components
│   │   ├── health/         # Health monitoring components
│   │   └── diagnosis/      # Diagnosis components
│   ├── hooks/              # Custom React hooks
│   │   ├── useWebSocket.ts
│   │   ├── useAudioRecorder.ts
│   │   └── useConsultation.ts
│   ├── services/           # API and external services
│   │   ├── apiService.ts
│   │   ├── webSocketService.ts
│   │   └── audioService.ts
│   ├── types/              # TypeScript type definitions
│   ├── utils/              # Utility functions
│   └── styles/             # Global styles
├── package.json
├── tsconfig.json
└── README.md
```

## 🔧 Configuration

### Environment Variables

- `REACT_APP_API_URL` - Backend API URL (default: http://localhost:8000)
- `REACT_APP_WS_URL` - WebSocket URL (default: ws://localhost:8000/ws/health)

### API Integration

The frontend communicates with the FastAPI backend through:

- **REST API**: For consultation submissions and health checks
- **WebSocket**: For real-time health monitoring and progress updates
- **File Upload**: For voice consultation audio files

## 🧪 Testing

The project includes comprehensive testing setup:

- **Unit Tests**: Component and utility function tests
- **Integration Tests**: API integration and user workflow tests
- **E2E Tests**: End-to-end user journey tests (planned)

Run tests with:
```bash
npm test                    # Run all tests
npm test -- --coverage     # Run with coverage report
npm test -- --watch        # Run in watch mode
```

## 🚀 Deployment

### Development Deployment

1. Start the React development server:
   ```bash
   npm start
   ```

2. Ensure the backend is running on port 8000

### Production Deployment

1. Build the React app:
   ```bash
   npm run build
   ```

2. The built files will be in the `build/` directory

3. The FastAPI backend will automatically serve the built React app

## 🔒 Security Features

- **Input Validation**: Client-side and server-side validation
- **Error Boundaries**: Graceful error handling
- **CORS Configuration**: Proper cross-origin resource sharing
- **Type Safety**: TypeScript for compile-time error prevention

## 🎯 Performance Optimizations

- **Code Splitting**: Automatic code splitting with React
- **Lazy Loading**: Components loaded on demand
- **Memoization**: React.memo and useMemo for performance
- **Bundle Optimization**: Webpack optimizations for production

## 🐛 Error Handling

The application includes comprehensive error handling:

- **Error Boundaries**: Catch and display component errors
- **API Error Handling**: Graceful handling of network errors
- **User Feedback**: Clear error messages and retry mechanisms
- **Logging**: Console logging for development and debugging

## 🤝 Contributing

1. Follow the existing code style and patterns
2. Write tests for new features
3. Update documentation as needed
4. Use TypeScript for all new code
5. Follow React best practices and hooks patterns

## 📝 API Documentation

The frontend integrates with these backend endpoints:

- `POST /api/consultation/text` - Text-based consultation
- `POST /api/consultation/voice` - Voice-based consultation
- `POST /api/consultation/enhanced` - Enhanced consultation
- `GET /api/health` - System health status
- `WS /ws/health` - Real-time health monitoring

## 🔄 State Management

The application uses:

- **Local State**: React useState for component state
- **Custom Hooks**: Shared stateful logic
- **Context API**: Global state management (planned)
- **React Query**: Server state caching (planned)

## 📱 Responsive Design

The interface is fully responsive with:

- **Mobile-first approach**: Optimized for mobile devices
- **Breakpoint system**: Tailwind CSS responsive utilities
- **Touch-friendly**: Large touch targets and gestures
- **Accessibility**: WCAG 2.1 compliance

## 🎨 Styling

- **Tailwind CSS**: Utility-first CSS framework
- **Custom CSS Variables**: Consistent theming
- **Component Styles**: Modular styling approach
- **Dark Mode**: Support planned for future release
