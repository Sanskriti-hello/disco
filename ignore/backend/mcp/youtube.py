from googleapiclient.discovery import build
import google.oauth2.credentials

# For APIs that access user data, obtain credentials via OAuth 2.0 flow
# (e.g., using google-auth-oauthlib)
# credentials = ... # (see documentation on OAuth 2.0 flows)

# For simple public data access (API key), you can use a developer key
API_KEY = ''

# Build the service object for a specific API and version (e.g., YouTube v3)
service = build('youtube', 'v3', developerKey=API_KEY)
print(dir(service))
# Example: Make a request to list video categories
request = service.videoCategories().list(part='snippet', regionCode='us')
response = request.execute()

print(response)