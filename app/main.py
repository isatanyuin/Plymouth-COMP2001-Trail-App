
import logging
import os
from typing import Optional
from dotenv import load_dotenv
from fastapi.security import  HTTPBasic, HTTPBasicCredentials
import pyodbc
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from fastapi.openapi.docs import get_swagger_ui_html
import requests

# load env variable
load_dotenv()

# get server and database from env
server = os.getenv("DB_SERVER")
database = os.getenv("DB_NAME")
AUTH_API_URL = os.getenv("AUTH_API_URL")

# connect to database
def get_db_connection():
    try:
        conn = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={server};"
            f"DATABASE={database};"
            "Trusted_Connection=yes;"
            "MARS_Connection=yes;",
              autocommit=True  # for store procedure execution
        )
        return conn
    except pyodbc.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database connection failed")


# Create FastAPI app with metadata
app = FastAPI(
    title="Trail App - ProfileService API",
    description="""
    ## ProfileService Microservice for Trail Application
    
    This microservice manages user profiles, authentication, and activity preferences 
    for the Trail App platform.
    
    ### Authentication
    This API uses **HTTP Basic Authentication**. You need to provide your email 
    and password credentials which will be verified against the external 
    authenticator service.
    
    **Test Accounts:**
    - Username: `grace@plymouth.ac.uk` | Password: `ISAD123!`
    - Username: `tim@plymouth.ac.uk` | Password: `COMP2001!`
    - Username: `ada@plymouth.ac.uk` | Password: `insecurePassword`

    """,
    version="1.0.0",
    openapi_extra={
        "components": {
            "schemas": {
                "HTTPValidationError": {"type": "object"},
                "ValidationError": {"type": "object"}
            }
        }
    },
    docs_url=None,
    redoc_url=None,
    contact={
        "name": "API Support",
        "email": "your.email@plymouth.ac.uk",
    },
    license_info={
        "name": "Academic Use Only",
    }
)

@app.get("/docs", include_in_schema=False)
def custom_docs():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="CW2 API Docs"
    )

# =============================================================
# AUTHENTICATION
# =============================================================

