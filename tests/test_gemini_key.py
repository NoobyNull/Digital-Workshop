"""
Test script to verify Gemini API key is working.
"""

import sys
import os
from pathlib import Path
import tempfile
from PIL import Image


def test_gemini_key(api_key: str) -> tuple[bool, str]:
    """
    Test if the Gemini API key is valid and working.

    Args:
        api_key: The Gemini API key to test

    Returns:
        Tuple of (success, message)
    """
    try:
        import google.generativeai as genai

        print("[INFO] Testing Gemini API key...")
        print(f"[INFO] API Key (masked): {api_key[:10]}...{api_key[-4:]}")

        # Step 1: Configure the API
        print("[STEP 1] Configuring Gemini API...")
        try:
            genai.configure(api_key=api_key)
            print("[PASS] API configured successfully")
        except Exception as e:
            return False, f"Failed to configure API: {str(e)}"

        # Step 2: List available models
        print("[STEP 2] Listing available models...")
        try:
            models = genai.list_models()
            vision_models = [
                m
                for m in models
                if "vision" in m.name.lower() or "gemini" in m.name.lower()
            ]
            print(f"[PASS] Found {len(vision_models)} vision models")
            for model in vision_models[:5]:
                print(f"  - {model.name}")
        except Exception as e:
            return False, f"Failed to list models: {str(e)}"

        # Step 3: Create a test image
        print("[STEP 3] Creating test image...")
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                # Create a simple test image
                img = Image.new("RGB", (100, 100), color="red")
                img.save(tmp.name)
                test_image_path = tmp.name
                print(f"[PASS] Test image created: {test_image_path}")
        except Exception as e:
            return False, f"Failed to create test image: {str(e)}"

        # Step 4: Test image analysis
        print("[STEP 4] Testing image analysis...")
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            print("[INFO] Using model: gemini-2.5-flash")

            # Load the test image
            with open(test_image_path, "rb") as f:
                image_data = f.read()

            # Create the request
            print("[INFO] Sending analysis request...")
            response = model.generate_content(
                ["Describe this image in one sentence.", Image.open(test_image_path)]
            )

            if response.text:
                print(f"[PASS] Analysis successful!")
                print(f"[RESULT] {response.text[:100]}...")

                # Clean up
                os.unlink(test_image_path)

                return (
                    True,
                    f"Gemini API key is working! Response: {response.text[:50]}...",
                )
            else:
                return False, "API returned empty response"

        except Exception as e:
            error_msg = str(e)
            print(f"[FAIL] Analysis failed: {error_msg}")

            # Clean up
            if os.path.exists(test_image_path):
                os.unlink(test_image_path)

            # Check for specific error types
            if "API key" in error_msg or "authentication" in error_msg.lower():
                return False, f"API Key Error: {error_msg}"
            elif "quota" in error_msg.lower():
                return False, f"Quota Error: {error_msg}"
            elif "rate limit" in error_msg.lower():
                return False, f"Rate Limit Error: {error_msg}"
            else:
                return False, f"Analysis Error: {error_msg}"

    except ImportError:
        return (
            False,
            "google.generativeai library not installed. Install with: pip install google-generativeai",
        )
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def main():
    """Main test function."""
    print("=" * 70)
    print("Gemini API Key Verification Test")
    print("=" * 70)
    print()

    # Get API key from environment or user input
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("[ERROR] GOOGLE_API_KEY environment variable not set")
        print()
        print("Please provide your Gemini API key in one of these ways:")
        print("1. Set environment variable: set GOOGLE_API_KEY=your_key")
        print(
            "2. Or pass it as command line argument: python test_gemini_key.py your_key"
        )
        print()

        if len(sys.argv) > 1:
            api_key = sys.argv[1]
            print(f"[INFO] Using API key from command line argument")
        else:
            print("[ERROR] No API key provided")
            return False
    else:
        print("[INFO] Using API key from GOOGLE_API_KEY environment variable")

    print()

    # Run the test
    success, message = test_gemini_key(api_key)

    print()
    print("=" * 70)
    if success:
        print("[SUCCESS] ✓ Gemini API key is working!")
        print(f"Message: {message}")
    else:
        print("[FAILURE] ✗ Gemini API key is NOT working")
        print(f"Error: {message}")
    print("=" * 70)

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
