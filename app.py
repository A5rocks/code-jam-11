import asyncio
import contextlib

from app import main

if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main.main())
