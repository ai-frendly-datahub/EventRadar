from __future__ import annotations

import asyncio

from eventradar.mcp_server.server import create_app, main

__all__ = ["create_app", "main"]


if __name__ == "__main__":
    asyncio.run(main())
