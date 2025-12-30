# Profile Service API (CW2)

## Overview

This microservice is a RESTful API developed using **FastAPI** as part of the COMP2001 coursework.
It manages user profiles and user activity preferences and interacts with a Microsoft SQL Server
database using stored procedures.

The service is containerised using Docker and published to Docker Hub for deployment and assessment.

---

## Features

- User profile creation, retrieval, update, and deletion
- User activity preference management (add and update activities)
- External authentication using the COMP2001 authentication API
- Secure database access via stored procedures
- Fully containerised using Docker

---

## Technology Stack

- **FastAPI** (Python)
- **Microsoft SQL Server**
- **pyodbc**
- **Docker**
- **Docker Hub**
- **GitHub Classroom**

---

## Database Setup

All database objects are hosted on the allocated Microsoft SQL Server:

## Docker Deployment

The service is containerised and published to Docker Hub.

### Pull image

```bash
docker pull isatanyuin/profile-service-api:latest
```
