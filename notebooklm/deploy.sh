#!/bin/bash

# Openbook Deployment Script - Future AGI Inc
# This script sets up and deploys the complete Openbook system

set -e

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

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Create environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        print_status "Creating .env file from template..."
        cp notebooklm-backend/.env.example .env
        
        # Generate random secrets
        SECRET_KEY=$(openssl rand -hex 32)
        JWT_SECRET=$(openssl rand -hex 32)
        
        # Update .env file
        sed -i "s/your-secret-key-here-change-in-production/$SECRET_KEY/" .env
        sed -i "s/your-jwt-secret-key-here-change-in-production/$JWT_SECRET/" .env
        
        print_warning "Please edit .env file and add your API keys (OpenAI, etc.)"
        print_warning "The system will work with limited functionality without API keys"
    else
        print_success "Environment file already exists"
    fi
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Run database initialization
    docker-compose exec backend python src/database/init_db.py
    
    print_success "Database initialized successfully"
}

# Build and start services
start_services() {
    print_status "Building and starting services..."
    
    # Build images
    docker-compose build
    
    # Start services
    docker-compose up -d
    
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    if docker-compose ps | grep -q "Up (healthy)"; then
        print_success "Services are running and healthy"
    else
        print_warning "Some services may not be fully ready yet"
    fi
}

# Show service status
show_status() {
    print_status "Service Status:"
    docker-compose ps
    
    echo ""
    print_status "Access URLs:"
    echo "  Frontend: http://localhost"
    echo "  Backend API: http://localhost:5050"
    echo "  API Documentation: http://localhost:5050/api/health"
    echo ""
    
    print_status "Default Login Credentials:"
    echo "  Email: test@example.com"
    echo "  Password: password123"
    echo ""
    echo "  Demo Account:"
    echo "  Email: demo@example.com"
    echo "  Password: demo123"
}

# Stop services
stop_services() {
    print_status "Stopping services..."
    docker-compose down
    print_success "Services stopped"
}

# Clean up everything
cleanup() {
    print_status "Cleaning up..."
    docker-compose down -v --rmi all
    docker system prune -f
    print_success "Cleanup completed"
}

# Show logs
show_logs() {
    if [ -n "$2" ]; then
        docker-compose logs -f "$2"
    else
        docker-compose logs -f
    fi
}

# Main script logic
case "$1" in
    "start"|"")
        print_status "Starting Openbook deployment..."
        check_docker
        setup_environment
        start_services
        init_database
        show_status
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        start_services
        show_status
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "$@"
        ;;
    "cleanup")
        cleanup
        ;;
    "init-db")
        init_database
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs [service]|cleanup|init-db}"
        echo ""
        echo "Commands:"
        echo "  start     - Start all services (default)"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  status    - Show service status and access URLs"
        echo "  logs      - Show logs for all services or specific service"
        echo "  cleanup   - Stop services and remove all data"
        echo "  init-db   - Initialize database with sample data"
        exit 1
        ;;
esac

