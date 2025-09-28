#!/bin/bash

# =============================================================================
# Script de Deploy para sofIA Agents (Python)
# =============================================================================
# Este script facilita o deploy apenas dos agentes Python
# O WhatsApp Bridge deve ser deployado separadamente

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_message() {
    echo -e "${BLUE}[sofIA]${NC} $1"
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

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

# Nome da imagem Docker
IMAGE_NAME="sofia-agents"
CONTAINER_NAME="sofia-payment-agents"

# Porta padrão
PORT=${PORT:-8000}

# =============================================================================
# FUNÇÕES
# =============================================================================

check_requirements() {
    print_message "Verificando requisitos..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker não está instalado!"
        exit 1
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose não está instalado!"
        exit 1
    fi
    
    # Verificar arquivo .env
    if [ ! -f ".env" ]; then
        print_warning "Arquivo .env não encontrado!"
        print_message "Copiando env.deploy.example para .env..."
        cp env.deploy.example .env
        print_warning "Configure o arquivo .env com suas credenciais antes de continuar!"
        exit 1
    fi
    
    print_success "Requisitos verificados!"
}

build_image() {
    print_message "Construindo imagem Docker..."
    
    docker build -f Dockerfile.agents -t $IMAGE_NAME .
    
    print_success "Imagem construída com sucesso!"
}

stop_existing() {
    print_message "Parando containers existentes..."
    
    # Parar container se estiver rodando
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        docker stop $CONTAINER_NAME
        print_message "Container parado."
    fi
    
    # Remover container se existir
    if docker ps -aq -f name=$CONTAINER_NAME | grep -q .; then
        docker rm $CONTAINER_NAME
        print_message "Container removido."
    fi
}

start_container() {
    print_message "Iniciando container..."
    
    # Carregar variáveis do .env
    export $(cat .env | grep -v '^#' | xargs)
    
    # Iniciar container
    docker run -d \
        --name $CONTAINER_NAME \
        --restart unless-stopped \
        -p $PORT:8000 \
        --env-file .env \
        -v $(pwd)/logs:/app/logs \
        -v $(pwd)/temp:/app/temp \
        $IMAGE_NAME
    
    print_success "Container iniciado na porta $PORT!"
}

start_with_compose() {
    print_message "Iniciando com Docker Compose..."
    
    docker-compose -f docker-compose.agents.yml up -d
    
    print_success "Serviços iniciados com Docker Compose!"
}

check_health() {
    print_message "Verificando saúde do serviço..."
    
    # Aguardar serviço inicializar
    sleep 10
    
    # Testar health check
    if curl -f http://localhost:$PORT/health > /dev/null 2>&1; then
        print_success "Serviço está saudável!"
        print_message "Acesse: http://localhost:$PORT/health"
    else
        print_error "Serviço não está respondendo!"
        print_message "Verifique os logs: docker logs $CONTAINER_NAME"
        exit 1
    fi
}

show_logs() {
    print_message "Mostrando logs do container..."
    docker logs -f $CONTAINER_NAME
}

show_status() {
    print_message "Status dos containers:"
    docker ps -f name=$CONTAINER_NAME
}

cleanup() {
    print_message "Limpando recursos..."
    
    # Parar e remover container
    stop_existing
    
    # Remover imagem (opcional)
    if [ "$1" = "--remove-image" ]; then
        docker rmi $IMAGE_NAME
        print_message "Imagem removida."
    fi
    
    print_success "Limpeza concluída!"
}

show_help() {
    echo "Uso: $0 [COMANDO]"
    echo ""
    echo "Comandos:"
    echo "  build     - Construir imagem Docker"
    echo "  start     - Iniciar container"
    echo "  compose   - Iniciar com Docker Compose"
    echo "  stop      - Parar container"
    echo "  restart   - Reiniciar container"
    echo "  logs      - Mostrar logs"
    echo "  status    - Mostrar status"
    echo "  health    - Verificar saúde do serviço"
    echo "  cleanup   - Limpar recursos"
    echo "  help      - Mostrar esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0 build"
    echo "  $0 start"
    echo "  $0 compose"
    echo "  $0 logs"
    echo "  $0 cleanup --remove-image"
}

# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

main() {
    case "${1:-help}" in
        "build")
            check_requirements
            build_image
            ;;
        "start")
            check_requirements
            stop_existing
            build_image
            start_container
            check_health
            ;;
        "compose")
            check_requirements
            start_with_compose
            check_health
            ;;
        "stop")
            stop_existing
            ;;
        "restart")
            stop_existing
            build_image
            start_container
            check_health
            ;;
        "logs")
            show_logs
            ;;
        "status")
            show_status
            ;;
        "health")
            check_health
            ;;
        "cleanup")
            cleanup $2
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# =============================================================================
# EXECUÇÃO
# =============================================================================

# Verificar se está no diretório correto
if [ ! -f "app.py" ] || [ ! -f "Dockerfile.agents" ]; then
    print_error "Execute este script no diretório raiz do projeto!"
    exit 1
fi

# Executar função principal
main "$@"
