from app.api.routes.worksheets import router as worksheets_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.reports import router as reports_router
from app.api.routes.auth import router as auth_router
from app.api.routes.tracking import router as tracking_router
from app.api.routes.children import router as children_router

from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.parent import router as parent_router

__all__ = [
    "worksheets_router",
    "analysis_router",
    "reports_router",
    "auth_router",
    "tracking_router",
    "children_router",

    "dashboard_router",
    "parent_router",
]
