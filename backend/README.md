# Financial Statement Parser Backend

A Python backend for parsing and analyzing financial statements and identity documents using AI (OpenAI and Google Gemini).

## Features

- Extract personal information from financial statements
- Extract transaction details from financial statements
- Categorize transactions automatically
- Generate financial summaries and insights
- Process identity documents (driving licenses and passports)
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
   GEMINI_API_KEY=your_gemini_api_key
   ENABLE_FILE_STORAGE=True
   ```

## Usage

### Financial Statement Processing

Process a PDF statement:

```
python run_parser.py --pdf path/to/statement.pdf --output path/to/output/dir
```

Use Google Gemini instead of OpenAI:

```
python run_parser.py --pdf path/to/statement.pdf --use-gemini
```

Or use the batch script:

```
run_parser.bat path/to/statement.pdf
```

### Identity Document Processing

Process a driving license:

```
python process_identity_document.py --pdf path/to/driving_license.pdf --type driving_license
```

Process a passport:

```
python process_identity_document.py --pdf path/to/passport.pdf --type passport
```

Or use the batch script:

```
run_identity_processor.bat path/to/driving_license.pdf driving_license
run_identity_processor.bat path/to/passport.pdf passport
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
- `POST /process/identity`: Process an identity document

Example request to process a statement:

```
curl -X POST http://localhost:8000/process \
  -F "file=@path/to/statement.pdf" \
  -F "use_gemini=false"
```

Example request to process an identity document:

```
curl -X POST http://localhost:8000/process/identity \
  -F "file=@path/to/driving_license.pdf" \
  -F "document_type=driving_license"
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