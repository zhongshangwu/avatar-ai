import asyncio
from argparse import Namespace
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.responses import Response

from avatarai.utils.args_utils import FlexibleArgumentParser
from avatarai.engine.engine_args import EngineArgs
from avatarai.engine.async_avatar_engine import AsyncAvatarEngine
from avatarai.logger import init_logger


logger = init_logger("avatarai.entrypoints.serve")

TIMEOUT_KEEP_ALIVE = 5  # seconds.
app = FastAPI()
engine = None


@app.get("/health")
async def health() -> Response:
    """健康检查接口"""
    return Response(status_code=200)


def build_app(args: Namespace) -> FastAPI:
    global app

    app.root_path = args.root_path
    return app


async def init_app(args: Namespace) -> FastAPI:
    global engine

    if args.root_path:
        app.root_path = args.root_path

    engine_args = EngineArgs.from_cli_args(args)
    engine = AsyncAvatarEngine.from_engine_args(engine_args)
    await engine.serve()
    return app


async def run_server(args: Namespace, **uvicorn_kwargs: Any) -> None:
    logger.info(f"启动AvatarAI服务器，端口: {args.port}")

    app = await init_app(args)

    import uvicorn
    config = uvicorn.Config(
        app=app,
        host=args.host or "0.0.0.0",
        port=args.port,
        log_level=args.log_level,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    parser = FlexibleArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--root-path",
        type=str,
        default=None,
        help="FastAPI root_path when app is behind a path based routing proxy")
    parser.add_argument("--log-level", type=str, default="info")
    parser = EngineArgs.add_cli_args(parser)
    args = parser.parse_args()

    asyncio.run(run_server(args))
