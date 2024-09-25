from typing import List, Tuple

import pytest
import pytest_asyncio
from langchain.docstore.document import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from quivr_api.models.settings import settings
from quivr_api.modules.brain.entity.brain_entity import Brain, BrainType
from quivr_api.modules.knowledge.entity.knowledge import KnowledgeDB
from quivr_api.modules.user.entity.user_identity import User
from quivr_api.modules.vector.entity.vector import Vector
from quivr_api.modules.vector.repository.vectors_repository import VectorRepository
from quivr_api.modules.vector.service.vector_service import VectorService

pg_database_base_url = "postgresql://postgres:postgres@localhost:54322/postgres"

TestData = Tuple[List[Vector], KnowledgeDB, Brain]


@pytest.fixture(scope="module")
def embedder():
    return DeterministicFakeEmbedding(size=settings.embedding_dim)


@pytest_asyncio.fixture(scope="function")
async def test_data(session: AsyncSession, embedder) -> TestData:
    user_1 = (
        await session.exec(select(User).where(User.email == "admin@quivr.app"))
    ).one()
    assert user_1.id
    vectors = embedder.embed_documents(
        [
            "vector_1",
            "vector_2",
        ]
    )

    brain_1 = Brain(
        name="test_brain",
        description="this is a test brain",
        brain_type=BrainType.integration,
    )
    knowledge_1 = KnowledgeDB(
        file_name="test_file_1",
        extension=".txt",
        status="UPLOADED",
        source="test_source",
        source_link="test_source_link",
        file_size=100,
        file_sha1="test_sha1",
        brains=[brain_1],
        user_id=user_1.id,
    )
    session.add(knowledge_1)
    await session.commit()
    await session.refresh(knowledge_1)

    assert knowledge_1.id, "Knowledge ID not generated"

    vector_1 = Vector(
        content="vector_1",
        metadata_={"chunk_size": 96},
        embedding=vectors[0],  # type: ignore
        knowledge_id=knowledge_1.id,
    )

    vector_2 = Vector(
        content="vector_2",
        metadata_={"chunk_size": 96},
        embedding=vectors[1],  # type: ignore
        knowledge_id=knowledge_1.id,
    )

    session.add(vector_1)
    session.add(vector_2)

    await session.commit()

    return ([vector_1, vector_2], knowledge_1, brain_1)


@pytest.mark.asyncio(loop_scope="session")
async def test_create_vectors_service(
    session: AsyncSession, test_data: TestData, embedder
):
    _, knowledge, _ = test_data
    assert knowledge.id
    repo = VectorRepository(session)
    service = VectorService(repo)
    service.embedder = embedder

    chunk_1 = Document(page_content="I love eating pasta with tomato sauce")
    chunk_2 = Document(page_content="I love eating pizza with extra cheese")

    # Create vectors from documents
    new_vectors_id: List[int] = await service.create_vectors(
        [chunk_1, chunk_2], knowledge.id
    )  # type: ignore

    # Verify the correct number of vectors were created
    assert len(new_vectors_id) == 2, f"Expected 2 vectors, got {len(new_vectors_id)}"

    # Verify the content of the first vector matches the corresponding document
    vector_1_content = (
        (await session.execute(select(Vector).where(Vector.id == new_vectors_id[0])))
        .scalars()
        .first()
        .content
    )
    vector_2_content = (
        (await session.execute(select(Vector).where(Vector.id == new_vectors_id[1])))
        .scalars()
        .first()
        .content
    )

    assert (
        vector_1_content == chunk_1.page_content
    ), "The content of the first vector does not match"
    assert (
        vector_2_content == chunk_2.page_content
    ), "The content of the second vector does not match"


@pytest.mark.asyncio(loop_scope="session")
async def test_get_vectors_by_knowledge_id(session: AsyncSession, test_data: TestData):
    vectors, knowledge, _ = test_data
    assert knowledge.id

    repo = VectorRepository(session)
    results = await repo.get_vectors_by_knowledge_id(knowledge.id)  # type: ignore

    assert len(results) == 2, f"Expected 2 vectors, got {len(results)}"
    assert (
        results[0].content == vectors[0].content
    ), f"Expected {vectors[0].content}, got {results[0].content}"
    assert (
        results[1].content == vectors[1].content
    ), f"Expected {vectors[1].content}, got {results[1].content}"


@pytest.mark.asyncio(loop_scope="session")
async def test_service_similarity_search(
    session: AsyncSession, test_data: TestData, embedder
):
    vectors, knowledge, brain = test_data
    assert knowledge.id
    assert brain.brain_id

    repo = VectorRepository(session)
    service = VectorService(repo, embedder=embedder)

    k = 2
    results = await service.similarity_search(vectors[0].content, brain.brain_id, k=k)  # type: ignore
    assert len(results) == k
    assert results[0].page_content == vectors[0].content

    results = await service.similarity_search(vectors[1].content, brain.brain_id, k=k)  # type: ignore

    assert results[0].page_content == vectors[1].content

    k = 1
    results = await service.similarity_search(vectors[0].content, brain.brain_id, k=k)  # type: ignore
    assert len(results) == k
    assert results[0].page_content == vectors[0].content

    results = await service.similarity_search(vectors[1].content, brain.brain_id, k=k)  # type: ignore

    assert results[0].page_content == vectors[1].content


@pytest.mark.asyncio(loop_scope="session")
async def test_similarity_search(session: AsyncSession, test_data: TestData):
    vectors, knowledge, brain = test_data
    assert knowledge.id
    assert brain.brain_id

    repo = VectorRepository(session)

    k = 2
    results = await repo.similarity_search(vectors[0].embedding, brain.brain_id, k=k)  # type: ignore
    assert len(results) == k
    assert results[0].content == vectors[0].content

    results = await repo.similarity_search(vectors[1].embedding, brain.brain_id, k=k)  # type: ignore

    assert results[0].content == vectors[1].content

    k = 1
    results = await repo.similarity_search(vectors[0].embedding, brain.brain_id, k=k)  # type: ignore
    assert len(results) == k
    assert results[0].content == vectors[0].content

    results = await repo.similarity_search(vectors[1].embedding, brain.brain_id, k=k)  # type: ignore

    assert results[0].content == vectors[1].content


@pytest.mark.asyncio(loop_scope="session")
async def test_similarity_with_oversized_chunk(
    session: AsyncSession, test_data: TestData
):
    vectors, knowledge, brain = test_data
    assert knowledge.id
    assert brain.brain_id

    repo = VectorRepository(session)

    k = 2
    results = await repo.similarity_search(
        vectors[0].embedding,  # type: ignore
        brain.brain_id,
        k=k,
        max_chunk_sum=100,
    )

    assert len(results) == 1
    assert results[0].content == vectors[0].content
