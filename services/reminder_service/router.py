from aiogram import Router
from services.reminder_service.handlers.create_handlers import create_router
from services.reminder_service.handlers.action_handlers import action_router
from services.reminder_service.handlers.list_handlers import list_router

reminder_router = Router(name="reminder_router")

reminder_router.include_router(create_router)
reminder_router.include_router(action_router)
reminder_router.include_router(list_router)
