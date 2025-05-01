__all__ = (
    "start_router",
    "roles_router",
    "animals_router",
)

from .animals import router as animals_router
from .basic import router as start_router
from .roles import router as roles_router
