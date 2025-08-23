# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Start the application:**
```bash
./run.sh
```
Or manually:
```bash
cd backend && uv run uvicorn app:app --reload --port 8000
```

**Install dependencies:**
```bash
uv sync
```

**Environment setup:**
Copy `.env.example` to `.env` and add your `ANTHROPIC_API_KEY`.

## Architecture Overview

This is a RAG (Retrieval-Augmented Generation) chatbot system with a clear separation between frontend and backend:

### Core Components

**RAGSystem (backend/rag_system.py)**: Main orchestrator that coordinates all components. Handles document ingestion from `docs/` folder on startup and query processing through tool-based search.

**VectorStore (backend/vector_store.py)**: ChromaDB wrapper for semantic search using embeddings. Stores both course metadata and chunked content with the `all-MiniLM-L6-v2` model.

**AIGenerator (backend/ai_generator.py)**: Anthropic Claude integration using the `claude-sonnet-4-20250514` model. Supports tool calling for structured search operations.

**DocumentProcessor (backend/document_processor.py)**: Converts course documents (.txt, .pdf, .docx) into structured `Course`, `Lesson`, and `CourseChunk` objects with configurable chunking (800 chars, 100 overlap).

**SessionManager (backend/session_manager.py)**: Maintains conversation history (max 2 exchanges) for context-aware responses.

**ToolManager + CourseSearchTool (backend/search_tools.py)**: Implements function calling for Claude to perform semantic searches against the vector store.

### Data Flow

1. **Document Ingestion**: Startup processes `docs/` → DocumentProcessor → VectorStore
2. **Query Processing**: User query → RAGSystem → ToolManager → VectorStore search → Claude generation → Response
3. **Session Management**: Each conversation maintains context through SessionManager

### Frontend Integration

The FastAPI backend serves both API endpoints (`/api/query`, `/api/courses`) and static frontend files. The frontend uses vanilla JavaScript with real-time chat interface.

## Key Configuration

**Models**: Claude Sonnet 4 for generation, all-MiniLM-L6-v2 for embeddings
**Storage**: ChromaDB in `./chroma_db` directory
**Document Sources**: `docs/` folder processed automatically on startup
**API**: FastAPI with CORS enabled for development

## Data Models

**Course**: Contains title, instructor, lessons, and course_link
**Lesson**: Has lesson_number, title, and optional lesson_link  
**CourseChunk**: Text content with course_title, lesson_number, and chunk_index for precise attribution

The system maintains referential integrity between courses, lessons, and chunks for accurate source attribution in responses.