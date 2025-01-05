from app import app
import asyncio
import hypercorn.asyncio

async def main():
    config = hypercorn.Config()
    config.bind = ["localhost:5000"]
    await hypercorn.asyncio.serve(app, config)

if __name__ == "__main__":
    asyncio.run(main()) 