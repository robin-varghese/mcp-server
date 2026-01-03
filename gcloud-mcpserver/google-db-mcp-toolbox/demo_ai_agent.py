#!/usr/bin/env python3
"""
AI Agent Demo: Natural Language Queries to Student Database via MCP

This demonstrates how an AI agent (Claude, GPT, Gemini) would use the MCP Toolbox
to answer natural language questions about student data.

TOOLS.YAML STRUCTURE EXPLANATION:
==================================

The config/tools.yaml file defines how the MCP server connects to databases
and what operations (tools) are exposed to AI agents. Here's what each key means:

1. SOURCES Section
------------------
Defines database connections that tools can use.

sources:
  local_postgres:              # Unique identifier for this database connection
    kind: postgres             # Database type (postgres, mysql, bigquery, etc.)
    host: db                   # Hostname (use 'db' for docker-compose network)
    port: 5432                 # Database port
    user: postgres             # Database username
    password: postgres         # Database password (use secrets in production!)
    database: postgres         # Database name to connect to

2. TOOLS Section
----------------
Defines SQL operations that AI agents can invoke.

Each tool has these keys:

tools:
  tool_name:                   # Unique identifier for the tool
    kind: postgres-sql         # Tool type (postgres-sql, mysql-sql, etc.)
    description: "..."         # Human-readable description for AI agents
    source: local_postgres     # Which database connection to use (from sources)
    
    # Optional: Parameters that can be passed to the tool
    parameters:
      - name: param_name       # Parameter identifier
        type: integer          # Data type (string, integer, boolean)
        description: "..."     # What this parameter is for
    
    # The SQL query to execute
    statement: |
      SELECT * FROM table
      WHERE column = $1;       # $1, $2, etc. are positional parameter placeholders

KEY CONCEPTS:
-------------
- Tools without parameters: Execute fixed queries (e.g., "list all students")
- Tools with parameters: Allow dynamic queries (e.g., "search by name")
- Parameter substitution: Use $1, $2, $3 for PostgreSQL positional parameters
- Security: Only expose safe, read-only queries to AI agents
- Descriptions: AI uses these to understand when to call each tool

EXAMPLE TOOL DEFINITION:
------------------------
get_top_performers:
  kind: postgres-sql
  description: Get top performing students based on average marks
  source: local_postgres
  parameters:
    - name: limit_count
      type: integer
      description: Number of top students to return
  statement: |
    SELECT student_name, 
      ROUND((mathematics + physics + chemistry + biology + english) / 5.0, 2) as avg
    FROM students
    ORDER BY avg DESC
    LIMIT $1;

When AI agent calls: get_top_performers(limit_count=3)
SQL executed: SELECT ... LIMIT 3;
"""

import asyncio
from toolbox_core import ToolboxClient

TOOLBOX_URL = "http://localhost:5001"

# Simulated NLP queries showing how natural language maps to MCP tools
# Each entry shows:
# - question: What the user asks in natural language
# - tool: Which tool from tools.yaml to call
# - params: What parameters to pass (maps to tools.yaml parameter definitions)

NLP_QUERIES = [
    {
        "question": "Who are the top 3 students by average marks?",
        "tool": "get_top_performers",
        "params": {"limit_count": 3}  # Passes 3 to the $1 placeholder in SQL
    },
    {
        "question": "Show me Emma Watson's grades",
        "tool": "search_student_by_name",
        "params": {"name_search": "Emma"}  # Passes 'Emma' to $1 in ILIKE clause
    },
    {
        "question": "What's the average mathematics score?",
        "tool": "get_subject_statistics",
        "params": {}  # No parameters - runs fixed SQL query
    },
    {
        "question": "Which students scored above 90 in physics?",
        "tool": "get_students_physics_above_threshold",
        "params": {"min_score": 90}  # Passes 90 to $1 in WHERE clause
    },
    {
        "question": "Show me all students with their marks",
        "tool": "get_all_students",
        "params": {}  # No parameters needed
    },
    {
        "question": "How are students performing by enrollment year?",
        "tool": "get_enrollment_year_stats",
        "params": {}  # No parameters - aggregates by year automatically
    }
]

async def demo_ai_agent_queries():
    """
    Simulates an AI agent processing natural language queries
    and using MCP tools to get database answers.
    """
    print("=" * 80)
    print("🤖 AI AGENT DEMO: Natural Language Database Queries via MCP")
    print("=" * 80)
    print("\nThis demonstrates how AI agents translate user questions into MCP tool calls\n")
    
    async with ToolboxClient(url=TOOLBOX_URL) as client:
        for i, query in enumerate(NLP_QUERIES, 1):
            print(f"\n{'─' * 80}")
            print(f"Query {i}/{len(NLP_QUERIES)}")
            print(f"{'─' * 80}")
            print(f"👤 User: \"{query['question']}\"")
            print(f"\n🤖 AI Agent thinks: I'll use the '{query['tool']}' tool")
            print(f"   Parameters: {query['params']}")
            
            try:
                # STEP 1: Load the tool definition from the MCP server
                # This reads the tool configuration from tools.yaml
                # The tool object contains:
                # - name: The tool identifier
                # - description: What the tool does
                # - parameters: Expected parameter schema
                # - The SQL statement template
                tool = await client.load_tool(name=query['tool'])
                
                # STEP 2: Invoke the tool with parameters
                # The SDK handles:
                # - Parameter validation (type checking)
                # - SQL parameter substitution ($1, $2, etc.)
                # - Executing the query via the database connection
                # - Returning results as JSON
                #
                # How parameter passing works:
                # - params = {"limit_count": 3} → SQL gets $1 = 3
                # - params = {"name_search": "Emma"} → SQL gets $1 = 'Emma'
                # - params = {} → No substitution, runs SQL as-is
                result = await tool(**query['params']) if query['params'] else await tool()
                
                print(f"\n✅ Result from database:")
                print(f"{result}")
                
                # Simulate AI formatting the response
                print(f"\n💬 AI Response to user:")
                print(f"   (In production, the AI would format this nicely)")
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
            
            # Pause between queries for readability
            await asyncio.sleep(1)
    
    print(f"\n{'=' * 80}")
    print("Demo complete! This shows how AI agents use MCP tools to:")
    print("  1. Understand natural language questions")
    print("  2. Select the appropriate pre-defined tool")
    print("  3. Execute safe, validated database queries")  
    print("  4. Return structured results to format for users")
    print("=" * 80)

if __name__ == "__main__":
    print("\n🚀 Starting AI Agent Demo...")
    print("   (Make sure docker-compose is running)\n")
    
    try:
        asyncio.run(demo_ai_agent_queries())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. docker-compose is running: cd google-db-mcp-toolbox && docker-compose up -d")
        print("  2. Students table exists: docker exec -i google-db-mcp-toolbox-db-1 psql -U postgres -d postgres < setup_students.sql")
