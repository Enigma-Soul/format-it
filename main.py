import argparse

import uvicorn


def main():
    parser = argparse.ArgumentParser(
        prog="format-it",
        description="格式化公文工具 — Web UI",
    )
    parser.add_argument("--host", default="127.0.0.1", help="监听地址 (默认: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="监听端口 (默认: 8000)")
    parser.add_argument("--public", action="store_true", help="监听所有接口 (等同 --host 0.0.0.0)")
    args = parser.parse_args()

    host = "0.0.0.0" if args.public else args.host
    uvicorn.run("web.app:create_app", host=host, port=args.port, factory=True)


if __name__ == "__main__":
    main()
