# Financial Statement Parser Backend

A Python backend for parsing and analyzing financial statements using AI (OpenAI and Google Gemini).

## Features

- Extract personal information from financial statements
- Extract transaction details from financial statements
- Categorize transactions automatically
- Generate financial summaries and insights
- Support for both OpenAI and Google Gemini AI models
- REST API for integration with web applications

## Directory Structure

```
backend/
├── data/                  # Data storage directory
├── src/                   # Source code
│   ├── api/               # API endpoints
│   ├── config/            # Configuration settings
│   ├── core/              # Core business logic
│   ├── models/            # Data models
│   ├── services/          # External service integrations
│   └── utils/             # Utility functions
├── tests/                 # Test cases
├── setup.py               # Package setup script
└── README.md              # This file
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd <repository-directory>/backend
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package:
   ```
   pip install -e .
   ```

4. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ASSISTANT_ID=your_openai_assistant_id
   PERSONAL_INFO_ASSISTANT_ID=your_personal_info_assistant_id
   GOOGLE_API_KEY=your_google_api_key
   ENABLE_FILE_STORAGE=True
   ```

## Usage

### Command Line Interface

Process a PDF statement:

```
statement-parser --pdf path/to/statement.pdf --output path/to/output/dir
```

Use Google Gemini instead of OpenAI:

```
statement-parser --pdf path/to/statement.pdf --use-gemini
```

### REST API

Start the API server:

```
statement-api --host 0.0.0.0 --port 8000
```

With auto-reload for development:

```
statement-api --reload
```

### API Endpoints

- `GET /`: Root endpoint
- `GET /health`: Health check endpoint
- `POST /process`: Process a financial statement PDF

Example request to process a statement:

```
curl -X POST http://localhost:8000/process \
  -F "file=@path/to/statement.pdf" \
  -F "use_gemini=false"
```

## Development

### Running Tests

```
pytest tests/
```

### Code Style

This project follows PEP 8 style guidelines. You can check your code with:

```
flake8 src/
```

## License

[MIT License](LICENSE) 