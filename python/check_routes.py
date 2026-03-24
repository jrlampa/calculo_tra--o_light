from api.main import app
for route in app.routes:
    methods = getattr(route, 'methods', None)
    methods_str = ",".join(methods) if methods else ""
    print(f"{route.path} [{methods_str}]")
