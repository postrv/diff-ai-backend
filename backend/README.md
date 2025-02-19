# AI-Powered Document Diffing and Merging Platform

This platform enables users to compare and intelligently merge text documents using AI-powered analysis.

## Current Progress

### Backend (FastAPI + SQLAlchemy)
- ✅ Authentication system with JWT
- ✅ Document upload and management
- ✅ Basic and enhanced diff computation
- ✅ AI-powered diff analysis with Claude
- ✅ Background task processing
- ✅ Test suite covering core functionality

### Frontend (React + TypeScript + Material UI)
- ✅ Document upload with drag-and-drop
- ✅ Diff visualization (unified and side-by-side views)
- ✅ AI-powered diff summary display
- ✅ Merge goal setting interface
- ✅ Light/Dark mode toggle
- ✅ Responsive design for mobile/desktop

## Current Issues

1. **AI Summary Formatting**: AI-generated summaries include preamble text and need better formatting
2. **Merge Functionality**: Document merge doesn't function properly
3. **Timeout Issues**: Frontend times out while waiting for the summary 
4. **Processing Indication**: Need better loading indicators for long-running operations

## Next Steps

1. **Fix AI Summary Response Format**:
   - Update the `ai_service.py` to better parse AI responses
   - Implement proper formatting and remove preamble text

2. **Implement Robust Merge Functionality**:
   - Enhance the merge algorithm to properly apply user-defined strategies
   - Add error handling for merge failures
   - Implement content length limits to avoid context window issues

3. **Add Streaming or Progress Indicators**:
   - Implement either:
     - Server-sent events (SSE) for streaming responses, or
     - Enhanced background processing with frequent status updates
   - Add a visually appealing loading screen with progress indication

4. **Enhance Merge Result Visualization**:
   - Add color-coding for parts of the document changed by the merge
   - Implement before/after comparison view
   - Add the ability to manually edit merge results

## Setup Instructions

### Backend Setup
1. Create and activate a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies
   ```
   pip install -r requirements.txt
   ```

3. Configure environment variables in `.env` file
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/dbname
   SECRET_KEY=your-secret-key
   AI_API_KEY=your-anthropic-api-key
   ```

4. Run the application
   ```
   uvicorn backend.app.main:app --reload
   ```

### Frontend Setup
1. Install dependencies
   ```
   npm install
   ```

2. Configure environment variables in `.env` file
   ```
   REACT_APP_API_BASE_URL=http://localhost:8000
   ```

3. Start the development server
   ```
   npm start
   ```

## API Documentation

Once the backend is running, access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc