# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## How to Run the Application

This project consists of a React frontend and a FastAPI Python backend. To run the application locally, you need to start both servers.

### 1. Start the Backend

Open a terminal and navigate to the `backend` directory:
```bash
cd ../backend
```

Install the Python dependencies:
```bash
pip install -r ../requirements.txt
```

Set up your environment variables by creating a `.env` file in the `backend` directory and adding your Groq API key:
```env
GROQ_API_KEY=your_api_key_here
```

Start the FastAPI backend server:
```bash
python -m uvicorn main:app --reload
```
The backend will run at `http://localhost:8000`.

### 2. Start the Frontend

Open a separate terminal and navigate to the `frontend` directory:
```bash
cd frontend
```

Install the required Node.js dependencies:
```bash
npm install
```

Start the Vite development server:
```bash
npm run dev
```
The frontend will run at `http://localhost:5173`. Open this URL in your browser to interact with the application.
