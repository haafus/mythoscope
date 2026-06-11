from importlib import import_module as _imp

_run_server = _imp("06_web.run_server")
create_app = _run_server.create_app
run_server = _run_server.run_server

app = create_app()

if __name__ == "__main__":
    run_server()
