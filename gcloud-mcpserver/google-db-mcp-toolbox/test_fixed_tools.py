#!/usr/bin/env python3
"""
Test Fixed Parameterized Tools
"""

import asyncio
from toolbox_core import ToolboxClient

TOOLBOX_URL = "http://localhost:5001"

async def test_fixed_tools():
    """Test the fixed parameterized tools."""
    
    print("=" * 80)
    print("🔧 Testing Fixed Parameterized MCP Tools")
    print("=" * 80)
    
    async with ToolboxClient(url=TOOLBOX_URL) as client:
        
        # Test 1: Top performers
        print("\n" + "─" * 80)
        print("Test 1: Get top 3 students")
        print("─" * 80)
        try:
            tool = await client.load_tool(name="get_top_performers")
            result = await tool(limit_count=3)
            print(f"✅ Result: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: Search by name
        print("\n" + "─" * 80)
        print("Test 2: Search for 'Emma'")
        print("─" * 80)
        try:
            tool = await client.load_tool(name="search_student_by_name")
            result = await tool(name_search="Emma")
            print(f"✅ Result: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: Mathematics statistics
        print("\n" + "─" * 80)
        print("Test 3: Mathematics statistics")
        print("─" * 80)
        try:
            tool = await client.load_tool(name="get_subject_statistics")
            result = await tool()
            print(f"✅ Result: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 4: Students above threshold in physics
        print("\n" + "─" * 80)
        print("Test 4: Students with physics > 90")
        print("─" * 80)
        try:
            tool = await client.load_tool(name="get_students_physics_above_threshold")
            result = await tool(min_score=90)
            print(f"✅ Result: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("Testing complete!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_fixed_tools())
