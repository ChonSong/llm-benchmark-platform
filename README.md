# LLM Benchmark Platform

A web-based, Dockerized platform for benchmarking LLM coding capabilities across three evaluation dimensions: Prompt Adherence, Refactoring, and System Extension.

## Features

- **Three Evaluation Tasks:**
  - **Task A: Strict Adherence** - Python Rate Limiter with 10 rigid rules
  - **Task B: Legacy Refactoring** - TypeScript API Handler with security issues
  - **Task C: System Extension** - Notification System with pattern recognition

- **Comprehensive Metrics:**
  - Cost analysis per run
  - Speed/latency measurement
  - Verbosity (Lines of Code) comparison
  - Qualitative radar chart (Completeness, Defensiveness, Precision)

- **Interactive Dashboard:**
  - Results comparison with charts
  - Code diff viewer
  - Model configuration management
  - Custom test case creation

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository and navigate to the project directory

2. Copy the environment file and add your API keys:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. Start the application:
   ```bash
   docker-compose up --build
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Manual Setup

#### Backend

```bash
cd backend
pip install poetry
poetry install
poetry run uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Configuration

### API Keys

Configure your LLM provider API keys in the `.env` file:

```
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
```

### Model Configuration

Models can be configured through the UI or by calling the API:

- **GPT-4o** (OpenAI)
- **Claude Sonnet 4** (Anthropic)
- **Gemini 2.0 Flash** (Google)

## Usage

1. **Seed Default Data**: Click "Seed Defaults" on the Models and Test Cases pages to populate with pre-configured options.

2. **Create a Benchmark**: Go to Benchmarks page, click "New Benchmark", select models and test cases.

3. **View Results**: After completion, view detailed scores, charts, and generated code.

4. **Mock Mode**: Enable "Use mock data" when creating benchmarks to test the UI without making API calls.

## API Endpoints

- `GET /api/models/` - List all models
- `POST /api/models/seed-defaults` - Seed default models
- `GET /api/test-cases/` - List all test cases
- `POST /api/test-cases/seed-defaults` - Seed default test cases
- `POST /api/benchmarks/` - Create and run a benchmark
- `GET /api/results/benchmark/{id}/comparison` - Get comparison data

## Architecture

```
llm-benchmark-platform/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Config and database
│   │   ├── models/       # SQLAlchemy models
│   │   └── services/     # Business logic
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API client
│   │   └── types/        # TypeScript types
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

## Scoring Logic

### Task A: Strict Adherence
- Rewards literal interpretation of specifications
- Penalizes defensive coding (unrequested validations)
- Checks for exact class/method names

### Task B: Legacy Refactoring
- Security: SQL injection fixes, environment variables
- Architecture: Service/Controller/Repository separation
- Completeness: Rate limiting, transactions, error handling

### Task C: System Extension
- Architecture: Following existing patterns
- Completeness: Template management, multiple recipients, attachments
- Code quality: Type annotations, async handling

## License

MIT
