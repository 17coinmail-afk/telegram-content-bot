import logging
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

import_errors = []

# Test all our custom imports
modules_to_test = [
    "app.config",
    "app.bot",
    "app.database.base",
    "app.database.session",
    "app.database.models",
    "app.handlers.start",
    "app.handlers.topics",
    "app.handlers.content",
    "app.handlers.subscription",
    "app.handlers.channels",
    "app.handlers.admin",
    "app.services.image_overlay",
    "app.services.ai.groq",
    "app.services.ai.images",
    "app.services.telegram",
    "app.keyboards.inline",
]

for module_name in modules_to_test:
    try:
        __import__(module_name)
        import_errors.append(f"OK {module_name}")
    except Exception as e:
        import_errors.append(f"FAIL {module_name}: {str(e)[:200]}")
        logger.error(f"Import failed {module_name}: {e}")

@app.get("/health")
async def health_check():
    failed = [e for e in import_errors if e.startswith("FAIL")]
    return {
        "status": "ok" if not failed else "import_errors",
        "failed_count": len(failed),
        "failed": failed,
    }

@app.get("/")
async def root():
    return {"message": "Bot diagnostic mode"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
