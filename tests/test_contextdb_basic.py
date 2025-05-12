from core.context_db import ContextDB


def test_contextdb_basic():
    db = ContextDB()
    # Novel追加
    novel, created = db.get_or_create_novel(
        url="https://example.com/novel/1",
        defaults={
            "title": "テスト小説",
            "author": "テスト作者",
            "platform": "testsite",
            "tags": "test,novel",
            "synopsis": "これはテスト用の小説です。"
        }
    )
    assert novel is not None
    print(f"Novel: {novel.title}, id={novel.id}, created={created}")

    # Episode追加
    episode, created = db.get_or_create_episode(
        novel_id=novel.id,
        episode_url="https://example.com/novel/1/ep1",
        defaults={
            "episode_title": "第1話 テストエピソード",
            "episode_number": 1,
            "content_raw": "テスト本文",
            "publication_date": None
        }
    )
    assert episode is not None
    print(
        f"Episode: {episode.episode_title}, id={episode.id}, created={created}")

    # Character追加
    character, created = db.get_or_create_character(
        novel_id=novel.id,
        name="テストキャラ",
        defaults={
            "description_by_author": "主人公です。"
        }
    )
    assert character is not None
    print(f"Character: {character.name}, id={character.id}, created={created}")

    # 取得テスト
    fetched_novel = db.get_novel_by_id(novel.id)
    assert fetched_novel is not None
    print(f"Fetched Novel: {fetched_novel.title}")

    fetched_episode = db.get_episode_by_id(episode.id)
    assert fetched_episode is not None
    print(f"Fetched Episode: {fetched_episode.episode_title}")

    fetched_characters = db.get_characters_for_novel(novel.id)
    assert len(fetched_characters) > 0
    print(f"Characters for novel: {[c.name for c in fetched_characters]}")


if __name__ == "__main__":
    test_contextdb_basic()
