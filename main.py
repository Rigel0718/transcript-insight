from fastapi import FastAPI
from api.route import router, CLIENT_DATA_DIR
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles

load_dotenv()

app = FastAPI()
app.include_router(router)
app.mount(
    "/artifacts",
    StaticFiles(directory=str(CLIENT_DATA_DIR / "users")),
    name="artifacts"
)
