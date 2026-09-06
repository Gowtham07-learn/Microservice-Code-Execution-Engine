from fastapi import APIRouter, Request

from app.api.schemas import LanguageOut, LanguagesResponseOut

router = APIRouter()


@router.get("/api/v1/languages", response_model=LanguagesResponseOut)
async def list_languages(request: Request) -> LanguagesResponseOut:
    registry = request.app.state.plugin_registry
    languages = [
        LanguageOut(name=plugin.language(), version=plugin.version())
        for plugin in registry.list_plugins()
    ]
    languages.sort(key=lambda item: item.name)
    return LanguagesResponseOut(languages=languages)
