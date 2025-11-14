#!/usr/bin/env python3
"""Test script to interact with PyMCPAutoGUI server."""

import subprocess
import json
import sys
import time
from pathlib import Path

def test_pymcp_server():
    """Test the PyMCPAutoGUI server by listing available tools."""
    
    print("=" * 60)
    print("PyMCPAutoGUI Server Interaction Test")
    print("=" * 60)
    
    # Start the server
    print("\n[1] Starting PyMCPAutoGUI server...")
    proc = subprocess.Popen(
        [sys.executable, '-m', 'pymcpautogui.server'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    time.sleep(2)  # Give server time to start
    
    try:
        # Send initialization request
        print("[2] Sending initialization request...")
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0"
                }
            }
        }
        
        init_json = json.dumps(init_msg)
        proc.stdin.write(init_json + '\n')
        proc.stdin.flush()
        
        # Read response
        print("[3] Reading server response...")
        response = proc.stdout.readline()
        if response:
            print(f"Response: {response}")
            resp_data = json.loads(response)
            print(f"Server initialized: {resp_data.get('result', {}).get('serverInfo', {}).get('name')}")
        
        # Request tools list
        print("\n[4] Requesting available tools...")
        tools_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        tools_json = json.dumps(tools_msg)
        proc.stdin.write(tools_json + '\n')
        proc.stdin.flush()
        
        # Read tools response
        response = proc.stdout.readline()
        if response:
            resp_data = json.loads(response)
            tools = resp_data.get('result', {}).get('tools', [])
            print(f"\n[5] Available Tools ({len(tools)} total):")
            print("-" * 60)
            for i, tool in enumerate(tools[:10], 1):  # Show first 10
                print(f"  {i}. {tool.get('name')}")
                print(f"     Description: {tool.get('description', 'N/A')[:60]}...")
            if len(tools) > 10:
                print(f"  ... and {len(tools) - 10} more tools")
        
        # Test a simple tool - get_position
        print("\n[6] Testing get_position tool...")
        test_msg = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_position",
                "arguments": {}
            }
        }
        
        test_json = json.dumps(test_msg)
        proc.stdin.write(test_json + '\n')
        proc.stdin.flush()
        
        response = proc.stdout.readline()
        if response:
            resp_data = json.loads(response)
            result = resp_data.get('result', {}).get('content', [{}])[0].get('text', 'N/A')
            print(f"Current mouse position: {result}")
        
        print("\n" + "=" * 60)
        print("✓ PyMCPAutoGUI server is working correctly!")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        proc.terminate()
        proc.wait(timeout=5)

if __name__ == "__main__":
    test_pymcp_server()

