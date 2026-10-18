from aiogram import Router
from services.currency_service.handlers.currency_handlers import currency_router

currency_service_router = Router(name="currency_service_router")
currency_service_router.include_router(currency_router)
