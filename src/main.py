from server.run_server import create_app

# ASGI entry point: `uvicorn main:app` (and `mytho server`) load this.
app = create_app()

if __name__ == "__main__":
    # Running this file directly doesn't start anything — use the `mytho` CLI.
    print(
        "main.py only exposes the ASGI app (`main:app`); it is not a launcher.\n"
        "Use the `mytho` command instead, e.g.:\n"
        "  mytho server     start the web UI\n"
        "  mytho build      run the full pipeline\n"
        "  mytho status     show pipeline state\n"
        "  mytho --help     list all commands"
    )
    raise SystemExit(1)
