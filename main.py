from fastapi import Depends, FastAPI
from auth.auth import AuthHandler
import uvicorn

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

auth_handler = AuthHandler()

@app.get('/hello', tags=['Test'])
async def check_admin(user=Depends(auth_handler.get_current_admin)):
    return user
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7000, reload=True)