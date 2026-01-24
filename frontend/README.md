# LearnFlow Frontend

A modern learning progress tracker dashboard.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:5174`

## Features

- **Your Library**: View all your books with reading progress and mastery levels
- **Add Book**: Upload PDF files to your library
- **Book Viewer**: Click on any book to view it in a modal
- **Today's Goals**: Track daily reading goals (WIP)
- **Concept Map**: Visualize concept relationships (Coming soon)

## API Endpoints

The frontend connects to the backend at `http://localhost:8000` by default. You can change this by setting the `VITE_API_BASE_URL` environment variable.

### Endpoints Used:
- `GET /fetch-user-books` - Fetch all books for the user
- `POST /add-book` - Upload a new book
- `GET /get-book?filename=<filename>` - Get book file for viewing