# Configure logging for debugging and monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> dict:
    """
    Verifies username/password with external authenticator API.
    The API returns ["Verified","True"] on success.
    """
    email = credentials.username  # Use email as username
    password = credentials.password
    
    try:
        # Verify credentials with external API
        response = requests.post(
            AUTH_API_URL,
            json={"email": email, "password": password},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if verification successful
            # API returns ["Verified","True"] on success
            if isinstance(result, list) and len(result) >= 2:
                if result[0] == "Verified" and result[1] == "True":
                    logger.info(f"User authenticated: {email}")
                    return {
                        "email": email,
                        "authenticated": True
                    }
            
            # If we reach here, verification failed
            logger.warning(f"Authentication failed for: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
        else:
            logger.warning(f"Authentication API error: {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Basic"},
            )
            
    except requests.RequestException as e:
        logger.error(f"Authentication service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )


# define request body
class UserCreate(BaseModel):
    """Schema for creating a new user with validation"""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: Optional[EmailStr] = Field(None, description="User email address")
    phone_number: Optional[str] = Field(None, max_length=20, description="Contact number")
    location: Optional[str] = Field(None, max_length=100, description="User location")
    date_of_birth: Optional[date] = Field(None, description="Date of birth (YYYY-MM-DD)")



class UpdateUser(BaseModel):
    """Schema for updating user information (all fields optional)"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None

class Activity_Request(BaseModel):
    """Schema for creating user activity preferences"""
    activity_ID: int

class UpdateUserPreferences(BaseModel):
    """Schema for updating user activity preferences"""
    new_activity_ID: int | None = None
    old_activity_ID: int | None = None

class SuccessResponse(BaseModel):
    """Standard success response"""
    message: str

class Config:
    schema_extra = {
        "example": {
            "message": "Operation completed successfully"
        }
    }


def validation_checking(msg):
    if "user not found" in msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    elif "new activity not found" in msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New Activity not found")
    elif "old activity not found" in msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Old Activity not found for this user")
    elif "activity not found" in msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    elif "activity already exists for this user" in msg:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,  # Conflict
            detail="Activity already exists for this user."
        )
    elif "old activity not found for this user" in msg:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,  # Conflict
            detail="Old activity not found for this user."
        )
    elif "email already exists" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,  # Conflict
                detail="Email already exists."
            )
    elif "username already exists" in msg:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    elif "date_of_birth" in msg:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,  # Bad Request
            detail="Invalid date of birth, must be at least 13 years old."
        )
    elif "phone_number" in msg:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,  # Bad Request
            detail="Invalid phone number format, the number must start with +."
        )
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# API Endpoints

# create new user
@app.post(
    "/api/profiles")
def create_user(user:UserCreate, current_user: dict = Depends(verify_credentials)):
    """
    Create a new user profile in the system.
    
    Requires authentication via HTTP Basic Auth (email/password).
    """
    conn = get_db_connection() # avoid db access timeout
    cursor = conn.cursor()
    try:
        cursor.execute("""
                        EXEC CW2.Create_User
                        @Username = ?,
                        @Email = ?,
                        @Phone_Number = ?,
                        @Location = ?,
                        @Date_Of_Birth = ?

                    """,
                        user.username,
                        user.email,
                        user.phone_number,
                        user.location,
                        user.date_of_birth
        )
        logger.info(f"User created: {user.username} by {current_user.get('email')}")
        return {"message": "User created successfully"}
    except pyodbc.Error as e:
        conn.rollback()
        logger.error(f"Create user failed: {e}")
        msg = str(e).lower()
        validation_checking(msg)
    finally:
        cursor.close()
        conn.close()



# read user using user id
@app.get("/api/profiles/{user_id}")
# def read_user(user_id: int):
def read_user(user_id: int, current_user: dict = Depends(verify_credentials)):
    """
    Get user profile by ID.
    
    Requires authentication. Returns full profile information.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
                EXEC CW2.Read_User
                @User_ID = ?
            """
            , user_id
        )

        # get first user data based on user id
        row = cursor.fetchone()

        # get column names
        columns = [column[0] for column in cursor.description]

        # map column names to user data
        user_data = dict(zip(columns, row))
        return user_data
    
    except pyodbc.Error as e:
        logger.error(f"Read user failed:{e}")
        msg = str(e).lower()

        if "user not found" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve user profile")
    finally:
        cursor.close()
        conn.close()

# update user data based on user id
@app.put("/api/profiles/{user_id}")
def update_user(user_id: int, user:UpdateUser, current_user: dict = Depends(verify_credentials)):
    """
    Update user profile information.
    
    Only provide the fields you want to update. All fields are optional.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
                EXEC CW2.Update_User
                @User_ID = ?,
                @Username = ?,
                @Email = ?,
                @Phone_Number = ?,
                @Location = ?,
                @Date_Of_Birth = ?
            """
            , 
            user_id,
            user.username,
            user.email,
            user.phone_number,
            user.location,
            user.date_of_birth
        )
        return {"message": "User updated successfully"}
    except pyodbc.Error as e:
        msg = str(e).lower()
        print(msg)
        validation_checking(msg)
    finally:
        cursor.close()
        conn.close()

# Create user preferences
@app.post(
    "/api/profiles/{user_id}/activity",
    description="""
    Add a new favourite activity to user's preferences.
    
    **Authentication Required**: Yes
    
    **Available Activities:**
    - 1: Running
    - 2: Cycling
    - 3: Hiking
    
    Users can have multiple favourite activities.
    """)
def create_user_preferences(user_id: int, body:Activity_Request, current_user: dict = Depends(verify_credentials)):
    """
    Add a new favourite activity to user's profile.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
                EXEC CW2.Add_User_Activity
                @User_ID = ?,
                @Activity_ID = ?
            """
            , 
            user_id,
            body.activity_ID
        )

        return {"message": "User Preferences created successfully"}
    except pyodbc.Error as e:
        msg = str(e).lower()
        print(msg)
        validation_checking(msg)
    finally:
        cursor.close()
        conn.close()   



# update preferences
@app.post("/api/profiles/{user_id}")
def update_user_preferences(user_id: int, user:UpdateUserPreferences, current_user: dict = Depends(verify_credentials)):
    """
    Update user's activity preferences.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
                EXEC CW2.Update_User_Activity
                @User_ID = ?,
                @New_Activity_ID = ?,
                @Old_Activity_ID = ?
            """
            , 
            user_id,
            user.new_activity_ID,
            user.old_activity_ID
        )

        return {"message": "User Preferences updated successfully"}
    except pyodbc.Error as e:
        msg = str(e).lower()
        print(msg)
        validation_checking(msg)
    finally:
        cursor.close()
        conn.close()

# delete user based on user id
@app.delete("/api/profiles/{user_id}")
def delete_user(user_id: int, current_user: dict = Depends(verify_credentials)):
    """
    Delete user profile (hard delete).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
                EXEC CW2.Delete_User
                @User_ID = ?
            """
            ,
            user_id
        )
        return {"message": "User deleted successfully"}
    except pyodbc.Error as e:
        msg = str(e).lower()
        if "user not found" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete user profile")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


