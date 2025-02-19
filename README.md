# AI-Powered Document Diffing & Merging - Backend

A FastAPI-based backend that provides intelligent document comparison and merging capabilities using AI.

![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python)
![Anthropic](https://img.shields.io/badge/Anthropic%20Claude-3.5%20Sonnet-7F67BE)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-336791?logo=postgresql)

## Features

- **Document Management**: Upload, store, and retrieve text documents
- **Basic & Enhanced Diff**: Calculate differences between documents
- **AI-Powered Analysis**: Generate intelligent summaries of document changes
- **Smart Merge**: Apply AI to intelligently merge documents
- **Conflict Resolution**: Multiple strategies for resolving conflicting changes
- **Asynchronous Processing**: Background tasks for handling large documents
- **RESTful API**: Well-documented endpoints with comprehensive validation
- **Authentication**: JWT-based authentication system

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Anthropic API key

### Database Setup

Set up PostgreSQL using Docker:

```bash
docker run --name mypostgres \
    -e POSTGRES_USER=myuser \
    -e POSTGRES_PASSWORD=mypassword \
    -e POSTGRES_DB=mydatabase \
    -p 5432:5432 -d postgres
```

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd diffai-backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following contents:
   ```
   DATABASE_URL=postgresql://myuser:mypassword@localhost:5432/mydatabase
   SECRET_KEY=your-secret-key-for-jwt-tokens
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   AI_API_KEY=your-anthropic-api-key
   AI_MODEL_NAME=claude-3-5-sonnet-20241022
   AI_MAX_TOKENS=4096
   AI_ENABLED=true
   ```

### Running the Application

Start the development server:
```bash
uvicorn backend.app.main:app --reload
```

The API will be available at [http://localhost:8000](http://localhost:8000).

API documentation will be available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Architecture

### Directory Structure

```
backend/
├── app/
│   ├── endpoints/
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── diffs.py         # Diff and merge endpoints
│   │   └── documents.py     # Document management endpoints
│   ├── models/
│   │   └── document.py      # Database models
│   ├── services/
│   │   ├── ai_service.py    # AI integration service
│   │   └── diff_merge.py    # Diff and merge logic
│   ├── tasks/
│   │   └── background_tasks.py  # Asynchronous task processing
│   ├── config.py            # Application configuration
│   ├── database.py          # Database connection
│   ├── db_init.py           # Database initialization
│   └── main.py              # Application entry point
└── tests/                   # Test suite
```

### Key Technologies

- **FastAPI**: High-performance web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation and settings management
- **Anthropic Claude**: AI model for intelligent document analysis
- **PostgreSQL**: Relational database for data storage
- **PyJWT**: JWT token handling for authentication

## API Endpoints

### Authentication
- `POST /auth/login` - Authenticate user and get access token
- `GET /auth/me` - Get current user info

### Documents
- `POST /documents/upload` - Upload new document
- `GET /documents/` - List all documents
- `GET /documents/{doc_id}` - Get specific document
- `DELETE /documents/{doc_id}` - Delete document

### Diffs and Merges
- `GET /diffs/` - Get diff between two documents
- `POST /diffs/merge` - Merge two documents (synchronous)
- `POST /diffs/async-diff` - Create asynchronous diff task
- `POST /diffs/async-merge` - Create asynchronous merge task
- `GET /diffs/task-status/{task_id}` - Get task status
- `GET /diffs/merge-result/{task_id}` - Get merge result

## Background Processing

For large documents, the application uses background task processing:

1. Client submits an asynchronous request
2. Server creates a background task and returns a task ID
3. Client polls task status endpoint for progress updates
4. When complete, client retrieves the final result

This approach prevents timeouts and provides progress feedback for long-running operations.

## AI Integration

The application uses Anthropic's Claude model for:

- **Diff Analysis**: Generate human-readable summaries of document differences
- **Smart Merge**: Apply intelligent conflict resolution based on document context
- **Custom Rules**: Process natural language merge guidance

### AI Configuration

Adjust AI parameters in `.env`:
- `AI_API_KEY`: Your Anthropic API key
- `AI_MODEL_NAME`: Model to use (default: claude-3-5-sonnet-20241022)
- `AI_MAX_TOKENS`: Maximum tokens for responses
- `AI_ENABLED`: Toggle AI functionality

## Testing

Run the test suite:
```bash
pytest
```

The tests use a separate test database configured in `pytest.ini`.

## Deployment

### Docker

Build and run with Docker:
```bash
docker build -t diffai-backend .
docker run -p 8000:8000 --env-file .env diffai-backend
```

### Production Considerations

- Use a proper task queue (Celery, RQ) for production deployments
- Implement rate limiting for API endpoints
- Configure proper database connection pooling
- Set up monitoring and logging

## Troubleshooting

### Common Issues

**Database Connection Problems**:
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database user has proper permissions

**AI Service Errors**:
- Validate your Anthropic API key
- Check AI service availability
- Review rate limits and quotas

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

[MIT License](LICENSE)