#!/usr/bin/env python3
"""
Test script to check Neo4j connection and authorization.
Run this script to verify your Neo4j setup.
"""

import sys
import os

# Add src directory to path so we can import neo4j_graph
sys.path.append('src')

try:
    from neo4j_graph import get_connection_info, test_connection
    print("🔍 Testing Neo4j Connection...")
    print("=" * 50)
    
    # Display connection info and test
    success = get_connection_info()
    
    if success:
        print("\n🎉 Your Neo4j connection is working properly!")
    else:
        print("\n⚠️  Connection failed. Please check:")
        print("1. Is Neo4j running? (Check with: neo4j status)")
        print("2. Are your environment variables set correctly?")
        print("3. Is the URI correct? (should be 'neo4j://localhost:7687' for local)")
        print("4. Are your username and password correct?")
        
        print("\n💡 To set up environment variables, create a .env file with:")
        print("NEO4J_URI=neo4j://localhost:7687")
        print("NEO4J_USERNAME=neo4j")
        print("NEO4J_PASSWORD=your_password")
        
except ImportError as e:
    print(f"❌ Error importing neo4j_graph: {e}")
    print("Make sure you're running this from the project root directory.")
except Exception as e:
    print(f"❌ Unexpected error: {e}")



