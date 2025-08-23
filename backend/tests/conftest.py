"""
Shared pytest fixtures for the RAG system tests.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Generator, Dict, Any

from fastapi.testclient import TestClient
from config import config
from models import Course, Lesson, CourseChunk


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    mock_cfg = Mock()
    mock_cfg.CHUNK_SIZE = 800
    mock_cfg.CHUNK_OVERLAP = 100
    mock_cfg.CHROMA_PATH = ":memory:"
    mock_cfg.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    mock_cfg.MAX_RESULTS = 10
    mock_cfg.ANTHROPIC_API_KEY = "test-api-key"
    mock_cfg.ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
    mock_cfg.MAX_HISTORY = 2
    return mock_cfg


@pytest.fixture
def sample_course():
    """Sample course data for testing."""
    lessons = [
        Lesson(lesson_number=1, title="Introduction", lesson_link="https://example.com/lesson1"),
        Lesson(lesson_number=2, title="Advanced Topics", lesson_link="https://example.com/lesson2")
    ]
    return Course(
        title="Test Course",
        instructor="Test Instructor",
        lessons=lessons,
        course_link="https://example.com/course"
    )


@pytest.fixture
def sample_chunks(sample_course):
    """Sample course chunks for testing."""
    return [
        CourseChunk(
            course_title="Test Course",
            lesson_number=1,
            chunk_index=0,
            text="This is the introduction lesson content."
        ),
        CourseChunk(
            course_title="Test Course",
            lesson_number=1,
            chunk_index=1,
            text="More introduction content with detailed explanations."
        ),
        CourseChunk(
            course_title="Test Course",
            lesson_number=2,
            chunk_index=0,
            text="Advanced topics covering complex concepts."
        )
    ]


@pytest.fixture
def temp_docs_dir():
    """Create temporary directory with sample documents."""
    temp_dir = tempfile.mkdtemp()
    docs_path = Path(temp_dir)
    
    # Create sample document files
    (docs_path / "course1.txt").write_text(
        "Course: Test Course 1\nInstructor: John Doe\n\n"
        "Lesson 1: Introduction\nThis is lesson 1 content.\n\n"
        "Lesson 2: Advanced Topics\nThis is lesson 2 content."
    )
    
    (docs_path / "course2.txt").write_text(
        "Course: Test Course 2\nInstructor: Jane Smith\n\n"
        "Lesson 1: Basics\nBasic concepts explained here.\n\n"
        "Lesson 2: Intermediate\nIntermediate level content."
    )
    
    yield str(docs_path)
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_vector_store():
    """Mock VectorStore for testing."""
    mock_store = Mock()
    mock_store.add_course_metadata = Mock()
    mock_store.add_course_content = Mock()
    mock_store.search_content = Mock(return_value=[])
    mock_store.search_courses = Mock(return_value=[])
    mock_store.get_course_analytics = Mock(return_value={
        "total_courses": 2,
        "course_titles": ["Test Course 1", "Test Course 2"]
    })
    return mock_store


@pytest.fixture
def mock_ai_generator():
    """Mock AIGenerator for testing."""
    mock_ai = Mock()
    mock_ai.generate_response = AsyncMock(return_value="Test AI response")
    mock_ai.generate_response_with_tools = AsyncMock(return_value="Test AI response with tools")
    return mock_ai


@pytest.fixture
def mock_session_manager():
    """Mock SessionManager for testing."""
    mock_session = Mock()
    mock_session.create_session = Mock(return_value="test-session-id")
    mock_session.add_exchange = Mock()
    mock_session.get_history = Mock(return_value=[])
    return mock_session


@pytest.fixture
def mock_rag_system(mock_config, mock_vector_store, mock_ai_generator, mock_session_manager):
    """Mock RAGSystem for testing."""
    mock_rag = Mock()
    mock_rag.config = mock_config
    mock_rag.vector_store = mock_vector_store
    mock_rag.ai_generator = mock_ai_generator
    mock_rag.session_manager = mock_session_manager
    mock_rag.query = Mock(return_value=(
        "Test answer",
        [{"text": "Test source", "link": "https://example.com"}]
    ))
    mock_rag.get_course_analytics = Mock(return_value={
        "total_courses": 2,
        "course_titles": ["Test Course 1", "Test Course 2"]
    })
    mock_rag.add_course_folder = Mock(return_value=(2, 10))
    return mock_rag


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app without static file mounting."""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from pydantic import BaseModel
    from typing import List, Optional
    
    # Create a test app without static file dependencies
    test_app = FastAPI(title="Course Materials RAG System - Test", root_path="")
    
    # Add middleware
    test_app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Define request/response models
    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class SourceInfo(BaseModel):
        text: str
        link: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[SourceInfo]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]
    
    @test_app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            # Get the mock from app state
            mock_rag = getattr(test_app, 'mock_rag_system', None)
            if mock_rag is None:
                raise HTTPException(status_code=500, detail="Mock RAG system not configured")
                
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag.session_manager.create_session()
            
            answer, sources = mock_rag.query(request.query, session_id)
            
            source_objects = []
            for source in sources:
                if isinstance(source, dict):
                    source_objects.append(SourceInfo(text=source.get('text', ''), link=source.get('link')))
                else:
                    source_objects.append(SourceInfo(text=str(source), link=None))
            
            return QueryResponse(
                answer=answer,
                sources=source_objects,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @test_app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            # Get the mock from app state
            mock_rag = getattr(test_app, 'mock_rag_system', None)
            if mock_rag is None:
                raise HTTPException(status_code=500, detail="Mock RAG system not configured")
                
            analytics = mock_rag.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @test_app.get("/")
    async def root():
        return {"message": "Course Materials RAG System API"}
    
    # Store reference to inject mock in tests
    test_app.mock_rag_system = None
    
    return TestClient(test_app)


@pytest.fixture
def query_request_data():
    """Sample query request data for testing."""
    return {
        "query": "What is the main topic of the course?",
        "session_id": "test-session-123"
    }


@pytest.fixture
def expected_query_response():
    """Expected query response for testing."""
    return {
        "answer": "Test answer",
        "sources": [{"text": "Test source", "link": "https://example.com"}],
        "session_id": "test-session-123"
    }


@pytest.fixture
def expected_course_stats():
    """Expected course statistics for testing."""
    return {
        "total_courses": 2,
        "course_titles": ["Test Course 1", "Test Course 2"]
    }