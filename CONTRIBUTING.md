# Contributing to Excel Auto-Analyst

First off, thank you for considering contributing to Excel Auto-Analyst! It's people like you that make Excel Auto-Analyst such a great tool. 

## 🛠️ Environment Setup

To set up your local development environment, follow these steps:

### 1. Fork and Clone
Fork the repository to your own GitHub account and clone it to your local machine:
```bash
git clone https://github.com/YOUR_USERNAME/excel-auto-analyst.git
cd excel-auto-analyst
```

### 2. Create a Virtual Environment
It is highly recommended to use a virtual environment to manage dependencies:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
Install both the application dependencies and development dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Setup API Keys
Copy the example secrets file and add your free Groq API key:
```bash
# Windows
copy .streamlit\secrets.toml.example .streamlit\secrets.toml

# macOS/Linux
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```
Edit `.streamlit/secrets.toml` and replace the placeholder with your actual key.

## 🚀 Development Workflow

1. **Branching**: Always create a new branch for your feature or bugfix.
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Making Changes**: Write your code, ensuring it is clean and well-documented.
3. **Linting and Formatting**: We use `ruff` to maintain code quality.
   ```bash
   ruff format .
   ruff check . --fix
   ```
4. **Testing**: Run the test suite using `pytest` to ensure your changes do not break existing functionality.
   ```bash
   pytest tests/ -v
   ```
   *Note: Ensure test coverage remains high when adding new features.*

## 📩 Pull Request Guidelines

When you are ready to submit your changes, please follow these guidelines:

1. **Descriptive Title**: Use a clear and descriptive title for your PR (e.g., `feat: add custom box plots` or `fix: handle memory error on large files`).
2. **Detailed Description**: Explain *what* you changed and *why*. Include any relevant issue numbers (e.g., `Fixes #12`).
3. **Pass Checks**: Ensure all CI/CD checks (linting, tests) pass on your PR.
4. **Professional Comments**: Keep code comments professional and focused on the *why* rather than the *what*. 

Thank you for your contributions!
