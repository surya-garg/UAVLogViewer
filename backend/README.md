# UAV Log Chatbot Backend

Agentic chatbot backend for analyzing MAVLink flight logs using LLM-powered analysis.

## Features

- **Agentic Behavior**: Maintains conversation state, asks clarifying questions, and proactively identifies issues
- **MAVLink Parser**: Extracts and analyzes telemetry data from .bin files
- **Anomaly Detection**: Dynamically detects flight anomalies using LLM reasoning
- **Function Calling**: Uses LLM function calling to query data precisely
- **Multi-LLM Support**: Works with OpenAI GPT-4 or Anthropic Claude

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key

### 4. Run the Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Upload Log File
```http
POST /api/upload
Content-Type: multipart/form-data

file: <.bin file>
session_id: <optional session ID>
```

### Chat
```http
POST /api/chat
Content-Type: application/json

{
  "session_id": "uuid",
  "message": "What was the maximum altitude?"
}
```

### Get Session Info
```http
GET /api/session/{session_id}
```

### Reset Conversation
```http
POST /api/session/{session_id}/reset
```

### Delete Session
```http
DELETE /api/session/{session_id}
```

## Architecture

### Components

1. **MAVLink Parser** (`mavlink_parser.py`)
   - Parses .bin files using pymavlink
   - Extracts telemetry data (GPS, battery, attitude, etc.)
   - Computes metadata and statistics
   - Detects anomalies in flight data

2. **Flight Analysis Agent** (`agent.py`)
   - Agentic chatbot with conversation state
   - Uses LLM function calling for precise data queries
   - Maintains context across conversation
   - Proactively asks clarifying questions

3. **FastAPI Server** (`main.py`)
   - RESTful API endpoints
   - Session management
   - File upload handling
   - CORS configuration

### Agentic Features

The agent uses several strategies to provide intelligent analysis:

- **Function Calling**: Queries specific data using tools like `query_flight_data`, `detect_anomalies`, `get_time_series`
- **Context Awareness**: Maintains conversation history and log context
- **Dynamic Reasoning**: Uses LLM to reason about patterns rather than hardcoded rules
- **Proactive Analysis**: Suggests related issues and follow-up questions
