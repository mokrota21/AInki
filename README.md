# AInki - Spaced Repetition Learning Platform

AInki is an intelligent spaced repetition learning platform that extracts knowledge from your documents and helps you learn through scientifically-proven spaced repetition algorithms.

## Features

- **Document Processing**: Upload PDFs, text files, and other documents
- **Knowledge Extraction**: Automatically extracts definitions, theorems, lemmas, and other knowledge objects
- **Spaced Repetition**: Uses the Leitner box system for optimal learning intervals
- **Interactive Quizzes**: Review your knowledge through engaging quiz sessions
- **Real-time Notifications**: Get notified when items are ready for review

## Architecture

### Backend (FastAPI)
- **Authentication**: User registration and login
- **Document Processing**: File upload and knowledge extraction
- **Spaced Repetition Engine**: Manages review schedules using Neo4j
- **REST API**: Clean API endpoints for frontend communication

### Frontend (React + Vite)
- **Modern UI**: Beautiful, responsive interface
- **Real-time Updates**: Live notifications for pending reviews
- **Interactive Quizzes**: Engaging learning experience
- **File Upload**: Drag-and-drop document upload

### Database Layer
- **PostgreSQL**: User authentication and document storage
- **Neo4j**: Knowledge graph and spaced repetition state management

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL
- Neo4j

### Backend Setup

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Environment variables**:
   Create a `.env` file in the `backend` directory:
   ```env
   NEO4J_URI=neo4j://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   PG_DBNAME=ainki
   PG_USER=postgres
   PG_HOST=localhost
   PG_PASSWORD=your_password
   ```

3. **Run the backend**:
   ```bash
   python main.py
   ```

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Open your browser**:
   Navigate to `http://localhost:5173`

## Usage

1. **Register/Login**: Create an account or sign in
2. **Upload Documents**: Drag and drop your learning materials
3. **Review Knowledge**: Take quiz sessions when items are ready
4. **Track Progress**: Monitor your learning statistics

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

### Document Management
- `POST /api/upload` - Upload and process documents
- `GET /api/pending` - Get items ready for review

### Learning
- `POST /api/quiz/answer` - Submit quiz answers
- `GET /api/health` - Health check

## Development

### Backend Development
```bash
cd backend
python main.py
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Database Setup
1. Start PostgreSQL and create database
2. Start Neo4j and create constraints
3. Run the application to initialize schemas

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details