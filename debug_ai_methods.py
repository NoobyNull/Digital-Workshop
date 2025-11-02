#!/usr/bin/env python3
"""
Debug AI methods to understand the issues.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.gui.services.ai_description_service import AIDescriptionService

def test_static_methods():
    """Test the static methods directly."""
    print("Testing AIDescriptionService static methods...")
    
    # Test get_available_providers
    print("\n1. Testing get_available_providers():")
    providers = AIDescriptionService.get_available_providers()
    print(f"Result: {providers}")
    print(f"Type: {type(providers)}")
    print(f"Length: {len(providers)}")
    
    # Test get_available_models for openai
    print("\n2. Testing get_available_models('openai'):")
    openai_models = AIDescriptionService.get_available_models("openai")
    print(f"Result: {openai_models}")
    print(f"Type: {type(openai_models)}")
    print(f"Length: {len(openai_models)}")
    
    # Test get_available_models for unknown provider
    print("\n3. Testing get_available_models('unknown'):")
    unknown_models = AIDescriptionService.get_available_models("unknown")
    print(f"Result: {unknown_models}")
    print(f"Type: {type(unknown_models)}")
    print(f"Length: {len(unknown_models)}")

if __name__ == "__main__":
    test_static_methods()