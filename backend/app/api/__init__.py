from fastapi import APIRouter
from .auth import router as auth_router
from .profiles import router as profiles_router
from .learning import router as learning_router
from .goals import router as goals_router
from .resume import router as resume_router
from .interviews import router as interviews_router
from .dsa import router as dsa_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(profiles_router, prefix="/profiles", tags=["profiles"])
router.include_router(learning_router, prefix="/learning", tags=["learning"])
router.include_router(goals_router, prefix="/goals", tags=["goals"])
router.include_router(resume_router, prefix="/resume", tags=["resume"])
router.include_router(interviews_router, prefix="/interviews", tags=["interviews"])
router.include_router(dsa_router, prefix="/dsa", tags=["dsa"])
