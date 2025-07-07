from fastapi import FastAPI
from api.route import router

def main():
    print("Hello from transcript-insight!")
    app = FastAPI()
    app.include_router(router)

if __name__ == "__main__":
    main()
