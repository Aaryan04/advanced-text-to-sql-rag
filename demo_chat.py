#!/usr/bin/env python3
"""
Demo script to test the chat interface functionality
"""
import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8001"

def test_chat_queries():
    """Test various chat queries to demonstrate functionality"""
    
    queries = [
        "Show me all employees in the Engineering department",
        "What's the average salary by department?",
        "Find the top 5 highest paid employees",
        "List all active projects with their budgets",
        "Show me employees hired in the last year",
        "Which department has the most employees?"
    ]
    
    print("🚀 Testing Chat Interface Queries")
    print("=" * 50)
    
    for i, query in enumerate(queries, 1):
        print(f"\n💬 Query {i}: {query}")
        print("-" * 40)
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/query",
                json={
                    "question": query,
                    "include_explanation": True,
                    "max_results": 10
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"🔍 Generated SQL: {data.get('sql_query', 'N/A')}")
                print(f"📊 Results: {len(data.get('results', []))} rows")
                print(f"⭐ Confidence: {data.get('confidence_score', 0):.2%}")
                print(f"⚡ Execution Time: {data.get('execution_time', 0)*1000:.1f}ms")
                
                if data.get('results'):
                    print("📋 Sample Results:")
                    for row in data['results'][:3]:  # Show first 3 rows
                        print(f"   {row}")
                
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        time.sleep(1)  # Brief pause between queries
    
    print("\n✅ Chat interface demo completed!")

if __name__ == "__main__":
    # Check if backend is running
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Backend is healthy and ready")
            test_chat_queries()
        else:
            print("❌ Backend health check failed")
    except Exception as e:
        print(f"❌ Cannot connect to backend: {str(e)}")
        print("Make sure the backend is running on http://localhost:8001")