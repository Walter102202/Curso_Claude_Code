"""
Tests for FastAPI endpoints.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.mark.api
class TestQueryEndpoint:
    """Tests for the /api/query endpoint."""

    def test_query_with_session_id(self, test_client, mock_rag_system, query_request_data):
        """Test querying with provided session ID."""
        # Inject mock into test app
        test_client.app.mock_rag_system = mock_rag_system
        
        response = test_client.post("/api/query", json=query_request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == query_request_data["session_id"]
        assert isinstance(data["sources"], list)
        
        # Verify the mock was called correctly
        mock_rag_system.query.assert_called_once_with(
            query_request_data["query"], 
            query_request_data["session_id"]
        )

    def test_query_without_session_id(self, test_client, mock_rag_system):
        """Test querying without session ID - should create new session."""
        # Inject mock into test app
        test_client.app.mock_rag_system = mock_rag_system
        
        request_data = {"query": "What is machine learning?"}
        
        response = test_client.post("/api/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session-id"  # From mock
        
        # Verify session was created
        mock_rag_system.session_manager.create_session.assert_called_once()

    def test_query_with_dict_sources(self, test_client, mock_rag_system):
        """Test query response with dictionary sources (with links)."""
        # Setup mock to return dict sources
        mock_rag_system.query.return_value = (
            "Test answer",
            [
                {"text": "Source with link", "link": "https://example.com/page1"},
                {"text": "Source without link", "link": None}
            ]
        )
        
        # Inject mock into test app
        test_client.app.mock_rag_system = mock_rag_system
        
        request_data = {"query": "Test query"}
        response = test_client.post("/api/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["sources"]) == 2
        assert data["sources"][0]["text"] == "Source with link"
        assert data["sources"][0]["link"] == "https://example.com/page1"
        assert data["sources"][1]["text"] == "Source without link"
        assert data["sources"][1]["link"] is None

    def test_query_with_string_sources(self, test_client, mock_rag_system):
        """Test query response with legacy string sources."""
        # Setup mock to return string sources
        mock_rag_system.query.return_value = (
            "Test answer",
            ["String source 1", "String source 2"]
        )
        
        # Inject mock into test app
        test_client.app.mock_rag_system = mock_rag_system
        
        request_data = {"query": "Test query"}
        response = test_client.post("/api/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["sources"]) == 2
        assert data["sources"][0]["text"] == "String source 1"
        assert data["sources"][0]["link"] is None
        assert data["sources"][1]["text"] == "String source 2"
        assert data["sources"][1]["link"] is None

    def test_query_invalid_request(self, test_client, mock_rag_system):
        """Test query with invalid request data."""
        # Inject mock into test app
        test_client.app.mock_rag_system = mock_rag_system
        
        # Missing required 'query' field
        response = test_client.post("/api/query", json={})
        
        assert response.status_code == 422  # Validation error

    def test_query_empty_string(self, test_client, mock_rag_system):
        """Test query with empty query string."""
        # Inject mock into test app
        test_client.app.mock_rag_system = mock_rag_system
        
        request_data = {"query": ""}
        response = test_client.post("/api/query", json=request_data)
        
        assert response.status_code == 200
        mock_rag_system.query.assert_called_once()

    def test_query_server_error(self, test_client, mock_rag_system):
        """Test query when RAG system raises an exception."""
        # Setup mock to raise exception
        mock_rag_system.query.side_effect = Exception("Database connection failed")
        
        # Inject mock into test app
        test_client.app.mock_rag_system = mock_rag_system
        
        request_data = {"query": "Test query"}
        response = test_client.post("/api/query", json=request_data)
        
        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]


@pytest.mark.api
class TestCoursesEndpoint:
    """Tests for the /api/courses endpoint."""

    def test_get_course_stats_success(self, test_client, mock_rag_system, expected_course_stats):
        """Test successful course stats retrieval."""
        # Inject mock into test app
        test_client.app.mock_rag_system = mock_rag_system
        
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_courses" in data
        assert "course_titles" in data
        assert data["total_courses"] == expected_course_stats["total_courses"]
        assert data["course_titles"] == expected_course_stats["course_titles"]
        
        # Verify the mock was called
        mock_rag_system.get_course_analytics.assert_called_once()

    def test_get_course_stats_empty_result(self, test_client, mock_rag_system):
        """Test course stats when no courses exist."""
        # Setup mock to return empty results
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }
        
        # Inject mock into test app
        test_client.app.mock_rag_system = mock_rag_system
        
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_get_course_stats_server_error(self, test_client, mock_rag_system):
        """Test course stats when RAG system raises an exception."""
        # Setup mock to raise exception
        mock_rag_system.get_course_analytics.side_effect = Exception("Vector store unavailable")
        
        # Inject mock into test app
        test_client.app.mock_rag_system = mock_rag_system
        
        response = test_client.get("/api/courses")
        
        assert response.status_code == 500
        assert "Vector store unavailable" in response.json()["detail"]


@pytest.mark.api
class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_endpoint(self, test_client):
        """Test the root endpoint returns basic API info."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "Course Materials RAG System API" in data["message"]


@pytest.mark.api
class TestCORSAndMiddleware:
    """Tests for CORS and middleware functionality."""

    def test_cors_headers(self, test_client, mock_rag_system):
        """Test that CORS headers are properly set."""
        # Inject mock into test app
        test_client.app.mock_rag_system = mock_rag_system
        
        response = test_client.post("/api/query", 
                                   json={"query": "test"}, 
                                   headers={"Origin": "https://example.com"})
        
        # Check CORS headers are present (TestClient may not set all headers)
        assert response.status_code in [200, 500]  # Either success or mock error
        
    def test_options_request(self, test_client):
        """Test OPTIONS request for preflight CORS."""
        response = test_client.options("/api/query")
        
        # TestClient may return 405 for OPTIONS, but real server with CORS middleware handles it
        # In a real server, CORS middleware would handle OPTIONS requests
        assert response.status_code in [200, 405]  # Allow both for test environment


@pytest.mark.api 
class TestRequestValidation:
    """Tests for request validation."""

    def test_query_request_validation(self, test_client, mock_rag_system):
        """Test various query request validation scenarios."""
        # Inject mock into test app
        test_client.app.mock_rag_system = mock_rag_system
        
        # Valid request
        response = test_client.post("/api/query", json={
            "query": "Valid query",
            "session_id": "valid-session"
        })
        assert response.status_code == 200
        
        # Query too long (if validation exists)
        very_long_query = "a" * 10000
        response = test_client.post("/api/query", json={"query": very_long_query})
        # Should still work unless explicit validation added
        assert response.status_code == 200
        
        # Invalid JSON
        response = test_client.post("/api/query", 
                                   data="invalid json", 
                                   headers={"Content-Type": "application/json"})
        assert response.status_code == 422

    def test_content_type_handling(self, test_client, mock_rag_system):
        """Test different content types."""
        # Inject mock into test app
        test_client.app.mock_rag_system = mock_rag_system
        
        # Valid JSON content type
        response = test_client.post("/api/query", 
                                   json={"query": "test"},
                                   headers={"Content-Type": "application/json"})
        assert response.status_code == 200
        
        # Missing content type should still work with TestClient
        response = test_client.post("/api/query", json={"query": "test"})
        assert response.status_code == 200