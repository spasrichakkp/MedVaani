#!/bin/bash

# Enhanced Medical Research AI - Installation Script
# This script sets up the Enhanced Medical Research AI system

set -e  # Exit on any error

echo "🩺 Enhanced Medical Research AI - Installation Script"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
check_python() {
    print_status "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION found"
        
        # Check if version is 3.9+
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
            print_success "Python version is compatible (3.9+)"
        else
            print_error "Python 3.9+ is required. Current version: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 is not installed. Please install Python 3.9+ first."
        exit 1
    fi
}

# Check if UV is available, install if not
setup_uv() {
    print_status "Checking UV package manager..."
    
    if command -v uv &> /dev/null; then
        print_success "UV package manager found"
        USE_UV=true
    else
        print_warning "UV package manager not found"
        echo "Would you like to install UV for faster dependency management? (y/n)"
        read -r response
        
        if [[ "$response" =~ ^[Yy]$ ]]; then
            print_status "Installing UV package manager..."
            curl -LsSf https://astral.sh/uv/install.sh | sh
            
            # Source the shell to get UV in PATH
            export PATH="$HOME/.cargo/bin:$PATH"
            
            if command -v uv &> /dev/null; then
                print_success "UV installed successfully"
                USE_UV=true
            else
                print_warning "UV installation failed, falling back to pip"
                USE_UV=false
            fi
        else
            print_status "Using pip for dependency management"
            USE_UV=false
        fi
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ "$USE_UV" = true ]; then
        uv venv
        print_success "Virtual environment created with UV"
    else
        python3 -m venv .venv
        print_success "Virtual environment created with venv"
    fi
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source .venv/Scripts/activate
    else
        source .venv/bin/activate
    fi
    
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    if [ "$USE_UV" = true ]; then
        print_status "Installing with UV..."
        uv pip install -r requirements.txt
        uv pip install -r requirements-web.txt
        
        # Install development dependencies if requested
        echo "Would you like to install development dependencies? (y/n)"
        read -r dev_response
        if [[ "$dev_response" =~ ^[Yy]$ ]]; then
            uv pip install -e ".[dev]"
            print_success "Development dependencies installed"
        fi
    else
        print_status "Installing with pip..."
        pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-web.txt
        
        # Install development dependencies if requested
        echo "Would you like to install development dependencies? (y/n)"
        read -r dev_response
        if [[ "$dev_response" =~ ^[Yy]$ ]]; then
            pip install -e ".[dev]"
            print_success "Development dependencies installed"
        fi
    fi
    
    print_success "Dependencies installed successfully"
}

# Download initial models
download_models() {
    print_status "Downloading initial AI models..."
    
    echo "Would you like to download the default medical AI model? (y/n)"
    echo "This will download google/flan-t5-base (~1GB)"
    read -r model_response
    
    if [[ "$model_response" =~ ^[Yy]$ ]]; then
        python download_models.py
        print_success "Models downloaded successfully"
    else
        print_warning "Models not downloaded. You can download them later with: python download_models.py"
    fi
}

# Setup environment file
setup_env() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        cat > .env << EOF
# Enhanced Medical Research AI Configuration

# Optional: Infermedica API for enhanced accuracy
# INFERMEDICA_APP_ID=your_app_id
# INFERMEDICA_APP_KEY=your_app_key

# Enhanced features (enabled by default)
ENABLE_DRUG_RECOMMENDATIONS=true
ENABLE_INTERACTIVE_DIAGNOSIS=true

# Model configuration
MEDICAL_MODEL=google/flan-t5-base
MEDICAL_DEVICE=auto
ENVIRONMENT=development

# Performance tuning
FORCE_TORCH_DTYPE=float32
USE_MOCK_ADAPTERS=false
EOF
        print_success "Environment file created (.env)"
    else
        print_warning "Environment file already exists (.env)"
    fi
}

# Run tests
run_tests() {
    echo "Would you like to run tests to verify the installation? (y/n)"
    read -r test_response
    
    if [[ "$test_response" =~ ^[Yy]$ ]]; then
        print_status "Running tests..."
        
        if command -v pytest &> /dev/null; then
            pytest tests/ -v
            print_success "Tests completed"
        else
            print_warning "pytest not available, skipping tests"
        fi
    fi
}

# Main installation process
main() {
    echo
    print_status "Starting Enhanced Medical Research AI installation..."
    echo
    
    # Check prerequisites
    check_python
    
    # Setup package manager
    setup_uv
    
    # Create and activate virtual environment
    create_venv
    activate_venv
    
    # Install dependencies
    install_dependencies
    
    # Setup environment
    setup_env
    
    # Download models
    download_models
    
    # Run tests
    run_tests
    
    echo
    print_success "🎉 Installation completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Activate the virtual environment:"
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        echo "   source .venv/Scripts/activate"
    else
        echo "   source .venv/bin/activate"
    fi
    echo "2. Start the web server:"
    echo "   python web/main.py"
    echo "3. Open your browser to: http://localhost:8000"
    echo
    echo "For more information, see README.md"
    echo
}

# Run main function
main "$@"
