
from fastapi import FastAPI
from .routes import user_router, event_router
from .database import DB_URL,create_db_and_tables
import uvicorn
app = FastAPI()

#On startup event, create the database and tables if needed
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

    

app.include_router(user_router)
app.include_router(event_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)