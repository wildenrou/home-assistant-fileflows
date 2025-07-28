#!/usr/bin/env python3
"""
Enhanced test script for FileFlows API to discover all available endpoints.
This will help identify which additional endpoints are available on your server.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

async def test_enhanced_fileflows_api():
    """Test all potential FileFlows API endpoints."""
    
    host = "192.168.1.18"
    port = 8585
    base_url = f"http://{host}:{port}"
    
    # List of endpoints to test based on FileFlows documentation and common patterns
    endpoints_to_test = [
        # Core endpoints
        "/api/status",
        "/api/help",
        
        # System information
        "/api/system",
        "/api/system/info",
        "/api/info",
        "/api/version",
        
        # Flows and libraries
        "/api/flows",
        "/api/libraries",
        "/api/library",
        
        # Nodes and workers
        "/api/nodes",
        "/api/workers",
        "/api/node",
        "/api/worker",
        
        # Statistics and monitoring
        "/api/statistics",
        "/api/stats", 
        "/api/dashboard",
        "/api/dashboard/statistics",
        
        # Settings and configuration
        "/api/settings",
        "/api/config",
        "/api/configuration",
        
        # Plugins
        "/api/plugins",
        "/api/plugin",
        
        # Files and history
        "/api/files",
        "/api/file",
        "/api/history",
        "/api/file-history",
        
        # Logs
        "/api/logs",
        "/api/log",
        
        # Control endpoints
        "/api/pause",
        "/api/resume",
        "/api/start",
        "/api/stop",
        
        # Additional potential endpoints
        "/api/queue",
        "/api/processing",
        "/api/tasks",
        "/api/jobs",
        "/api/variables",
        "/api/scripts",
        "/api/templates",
    ]
    
    print(f"🔍 Testing FileFlows API at {base_url}")
    print("=" * 80)
    
    working_endpoints = []
    error_endpoints = []
    
    try:
        timeout = aiohttp.ClientTimeout(total=10, connect=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "FileFlows Enhanced Test Script"
            }
            
            for endpoint in endpoints_to_test:
                url = f"{base_url}{endpoint}"
                try:
                    async with session.get(url, headers=headers) as response:
                        content_type = response.headers.get('content-type', 'unknown')
                        
                        if response.status == 200:
                            try:
                                text = await response.text()
                                
                                # Try to parse as JSON
                                if 'application/json' in content_type or text.strip().startswith(('{', '[')):
                                    data = json.loads(text)
                                    print(f"✅ {endpoint}")
                                    print(f"   📊 Data type: {type(data).__name__}")
                                    
                                    # Show key information about the response
                                    if isinstance(data, dict):
                                        keys = list(data.keys())[:5]  # Show first 5 keys
                                        print(f"   🔑 Keys: {keys}")
                                        if len(data.keys()) > 5:
                                            print(f"   📝 Total keys: {len(data.keys())}")
                                    elif isinstance(data, list):
                                        print(f"   📝 Array length: {len(data)}")
                                        if data and isinstance(data[0], dict):
                                            keys = list(data[0].keys())[:3]
                                            print(f"   🔑 Item keys: {keys}")
                                    
                                    working_endpoints.append((endpoint, data))
                                else:
                                    # Non-JSON response
                                    print(f"✅ {endpoint} (Non-JSON)")
                                    print(f"   📄 Content-Type: {content_type}")
                                    print(f"   📝 Length: {len(text)} chars")
                                    working_endpoints.append((endpoint, {"content": text[:200]}))
                                    
                            except json.JSONDecodeError:
                                print(f"⚠️  {endpoint} - Valid response but not JSON")
                                text = await response.text()
                                working_endpoints.append((endpoint, {"raw_content": text[:200]}))
                                
                        elif response.status == 404:
                            print(f"❌ {endpoint} - Not Found")
                            error_endpoints.append((endpoint, "404 Not Found"))
                        elif response.status == 405:
                            print(f"🔒 {endpoint} - Method Not Allowed (might work with POST)")
                            error_endpoints.append((endpoint, "405 Method Not Allowed"))
                        else:
                            print(f"❌ {endpoint} - HTTP {response.status}")
                            error_endpoints.append((endpoint, f"HTTP {response.status}"))
                            
                except asyncio.TimeoutError:
                    print(f"⏰ {endpoint} - Timeout")
                    error_endpoints.append((endpoint, "Timeout"))
                except Exception as e:
                    print(f"❌ {endpoint} - Error: {e}")
                    error_endpoints.append((endpoint, str(e)))
                
                # Small delay to be nice to the server
                await asyncio.sleep(0.1)
    
    except Exception as e:
        print(f"❌ Failed to create session: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    
    print(f"✅ Working endpoints: {len(working_endpoints)}")
    for endpoint, _ in working_endpoints:
        print(f"   {endpoint}")
    
    print(f"\n❌ Non-working endpoints: {len(error_endpoints)}")
    for endpoint, error in error_endpoints:
        print(f"   {endpoint} - {error}")
    
    # Show detailed data for key endpoints
    print("\n" + "=" * 80)
    print("📋 DETAILED DATA FOR KEY ENDPOINTS")
    print("=" * 80)
    
    key_endpoints = ["/api/status", "/api/flows", "/api/libraries", "/api/nodes", "/api/statistics"]
    
    for endpoint_name, endpoint_data in working_endpoints:
        if endpoint_name in key_endpoints:
            print(f"\n🔍 {endpoint_name}:")
            if isinstance(endpoint_data, dict):
                # Pretty print first level of data
                for key, value in list(endpoint_data.items())[:10]:  # Limit to 10 items
                    if isinstance(value, (dict, list)):
                        print(f"   {key}: {type(value).__name__} ({len(value)} items)")
                    else:
                        print(f"   {key}: {value}")
    
    print("\n" + "=" * 80)
    print("🎯 INTEGRATION RECOMMENDATIONS")
    print("=" * 80)
    
    recommendations = []
    
    # Check what additional data is available
    endpoint_data_map = {endpoint: data for endpoint, data in working_endpoints}
    
    if "/api/flows" in endpoint_data_map:
        recommendations.append("✅ Flows endpoint available - can add flow count sensor")
    
    if "/api/libraries" in endpoint_data_map:
        recommendations.append("✅ Libraries endpoint available - can add library count sensor")
        
    if "/api/nodes" in endpoint_data_map or "/api/workers" in endpoint_data_map:
        recommendations.append("✅ Nodes/Workers endpoint available - can add node status sensors")
        
    if "/api/statistics" in endpoint_data_map:
        recommendations.append("✅ Statistics endpoint available - can add detailed stats sensors")
        
    if "/api/system" in endpoint_data_map or "/api/info" in endpoint_data_map:
        recommendations.append("✅ System info endpoint available - can add version info")
        
    if "/api/pause" in [e for e, _ in working_endpoints] or "/api/resume" in [e for e, _ in working_endpoints]:
        recommendations.append("✅ Control endpoints available - can add pause/resume services")
    
    for rec in recommendations:
        print(rec)
    
    if not recommendations:
        print("ℹ️  Only basic status endpoint available - integration will work with current sensors")
    
    return len(working_endpoints) > 0

async def main():
    """Main test function."""
    print("FileFlows Enhanced API Discovery")
    print("=" * 80)
    
    success = await test_enhanced_fileflows_api()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 Discovery completed successfully!")
        print("✅ Use the results above to optimize your FileFlows integration")
    else:
        print("❌ Discovery failed")
        print("❌ Check your FileFlows server connection")

if __name__ == "__main__":
    asyncio.run(main())
