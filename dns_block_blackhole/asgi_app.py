import importlib.resources
import jinja2
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.responses import PlainTextResponse
from starlette.requests import Request


JINJA_ENV = jinja2.Environment(enable_async=True)
GO_AWAY_TEMPLATE = JINJA_ENV.from_string(
    importlib.resources.read_text(__package__, "go_away.txt.j2")
)


async def go_away(request: Request):
    content = await GO_AWAY_TEMPLATE.render_async(request=request)
    return PlainTextResponse(status_code=599, content=content)


ROUTES: list[Route] = [
    Route("/", go_away),
    Route("/{path}", go_away),
]

MIDDLEWARE: list[Middleware] = [
    Middleware(HTTPSRedirectMiddleware),
]


def create_asgi_app(debug: bool = False):
    return Starlette(debug=debug, routes=ROUTES, middleware=MIDDLEWARE)
