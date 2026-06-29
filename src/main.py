from server.run_server import create_app

# ASGI entry point: `uvicorn main:app` (and `mytho server`) load this.
app = create_app()

if __name__ == "__main__":
    # Running this file directly doesn't start anything — use the `mytho` CLI.
    print(
        "main.py only exposes the ASGI app (`main:app`); it is not a launcher.\n"
        "Use the `mytho` command instead — run `mytho --help` to list commands."
    )
    raise SystemExit(1)
