import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    def test_health_endpoint_success(self, client):
        """Test that health endpoint returns success status."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "components" in data
        assert data["components"]["database"] is True
        assert data["components"]["rag_system"] is True
        assert data["components"]["workflow"] is True

    def test_health_endpoint_response_structure(self, client):
        """Test that health endpoint returns correct response structure."""
        response = client.get("/health")
        data = response.json()
        
        required_fields = ["status", "timestamp", "components"]
        for field in required_fields:
            assert field in data
        
        component_fields = ["database", "rag_system", "workflow"]
        for field in component_fields:
            assert field in data["components"]


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_endpoint(self, client):
        """Test that root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "Text-to-SQL RAG System" in data["message"]


class TestQueryEndpoint:
    """Tests for the query execution endpoint."""
    
    def test_query_endpoint_success(self, client, sample_query_request):
        """Test successful query execution."""
        response = client.post("/query", json=sample_query_request)
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["sql_query", "results", "explanation", "confidence_score", "execution_time", "metadata"]
        for field in required_fields:
            assert field in data
        
        assert isinstance(data["results"], list)
        assert isinstance(data["confidence_score"], float)
        assert isinstance(data["execution_time"], float)
        assert isinstance(data["metadata"], dict)

    def test_query_endpoint_engineering_filter(self, client):
        """Test query with engineering department filter."""
        request_data = {
            "question": "Show all employees in engineering",
            "include_explanation": True,
            "max_results": 100
        }
        
        response = client.post("/query", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "engineering" in data["sql_query"].lower()
        assert len(data["results"]) > 0
        
        # Check that all results are from engineering department
        for result in data["results"]:
            assert result["department"] == "Engineering"

    def test_query_endpoint_salary_analytics(self, client, sample_analytics_query):
        """Test analytics query for salary information."""
        response = client.post("/query", json=sample_analytics_query)
        assert response.status_code == 200
        
        data = response.json()
        assert "avg" in data["sql_query"].lower() or "average" in data["sql_query"].lower()
        assert "salary" in data["sql_query"].lower()
        assert len(data["results"]) > 0

    def test_query_endpoint_complex_query(self, client, sample_complex_query):
        """Test complex query with sorting and limiting."""
        response = client.post("/query", json=sample_complex_query)
        assert response.status_code == 200
        
        data = response.json()
        assert "order by" in data["sql_query"].lower() or "top" in data["sql_query"].lower()
        assert len(data["results"]) <= 5

    def test_query_endpoint_empty_question(self, client):
        """Test query endpoint with empty question."""
        request_data = {
            "question": "",
            "include_explanation": True,
            "max_results": 100
        }
        
        response = client.post("/query", json=request_data)
        # Should still return 200 but with default query
        assert response.status_code == 200

    def test_query_endpoint_invalid_request(self, client):
        """Test query endpoint with invalid request format."""
        response = client.post("/query", json={})
        assert response.status_code == 422  # Validation error

    def test_query_endpoint_max_results_limit(self, client):
        """Test query endpoint respects max_results parameter."""
        request_data = {
            "question": "Show all employees",
            "include_explanation": True,
            "max_results": 3
        }
        
        response = client.post("/query", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["results"]) <= 3

    def test_query_endpoint_metadata_structure(self, client, sample_query_request):
        """Test that query endpoint returns proper metadata structure."""
        response = client.post("/query", json=sample_query_request)
        data = response.json()
        
        metadata = data["metadata"]
        expected_fields = ["complexity", "validation_passed", "optimization_applied", "retry_count"]
        for field in expected_fields:
            assert field in metadata


class TestSchemaEndpoint:
    """Tests for the database schema endpoint."""
    
    def test_schema_endpoint_success(self, client):
        """Test successful schema retrieval."""
        response = client.get("/schema")
        assert response.status_code == 200
        
        data = response.json()
        assert "schema" in data
        assert isinstance(data["schema"], dict)
        
        # Check that we have expected tables
        schema = data["schema"]
        expected_tables = ["employees", "departments"]
        for table in expected_tables:
            assert table in schema

    def test_schema_endpoint_table_structure(self, client):
        """Test that schema endpoint returns proper table structure."""
        response = client.get("/schema")
        data = response.json()
        
        schema = data["schema"]
        for table_name, table_info in schema.items():
            assert "columns" in table_info
            assert "sample_data" in table_info
            assert isinstance(table_info["columns"], list)
            assert isinstance(table_info["sample_data"], list)
            
            # Check column structure
            for column in table_info["columns"]:
                required_column_fields = ["name", "type", "nullable", "default"]
                for field in required_column_fields:
                    assert field in column

    def test_schema_endpoint_employees_table(self, client):
        """Test specific structure of employees table in schema."""
        response = client.get("/schema")
        data = response.json()
        
        employees_table = data["schema"]["employees"]
        column_names = [col["name"] for col in employees_table["columns"]]
        
        expected_columns = ["id", "first_name", "last_name", "email", "department", "salary", "hire_date"]
        for col in expected_columns:
            assert col in column_names


class TestTablesEndpoint:
    """Tests for the tables listing endpoint."""
    
    def test_tables_endpoint_success(self, client):
        """Test successful tables listing."""
        response = client.get("/tables")
        assert response.status_code == 200
        
        data = response.json()
        assert "tables" in data
        assert isinstance(data["tables"], list)
        
        expected_tables = ["employees", "departments"]
        for table in expected_tables:
            assert table in data["tables"]

    def test_tables_endpoint_response_format(self, client):
        """Test that tables endpoint returns correct format."""
        response = client.get("/tables")
        data = response.json()
        
        tables = data["tables"]
        assert len(tables) > 0
        
        # All table names should be strings
        for table in tables:
            assert isinstance(table, str)


class TestQueryHistoryEndpoint:
    """Tests for the query history endpoint."""
    
    def test_query_history_endpoint_success(self, client):
        """Test successful query history retrieval."""
        response = client.get("/query-history")
        assert response.status_code == 200
        
        data = response.json()
        assert "history" in data
        assert isinstance(data["history"], list)

    def test_query_history_endpoint_with_limit(self, client):
        """Test query history endpoint with limit parameter."""
        response = client.get("/query-history?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["history"]) <= 5

    def test_query_history_entry_structure(self, client):
        """Test structure of query history entries."""
        response = client.get("/query-history")
        data = response.json()
        
        if data["history"]:  # If there are history entries
            entry = data["history"][0]
            expected_fields = ["id", "question", "sql_query", "results_count", 
                             "execution_time", "confidence_score", "created_at", "success"]
            
            for field in expected_fields:
                assert field in entry


class TestAPIErrorHandling:
    """Tests for API error handling."""
    
    def test_invalid_endpoint(self, client):
        """Test request to invalid endpoint."""
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404

    def test_invalid_method(self, client):
        """Test invalid HTTP method on valid endpoint."""
        response = client.delete("/query")
        assert response.status_code == 405

    def test_malformed_json(self, client):
        """Test request with malformed JSON."""
        response = client.post("/query", data="invalid json")
        assert response.status_code == 422

    def test_missing_content_type(self, client):
        """Test POST request without proper content type."""
        response = client.post("/query", data=json.dumps({"question": "test"}))
        assert response.status_code == 422


class TestAPIResponseTimes:
    """Tests for API response times and performance."""
    
    def test_health_endpoint_response_time(self, client):
        """Test that health endpoint responds quickly."""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second

    def test_query_endpoint_response_time(self, client, sample_query_request):
        """Test that query endpoint responds within reasonable time."""
        import time
        
        start_time = time.time()
        response = client.post("/query", json=sample_query_request)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 5.0  # Should respond within 5 seconds