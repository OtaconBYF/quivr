from datetime import datetime

import httpx
import pytest
from notion_client.client import Client
from sqlmodel.ext.asyncio.session import AsyncSession

from quivr_api.modules.brain.integrations.Notion.Notion_connector import NotionPage
from quivr_api.modules.sync.entity.notion_page import NotionSearchResult
from quivr_api.modules.sync.repository.notion_repository import NotionRepository
from quivr_api.modules.sync.service.sync_notion import (
    SyncNotionService,
    fetch_limit_notion_pages,
    fetch_notion_pages,
    store_notion_pages,
)
from quivr_api.modules.user.entity.user_identity import User


def test_deserialize_notion_page(fetch_response):
    page = NotionPage.model_validate(fetch_response[0])  # type: ignore
    assert page


def test_fetch_notion_pages(fetch_response):
    def handler(request):
        return httpx.Response(
            200,
            json={"results": fetch_response, "has_more": False, "next_cursor": None},
        )

    _client = httpx.Client(transport=httpx.MockTransport(handler))
    notion_client = Client(client=_client)

    result = fetch_notion_pages(notion_client)
    assert len(result.results) == 2
    assert not result.has_more
    assert result.next_cursor is None


# TODO(@aminediro): test more cases: noresponse, error, no  has_more ..
def test_fetch_limit_notion_pages(fetch_response):
    def handler(request):
        return httpx.Response(
            200,
            json={"results": fetch_response, "has_more": False, "next_cursor": None},
        )

    _client = httpx.Client(transport=httpx.MockTransport(handler))
    notion_client = Client(client=_client)

    result = fetch_limit_notion_pages(
        notion_client=notion_client,
        last_sync_time=datetime(1970, 1, 1, 0, 0, 0),  # UNIX EPOCH
    )

    assert len(result) == len(fetch_response)


def test_fetch_limit_notion_pages_now(fetch_response):
    def handler(request):
        return httpx.Response(
            200,
            json={"results": fetch_response, "has_more": False, "next_cursor": None},
        )

    _client = httpx.Client(transport=httpx.MockTransport(handler))
    notion_client = Client(client=_client)

    result = fetch_limit_notion_pages(notion_client, datetime.now())

    assert len(result) == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_store_notion_pages_success(
    session: AsyncSession, notion_search_result: NotionSearchResult, user_1: User
):
    assert user_1.id
    notion_repository = NotionRepository(session)
    notion_service = SyncNotionService(notion_repository)
    sync_files = await store_notion_pages(
        notion_search_result.results, notion_service, user_1.id
    )
    assert sync_files
    assert len(sync_files) == 1
    assert sync_files[0].notion_id == notion_search_result.results[0].id
    assert sync_files[0].mime_type == "md"
    assert sync_files[0].notion_id == notion_search_result.results[0].id


@pytest.mark.asyncio(loop_scope="session")
async def test_store_notion_pages_fail(
    session: AsyncSession,
    notion_search_result_bad_parent: NotionSearchResult,
    user_1: User,
):
    assert user_1.id
    notion_repository = NotionRepository(session)
    notion_service = SyncNotionService(notion_repository)
    sync_files = await store_notion_pages(
        notion_search_result_bad_parent.results, notion_service, user_1.id
    )
    assert len(sync_files) == 0
