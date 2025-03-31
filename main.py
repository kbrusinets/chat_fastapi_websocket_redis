import asyncio

import uvicorn

from services.app.main import app


async def run():
    uvicorn_config = uvicorn.Config(app=app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config=uvicorn_config)
    await server.serve()


asyncio.run(run())
