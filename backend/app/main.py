from fastapi import FastAPI
from app.api import ml_router, model_router
from dotenv import load_dotenv

load_dotenv() 

app = FastAPI(title="Sales Forecast Enterprise System")

app.include_router(ml_router, prefix="/api/v1/forecast", tags=["Forecast"])
app.include_router(model_router, prefix="/api/v1/model", tags=["Model Management"])

@app.get("/")
async def root():
    return {"message": "Welcome to Sale Forecast API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)