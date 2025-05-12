import abc
from typing import Dict, List, Optional, Tuple, Any


class BaseScraper(metaclass=abc.ABCMeta):
    PLATFORM_NAME = "UnknownPlatform"

    @abc.abstractmethod
    def fetch_novel_metadata(self, novel_url: str) -> Optional[Dict[str, Any]]:
        """
        小説のトップページURLからメタデータを取得する。
        必須返り値キー: "title", "author", "novel_url", "platform"
        推奨返り値キー: "synopsis", "tags", "raw_episode_data" (List[Dict[str, Any]])
        raw_episode_data の各要素は {"url": str, "title": str, "number": int, "publication_date_str": Optional[str]} を含む辞書。
        失敗した場合は None を返す。
        """
        pass

    @abc.abstractmethod
    def fetch_episode_content(self, episode_url: str) -> Optional[str]:
        """
        各話のURLから生の本文テキストを取得する（ルビなどは除去または適切に処理）。
        話タイトルは fetch_novel_metadata で取得済みの前提とする。
        失敗した場合は None を返す。
        """
        pass
