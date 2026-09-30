from aiogram import Router
from services.password_manager.handlers.categories_handlers import categories_router
from services.password_manager.handlers.accounts_handlers import accounts_router
from services.password_manager.handlers.pin_handlers import pin_router

password_manager_router = Router(name="password_manager_router")

# Sub-routerlarni ulash
password_manager_router.include_router(categories_router)
password_manager_router.include_router(accounts_router)
password_manager_router.include_router(pin_router)
