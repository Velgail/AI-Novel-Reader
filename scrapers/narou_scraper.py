from core.logger_setup import setup_logger
from base_scraper import BaseScraper
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
import time
from typing import Dict, List, Optional, Any, Tuple
import re
from urllib.parse import urljoin
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


logger = setup_logger()


class NarouScraper(BaseScraper):
    PLATFORM_NAME = "narou"

    def __init__(self, request_delay_sec: float = 1.0):
        self.request_delay_sec = request_delay_sec
        logger.info(
            f"NarouScraper initialized with delay: {self.request_delay_sec} sec")

    def _make_request(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[BeautifulSoup]:
        try:
            time.sleep(self.request_delay_sec)
            default_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            if headers:
                default_headers.update(headers)
            logger.debug(f"Requesting URL: {url}")
            response = requests.get(url, timeout=20, headers=default_headers)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, "html.parser")
            logger.debug(f"Successfully fetched content from {url}")
            return soup
        except requests.exceptions.Timeout:
            logger.error(f"Request timed out for {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}", exc_info=False)
            return None
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during request to {url}: {e}", exc_info=True)
            return None

    def fetch_novel_metadata(self, novel_url: str) -> Optional[Dict[str, Any]]:
        # infotopページ対応
        is_infotop = False
        if "/novelview/infotop/" in novel_url:
            is_infotop = True
        # ncodeページ or infotopページどちらも許可
        if not (re.match(r"https?://ncode\.syosetu\.com/(n\d+[a-z]{2,3}/)?", novel_url) or "/novelview/infotop/" in novel_url):
            logger.error(f"Invalid URL format for NarouScraper: {novel_url}")
            return None
        soup = self._make_request(novel_url)
        if not soup:
            logger.error(
                f"Failed to fetch HTML content for metadata: {novel_url}")
            return None
        metadata: Dict[str, Any] = {
            "novel_url": novel_url, "platform": self.PLATFORM_NAME}
        logger.info(f"Start fetching metadata for: {novel_url}")
        try:
            if is_infotop:
                # infotopページ用のパース
                title_tag = soup.find("h1", class_="p-infotop-title")
                metadata["title"] = title_tag.get_text(
                    strip=True) if title_tag else "N/A"
                # 作者
                author = "N/A"
                for dt in soup.find_all("dt", class_="p-infotop-data__title"):
                    if dt.get_text(strip=True) == "作者名":
                        dd = dt.find_next_sibling(
                            "dd", class_="p-infotop-data__value")
                        if dd:
                            a = dd.find("a")
                            author = a.get_text(
                                strip=True) if a else dd.get_text(strip=True)
                        break
                metadata["author"] = author
                # あらすじ
                synopsis = "N/A"
                for dt in soup.find_all("dt", class_="p-infotop-data__title"):
                    if dt.get_text(strip=True) == "あらすじ":
                        dd = dt.find_next_sibling(
                            "dd", class_="p-infotop-data__value")
                        if dd:
                            synopsis = dd.get_text("\n", strip=True)
                        break
                metadata["synopsis"] = synopsis
                # キーワード
                tags = ""
                for dt in soup.find_all("dt", class_="p-infotop-data__title"):
                    if dt.get_text(strip=True) == "キーワード":
                        dd = dt.find_next_sibling(
                            "dd", class_="p-infotop-data__value")
                        if dd:
                            tags = dd.get_text(" ", strip=True)
                        break
                metadata["tags"] = tags
                # infotopページではエピソードリストは取得不可
                metadata["raw_episode_data"] = []
                logger.info(
                    f"Fetched infotop metadata for {novel_url}: Title='{metadata['title']}'")
                return metadata
            # ncodeメインページ用のパース（現行HTML構造対応）
            title_tag = soup.find("h1", class_="p-novel__title")
            metadata["title"] = title_tag.get_text(
                strip=True) if title_tag else "N/A"
            author_tag = soup.find("div", class_="p-novel__author")
            if author_tag:
                author_link = author_tag.find("a")
                metadata["author"] = author_link.get_text(
                    strip=True) if author_link else author_tag.get_text(strip=True).replace("作者：", "").strip()
            else:
                metadata["author"] = "N/A"
            synopsis_tag = soup.find("div", id="novel_ex")
            metadata["synopsis"] = synopsis_tag.get_text(
                "\n", strip=True) if synopsis_tag else "N/A"
            # タグはog:descriptionやmeta[name=description]からも取得可能
            tags = []
            og_desc = soup.find("meta", attrs={"property": "og:description"})
            if og_desc and og_desc.get("content"):
                tags = [t.strip()
                        for t in og_desc["content"].split() if t.strip()]
            metadata["tags"] = ", ".join(tags) if tags else ""

            # エピソードリスト抽出
            raw_episode_data: List[Dict[str, Any]] = []
            eplist = soup.find("div", class_="p-eplist")
            if eplist:
                episode_number_counter = 1
                current_chapter = ""
                for elem in eplist.children:
                    if not isinstance(elem, Tag):
                        continue
                    if "p-eplist__chapter-title" in elem.get("class", []):
                        current_chapter = elem.get_text(strip=True)
                    elif "p-eplist__sublist" in elem.get("class", []):
                        a_tag = elem.find("a", class_="p-eplist__subtitle")
                        if not a_tag or not a_tag.get("href"):
                            continue
                        episode_relative_url = a_tag.get("href")
                        episode_full_url = urljoin(
                            novel_url, episode_relative_url.strip())
                        episode_title_text = a_tag.get_text(strip=True)
                        # 章タイトルをタイトルに付与（必要なら）
                        full_title = f"{current_chapter} {episode_title_text}" if current_chapter else episode_title_text
                        update_div = elem.find(
                            "div", class_="p-eplist__update")
                        publication_date_str = None
                        update_time_str = None
                        if update_div:
                            # 例: 2013/02/20 00:36\n<span title="2013/03/30 23:52 改稿">（<u>改</u>）</span>
                            date_text = update_div.get_text(" ", strip=True)
                            # 最初の日時を抽出
                            m = re.search(
                                r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2})", date_text)
                            if m:
                                publication_date_str = m.group(1)
                        raw_episode_data.append({
                            "url": episode_full_url,
                            "title": full_title,
                            "number": episode_number_counter,
                            "publication_date_str": publication_date_str,
                        })
                        episode_number_counter += 1
            else:
                logger.warning(
                    f"Episode list ('div.p-eplist') not found for {novel_url}. Cannot fetch episode list.")
            metadata["raw_episode_data"] = raw_episode_data
            logger.info(
                f"Fetched metadata for {novel_url}: Title='{metadata['title']}', Episodes found: {len(raw_episode_data)}")
            return metadata
        except Exception as e:
            logger.error(
                f"Error parsing metadata for {novel_url}: {e}", exc_info=True)
            return None

    def _extract_text_with_ruby_as_plain(self, soup_element: Tag) -> str:
        if not soup_element:
            return ""
        paragraphs = []
        for p_tag in soup_element.find_all("p", id=re.compile(r"^L\d+$")):
            paragraph_parts = []
            for element in p_tag.contents:
                if isinstance(element, NavigableString):
                    paragraph_parts.append(str(element))
                elif isinstance(element, Tag):
                    if element.name == 'br':
                        if paragraph_parts and not paragraph_parts[-1].endswith('\n'):
                            paragraph_parts.append('\n')
                    elif element.name == 'ruby':
                        rb_text = ""
                        for sub_element in element.children:
                            if getattr(sub_element, 'name', None) == 'rb':
                                rb_text += sub_element.get_text("",
                                                                strip=False)
                            elif isinstance(sub_element, NavigableString) and sub_element.parent.name == 'ruby':
                                rb_text += str(sub_element)
                        if not rb_text:
                            rb_text = element.get_text("", strip=False)
                            rt_rp_tags = element.find_all(['rt', 'rp'])
                            for tag in rt_rp_tags:
                                rb_text = rb_text.replace(
                                    tag.get_text("", strip=False), '')
                        paragraph_parts.append(rb_text.strip())
                    else:
                        paragraph_parts.append(
                            element.get_text("", strip=False))
            paragraph_text = "".join(paragraph_parts).strip()
            if paragraph_text:
                paragraphs.append(paragraph_text)
        full_text = "\n\n".join(paragraphs)
        full_text = re.sub(r'[ \t]+', ' ', full_text)
        full_text = re.sub(r'\n{3,}', '\n\n', full_text)
        return full_text.strip()

    def fetch_episode_content(self, episode_url: str) -> Optional[str]:
        soup = self._make_request(episode_url)
        if not soup:
            logger.error(
                f"Failed to fetch HTML content for episode: {episode_url}")
            return None
        try:
            honbun_div = soup.find("div", id="novel_honbun")
            if not honbun_div:
                honbun_div = soup.find("div", class_="novel_view")
            if not honbun_div:
                # 新構造対応: <div class="js-novel-text p-novel__text">
                honbun_div = soup.find(
                    "div", class_="js-novel-text p-novel__text")
            if not honbun_div:
                logger.error(
                    f"Main text block (novel_honbun, novel_view, or js-novel-text p-novel__text) not found for {episode_url}")
                return None
            if honbun_div.get("class") and "js-novel-text" in honbun_div.get("class"):
                logger.debug(
                    "Using new content container 'div.js-novel-text.p-novel__text'.")
            elif honbun_div.get("id") == "novel_honbun":
                logger.debug(
                    "Using primary content container 'div#novel_honbun'.")
            else:
                logger.debug(
                    "Using fallback content container 'div.novel_view'.")
            cleaned_text = self._extract_text_with_ruby_as_plain(honbun_div)
            if not cleaned_text:
                logger.warning(
                    f"Extracted empty content for episode {episode_url}. HTML structure might have changed.")
            logger.info(
                f"Successfully fetched and cleaned episode content for {episode_url}. Length: {len(cleaned_text)}")
            return cleaned_text
        except Exception as e:
            logger.error(
                f"Error parsing episode content for {episode_url}: {e}", exc_info=True)
            return None


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_novel_url = sys.argv[1]
    else:
        test_novel_url = "https://ncode.syosetu.com/n6316bn/"
    scraper = NarouScraper(request_delay_sec=0.5)
    print(f"[Test] Fetching metadata for: {test_novel_url}")
    metadata = scraper.fetch_novel_metadata(test_novel_url)
    if metadata:
        print("\n--- [Test] Novel Metadata ---")
        print(f"Title: {metadata.get('title')}")
        print(f"Author: {metadata.get('author')}")
        print(f"Tags: {metadata.get('tags')}")
        print(f"Synopsis: {metadata.get('synopsis')}")
        episode_data_list = metadata.get('raw_episode_data', [])
        print(f"Total Episodes Found: {len(episode_data_list)}")
        if episode_data_list:
            for i, ep_data in enumerate(episode_data_list[:2]):
                print(
                    f"\n--- [Test] Episode #{ep_data.get('number')} ({ep_data.get('title')}) ---")
                print(f"URL: {ep_data.get('url')}")
                print(
                    f"Pub Date: {ep_data.get('publication_date_str')} {ep_data.get('update_time_str') or ''}")
                content = scraper.fetch_episode_content(ep_data.get('url'))
                if content is not None:
                    print(
                        f"Content Fetched (length: {len(content)}). First 200 chars:")
                    print(content[:200].replace('\n', '\\n') + "...")
                else:
                    print("Failed to fetch episode content.")
                print("-" * 20)
        else:
            print("[Test] No episode data found in metadata.")
    else:
        print("[Test] Failed to fetch novel metadata.")
