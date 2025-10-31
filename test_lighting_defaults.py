#!/usr/bin/env python3
"""Test script to verify lighting defaults are loaded correctly."""

import sys
sys.path.insert(0, 'd:\\Digital Workshop')

from src.core.application_config import ApplicationConfig
from src.gui.lighting_manager import LightingManager
from src.gui.lighting_control_panel import LightingControlPanel

print("=" * 60)
print("TESTING LIGHTING DEFAULTS")
print("=" * 60)

# Test 1: ApplicationConfig defaults
print("\n1. ApplicationConfig Defaults:")
config = ApplicationConfig.get_default()
print(f"   Position X: {config.default_light_position_x}")
print(f"   Position Y: {config.default_light_position_y}")
print(f"   Position Z: {config.default_light_position_z}")
print(f"   Intensity: {config.default_light_intensity}")
print(f"   Cone Angle: {config.default_light_cone_angle}")

# Expected values
expected = {
    'position_x': 90.0,
    'position_y': 90.0,
    'position_z': 180.0,
    'intensity': 1.2,
    'cone_angle': 90.0
}

print("\n2. Verification:")
all_correct = True
if config.default_light_position_x != expected['position_x']:
    print(f"   ❌ Position X: Expected {expected['position_x']}, got {config.default_light_position_x}")
    all_correct = False
else:
    print(f"   ✓ Position X: {config.default_light_position_x}")

if config.default_light_position_y != expected['position_y']:
    print(f"   ❌ Position Y: Expected {expected['position_y']}, got {config.default_light_position_y}")
    all_correct = False
else:
    print(f"   ✓ Position Y: {config.default_light_position_y}")

if config.default_light_position_z != expected['position_z']:
    print(f"   ❌ Position Z: Expected {expected['position_z']}, got {config.default_light_position_z}")
    all_correct = False
else:
    print(f"   ✓ Position Z: {config.default_light_position_z}")

if config.default_light_intensity != expected['intensity']:
    print(f"   ❌ Intensity: Expected {expected['intensity']}, got {config.default_light_intensity}")
    all_correct = False
else:
    print(f"   ✓ Intensity: {config.default_light_intensity}")

if config.default_light_cone_angle != expected['cone_angle']:
    print(f"   ❌ Cone Angle: Expected {expected['cone_angle']}, got {config.default_light_cone_angle}")
    all_correct = False
else:
    print(f"   ✓ Cone Angle: {config.default_light_cone_angle}")

print("\n" + "=" * 60)
if all_correct:
    print("✓ ALL DEFAULTS ARE CORRECT!")
else:
    print("❌ SOME DEFAULTS ARE INCORRECT!")
print("=" * 60)

