from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_exponential

from config import config


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_category_map():
    """Return {category_id (str): category_name} for REGION_CODE."""
    youtube = build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)
    response = (
        youtube.videoCategories().list(part="snippet", regionCode=config.REGION_CODE).execute()
    )
    return {item["id"]: item["snippet"]["title"] for item in response.get("items", [])}
