# import requests

# login_data = {
#     "email": "grace@plymouth.ac.uk",
#     "password": "ISAD123!"
# }

# response = requests.post(
#     "https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users",
#     json=login_data
# )

# print(response.status_code)
# print(response.text.strip('"') )

# if response.status_code == 200:
#     print("Login successful")
# else:
#     print("Login failed")
#     print(response.text)


import requests
from requests.auth import HTTPBasicAuth

# ============================================================================
# Test Your API with Basic Authentication
# ============================================================================

API_BASE_URL = "http://localhost:8000"

# Test accounts from coursework brief
test_accounts = [
    {"email": "grace@plymouth.ac.uk", "password": "ISAD123!"},
    {"email": "tim@plymouth.ac.uk", "password": "COMP2001!"},
    {"email": "ada@plymouth.ac.uk", "password": "insecurePassword"}
]

print("=" * 70)
print("Testing API with Basic Authentication")
print("=" * 70)

# Choose account to test with
account = test_accounts[0]  # Grace Hopper
email = account["email"]
password = account["password"]

print(f"\n🔐 Using credentials: {email}")

# ============================================================================
# Test 1: Test Authentication
# ============================================================================
print("\n" + "=" * 70)
print("Test 1: Testing Authentication")
print("=" * 70)

try:
    response = requests.get(
        f"https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users",
        auth=HTTPBasicAuth(email, password),
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    # print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Authentication working!")
    else:
        print("❌ Authentication failed")
        
except Exception as e:
    print(f"❌ Error: {e}")