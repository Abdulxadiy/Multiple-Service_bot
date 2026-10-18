from aiogram import Router
from services.finance_service.handlers.menu_handlers import menu_router
from services.finance_service.handlers.transaction_handlers import transaction_router
from services.finance_service.handlers.report_handlers import report_router

finance_router = Router(name="finance_router")

finance_router.include_router(menu_router)
finance_router.include_router(transaction_router)
finance_router.include_router(report_router)
