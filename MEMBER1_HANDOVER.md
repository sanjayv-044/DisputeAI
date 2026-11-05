# DisputeAI – Member 1 Technical Handover

## 1. Project Overview

DisputeAI is an AI-assisted banking dispute management system designed to help manage customer transaction disputes.

The current implementation provides:
- Customer dispute submission.
- Persistent dispute storage.
- Dispute retrieval and history.
- Rule-based fraud risk analysis.
- Risk scoring and prioritisation.
- Escalation recommendations.
- Backend validation, error handling and logging.
- Docker-based deployment.

## 2. Technology Stack

### Frontend
- React.js
- Vite
- JavaScript
- Axios
- CSS

### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite

### Deployment
- Docker
- Docker Compose

## 3. Member 1 Responsibilities Completed

### A. Frontend Development
- Created the main dashboard.
- Implemented dispute submission interface.
- Implemented dispute history.
- Added AI recommendations page.
- Integrated frontend with backend APIs.
- Displayed dispute information retrieved from the database.

### B. Backend Development
- Created FastAPI application.
- Configured SQLite database connection.
- Implemented SQLAlchemy database models.
- Created Pydantic request validation schemas.
- Implemented dispute creation and retrieval APIs.

### C. Rule-Based AI Risk Analysis

Implemented a baseline rule-based analysis engine in `backend/ai_engine.py`.

The engine evaluates:
- Fraud description keywords.
- Whether OTP was shared.
- Transaction amount.
- Transaction type.
- Delay between transaction and reporting.

It generates:
- Fraud type.
- Risk score.
- Priority level.
- Escalation recommendation.
- Suggested action.

**Important:** This is a rule-based baseline, not a trained machine-learning model.

### D. Validation and Error Handling
- Validates customer information.
- Validates transaction ID format.
- Checks transaction amount.
- Validates transaction type.
- Checks transaction and reporting dates.
- Handles invalid API requests.
- Provides readable frontend error messages.
- Includes backend request and error logging.

### E. Database
- Implemented SQLite persistence.
- Added AI analysis fields to the dispute model.
- Tested dispute creation and retrieval.
- Configured Docker database persistence using `backend/data`.

### F. Docker Deployment
Created:
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `docker-compose.yml`

Verified that both frontend and backend containers start successfully.

## 4. Backend API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Backend welcome response |
| GET | `/health` | Health check |
| POST | `/api/disputes` | Submit a new dispute |
| GET | `/api/disputes` | Retrieve all disputes |
| GET | `/api/disputes/{dispute_id}` | Retrieve an individual dispute |

Swagger documentation is available at:

`http://localhost:8000/docs`

## 5. Project Structure

```text
card-dispute-triage/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── ai_engine.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── disputes.db
│   └── data/
│       └── disputes.db
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── services/
│   │       └── api.js
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml
└── MEMBER1_HANDOVER.md
```

## 6. Running the Application

Open a terminal in the project root.

Start the application:

```bash
docker compose up -d
```

Check container status:

```bash
docker compose ps
```

Stop the application:

```bash
docker compose down
```

Application addresses:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## 7. Testing Completed

The following tests were performed:

- Successful dispute submission.
- Successful dispute retrieval.
- Database persistence after Docker restart.
- AI risk score generation.
- Priority classification.
- Escalation recommendation generation.
- Invalid transaction ID validation.
- Invalid transaction type validation.
- Negative amount validation.
- Future transaction date validation.
- Invalid reporting date validation.
- Invalid customer name validation.
- Empty or whitespace-only description validation.
- Docker frontend and backend startup.

## 8. Member 2 Handover

The existing frontend, backend, database and rule-based analysis baseline should be preserved.

Member 2 can continue with the next intelligence layer, subject to the agreed project division.

Suggested responsibilities:

1. Develop a machine-learning-based fraud or dispute classification model.
2. Research and prepare suitable datasets.
3. Perform data preprocessing and feature engineering.
4. Train and evaluate candidate models.
5. Compare model performance using appropriate metrics.
6. Integrate the trained model with the existing backend.
7. Compare ML predictions with the current rule-based baseline.
8. Document model limitations and evaluation results.

Before changing the backend, coordinate changes to `ai_engine.py`, `models.py`, `schemas.py` and `main.py`.

## 9. Important Notes

- Do not delete the existing SQLite database.
- Preserve the Docker database volume mapping.
- Do not replace the existing API response structure without coordinating with the frontend.
- Keep the current rule-based analysis available as a baseline.
- Test all changes before merging them into the main project.
- Do not claim that the current rule-based engine is a trained AI/ML model.

## 10. Current Status

Member 1's baseline implementation is deployed and has passed the listed functional checks.

Further project development, including advanced ML capabilities and additional intelligent agents, remains part of the subsequent project work.