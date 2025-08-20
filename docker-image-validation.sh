#!/bin/bash

set -e


RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

DEFAULT_REGISTRY="docker.io"

usage() {
    echo "Usage: $0 [OPTIONS] [IMAGE_LIST_FILE]"
    echo ""
    echo "Options:"
    echo "  -r, --registry REGISTRY    Specify Docker registry (default: docker.io)"
    echo "  -f, --format FORMAT        Output format: text, json, csv (default: text)"
    echo "  -v, --verbose              Verbose output"
    echo "  -h, --help                 Show this help message"
    echo ""
    echo "If no IMAGE_LIST_FILE is provided, validates the default list of images."
    echo ""
    echo "Example:"
    echo "  $0 -r my-registry.com -f json"
    echo "  $0 --verbose my-images.txt"
}

DEFAULT_IMAGES=(
    "mobility/pytorch/pytorch-v2.0.1-cpu"
    "mobility/spark3"
    "notebook/hub"
    "notebook/singleuser"
    "olympus/aletheia"
    "olympus/spark-benchmark"
    "pie/decision-engine"
    "pie/decision-engine-spark34x"
    "pie/x-pipeline"
    "public-affairs/general"
)

REGISTRY="$DEFAULT_REGISTRY"
FORMAT="text"
VERBOSE=false
IMAGE_LIST_FILE=""
VALIDATION_RESULTS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -f|--format)
            FORMAT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            echo "Unknown option $1"
            usage
            exit 1
            ;;
        *)
            IMAGE_LIST_FILE="$1"
            shift
            ;;
    esac
done

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1" >&2
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed or not in PATH${NC}" >&2
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}Error: Docker daemon is not running or not accessible${NC}" >&2
        exit 1
    fi
    
    log_verbose "Docker is available and running"
}

validate_image() {
    local image="$1"
    local full_image_name
    
    if [[ "$image" != *"/"* ]] || [[ "$image" == *"."* ]]; then
        full_image_name="$image"
    else
        full_image_name="$REGISTRY/$image"
    fi
    
    log_verbose "Validating image: $full_image_name"
    
    local result_status="UNKNOWN"
    local result_message=""
    local result_size=""
    local result_created=""
    
    if docker manifest inspect "$full_image_name" &> /dev/null; then
        result_status="ACCESSIBLE"
        result_message="Image manifest is accessible"
        
        if docker image inspect "$full_image_name" &> /dev/null 2>&1; then
            result_status="LOCAL"
            result_message="Image is available locally"
            
            local image_info
            image_info=$(docker image inspect "$full_image_name" --format '{{.Size}},{{.Created}}' 2>/dev/null || echo ",")
            result_size=$(echo "$image_info" | cut -d',' -f1)
            result_created=$(echo "$image_info" | cut -d',' -f2)
        else
            log_verbose "Attempting to pull image to verify accessibility..."
            if docker pull "$full_image_name" &> /dev/null; then
                result_status="PULLED"
                result_message="Image successfully pulled"
                
                local image_info
                image_info=$(docker image inspect "$full_image_name" --format '{{.Size}},{{.Created}}' 2>/dev/null || echo ",")
                result_size=$(echo "$image_info" | cut -d',' -f1)
                result_created=$(echo "$image_info" | cut -d',' -f2)
            else
                result_status="PULL_FAILED"
                result_message="Image manifest accessible but pull failed"
            fi
        fi
    else
        result_status="NOT_FOUND"
        result_message="Image not found or not accessible"
    fi
    
    VALIDATION_RESULTS+=("$image,$full_image_name,$result_status,$result_message,$result_size,$result_created")
    
    return 0
}

display_results() {
    case "$FORMAT" in
        "json")
            echo "{"
            echo "  \"validation_timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
            echo "  \"registry\": \"$REGISTRY\","
            echo "  \"results\": ["
            
            local first=true
            for result in "${VALIDATION_RESULTS[@]}"; do
                IFS=',' read -r image full_name status message size created <<< "$result"
                
                if [ "$first" = true ]; then
                    first=false
                else
                    echo ","
                fi
                
                echo -n "    {"
                echo -n "\"image\": \"$image\", "
                echo -n "\"full_name\": \"$full_name\", "
                echo -n "\"status\": \"$status\", "
                echo -n "\"message\": \"$message\""
                
                if [ -n "$size" ]; then
                    echo -n ", \"size\": $size"
                fi
                if [ -n "$created" ]; then
                    echo -n ", \"created\": \"$created\""
                fi
                echo -n "}"
            done
            echo ""
            echo "  ]"
            echo "}"
            ;;
            
        "csv")
            echo "Image,Full Name,Status,Message,Size,Created"
            for result in "${VALIDATION_RESULTS[@]}"; do
                echo "$result"
            done
            ;;
            
        "text"|*)
            echo -e "${BLUE}Docker Image Validation Report${NC}"
            echo -e "${BLUE}================================${NC}"
            echo "Validation Time: $(date)"
            echo "Registry: $REGISTRY"
            echo ""
            
            local total=0
            local accessible=0
            local local_images=0
            local not_found=0
            
            for result in "${VALIDATION_RESULTS[@]}"; do
                IFS=',' read -r image full_name status message size created <<< "$result"
                total=$((total + 1))
                
                case "$status" in
                    "ACCESSIBLE"|"LOCAL"|"PULLED")
                        echo -e "${GREEN}✓${NC} $image"
                        accessible=$((accessible + 1))
                        if [ "$status" = "LOCAL" ]; then
                            local_images=$((local_images + 1))
                        fi
                        ;;
                    "NOT_FOUND"|"PULL_FAILED")
                        echo -e "${RED}✗${NC} $image"
                        not_found=$((not_found + 1))
                        ;;
                    *)
                        echo -e "${YELLOW}?${NC} $image"
                        ;;
                esac
                
                if [ "$VERBOSE" = true ]; then
                    echo "    Full name: $full_name"
                    echo "    Status: $status"
                    echo "    Message: $message"
                    if [ -n "$size" ]; then
                        echo "    Size: $size bytes"
                    fi
                    if [ -n "$created" ]; then
                        echo "    Created: $created"
                    fi
                    echo ""
                fi
            done
            
            echo ""
            echo -e "${BLUE}Summary:${NC}"
            echo "Total images: $total"
            echo -e "Accessible: ${GREEN}$accessible${NC}"
            echo -e "Local: ${GREEN}$local_images${NC}"
            echo -e "Not found/Failed: ${RED}$not_found${NC}"
            ;;
    esac
}

main() {
    log_verbose "Starting Docker image validation"
    
    check_docker
    
    local images_to_validate=()
    
    if [ -n "$IMAGE_LIST_FILE" ]; then
        if [ ! -f "$IMAGE_LIST_FILE" ]; then
            echo -e "${RED}Error: Image list file '$IMAGE_LIST_FILE' not found${NC}" >&2
            exit 1
        fi
        
        log_verbose "Reading images from file: $IMAGE_LIST_FILE"
        while IFS= read -r line; do
            if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
                images_to_validate+=("$line")
            fi
        done < "$IMAGE_LIST_FILE"
    else
        log_verbose "Using default image list"
        images_to_validate=("${DEFAULT_IMAGES[@]}")
    fi
    
    if [ ${#images_to_validate[@]} -eq 0 ]; then
        echo -e "${RED}Error: No images to validate${NC}" >&2
        exit 1
    fi
    
    log_verbose "Validating ${#images_to_validate[@]} images"
    
    for image in "${images_to_validate[@]}"; do
        validate_image "$image"
    done
    
    display_results
    
    log_verbose "Validation complete"
}

main "$@"
