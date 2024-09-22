# Molecule Management API

## Overview

This project provides a RESTful API for managing molecules and performing substructure searches using RDKit and PostgreSQL. The application is built with FastAPI and SQLAlchemy.

## Prerequisites

Before running the application, ensure you have the following installed:

- Python 3.8 or higher
- PostgreSQL
- `psycopg2` (PostgreSQL adapter for Python)
- `fastapi`
- `sqlalchemy`
- `rdkit`

## Setup

### 1. Install PostgreSQL

Follow the [PostgreSQL installation guide](https://www.postgresql.org/download/) for your operating system.

### 2. Create a PostgreSQL Database

You need to create a PostgreSQL database for the application. You can do this using the `psql` command-line tool or a database management tool like pgAdmin.

### 3. Create a Virtual Environment and Install Dependencies

Create a virtual environment and activate it:

```bash 
python -m venv env
source env/bin/activate  # On Windows use: env\Scripts\activate
```
Install the required Python packages:
    
```bash
pip install -r requirements.txt
```

### 4. Configure the Database Connection

Ensure the DATABASE_URL in database.py points to your PostgreSQL instance:

```python
DATABASE_URL = "postgresql://postgres:password@localhost:5432/myMoleculeDB"

```

### 5. Run the Application

Run the FastAPI application:

```bash
uvicorn src.main:app --reload
```