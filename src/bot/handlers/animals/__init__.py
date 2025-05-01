__all__ = ("router",)

from aiogram import Router

from .add_animal import router as add_router

router = Router(name=__name__)
router.include_router(add_router)
