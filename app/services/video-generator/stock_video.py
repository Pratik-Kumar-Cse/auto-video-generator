import requests
import time
import json
from typing import List, Dict
from termcolor import colored

from ..utils import generate_hmac

from ..llm.llm_call import generate_similar_search_terms

from config import config

PEXELS_API_KEY = config.variables["PEXELS_API_KEY"]
STORYBLOCKS_API_KEY = config.variables["STORYBLOCKS_API_KEY"]
STORYBLOCKS_SCRECT_KEY = config.variables["STORYBLOCKS_SCRECT_KEY"]
SUTTERSTOCK_TOKEN = config.variables["SUTTERSTOCK_TOKEN"]


def search_for_stock_videos(query: str, it: int, min_dur: int) -> List[str]:
    """
    Searches for stock videos based on a query.

    Args:
        query (str): The query to search for.

    Returns:
        List[str]: A list of stock videos.
    """

    # Build headers
    headers = {"Authorization": PEXELS_API_KEY}

    # Build URL
    qurl = f"https://api.pexels.com/videos/search?query={query}&per_page={it}"

    # Send the request
    r = requests.get(qurl, headers=headers)

    # Parse the response
    response = r.json()

    # Parse each video
    raw_urls = []
    video_url = []
    video_res = 0
    try:
        # loop through each video in the result
        for i in range(it):
            # check if video has desired minimum duration
            if response["videos"][i]["duration"] < min_dur:
                continue
            raw_urls = response["videos"][i]["video_files"]
            temp_video_url = ""

            # loop through each url to determine the best quality
            for video in raw_urls:
                # Check if video has a valid download link
                if ".com/video-files" in video["link"]:
                    # Only save the URL with the largest resolution
                    if (video["width"] * video["height"]) > video_res:
                        temp_video_url = video["link"]
                        video_res = video["width"] * video["height"]

            # add the url to the return list if it's not empty
            if temp_video_url != "":
                video_url.append(temp_video_url)

    except Exception as e:
        print(colored("[-] No Videos found.", "red"))
        print(colored(e, "red"))

    # Let user know
    print(colored(f'\t=> "{query}" found {len(video_url)} Videos', "cyan"))

    # Return the video url
    return video_url


def search_for_stock_videos_on_story_block(
    queries: list, it=4, min_dur=10
) -> List[str]:
    """
    Searches for stock videos based on a query.

    Args:
        query (str): The query to search for.
        api_key (str): The API key to use.

    Returns:
        List[str]: A list of stock videos.
    """
    try:
        # Parse each video
        video_url = []

        for query in queries:
            data = call_story_block_api(query, it, min_dur)
            if len(data["results"]) != 0:
                break

        if len(data["results"]) == 0:

            result_data = generate_similar_search_terms(query)

            print(colored(f"result_data : {result_data}", "yellow"))

            for result in result_data:
                data = call_story_block_api(result, it, min_dur)
                if len(data["results"]) != 0:
                    break

        # loop through each video in the result
        for i in range(len(data["results"])):
            temp_video_url = data["results"][i]["preview_urls"]["_720p"]
            if not temp_video_url:
                temp_video_url = data["results"][i]["preview_urls"]["_480p"]
            # add the url to the return list if it's not empty
            if temp_video_url != "":
                video_url.append(temp_video_url)

    except Exception as e:
        print(colored("[-] No Videos found.", "red"))
        print(colored(e, "red"))

    if len(video_url) == 0:

        for query in queries:
            res = call_shutterstock_api(query, it, min_dur)
            print(res)
            if len(res) != 0:
                break

        for data in res:
            video_url.append(data["preview_url"])

    # Let user know
    print(colored(f'\t=> "{query}" found {len(video_url)} Videos', "cyan"))

    # Return the video url
    return video_url


def call_story_block_api(query: str, it, min_dur):
    # Build headers
    headers = {
        "Content-Type": "application/json",
    }

    expires = str(int(time.time()) + (1 * 60 * 60))

    params = {
        "APIKEY": STORYBLOCKS_API_KEY,
        "EXPIRES": expires,  # Replace with expiration timestamp
        "HMAC": generate_hmac(STORYBLOCKS_SCRECT_KEY, expires),
        "project_id": "475b6acd-c6d1-4361-8ce8-bdfce2e8a096",
        "user_id": "475b6acd-c6d1-4361-8ce8-bdfce2e8a094",
        "keywords": query,
        "content_type": "motionbackgrounds,templates",
        # "Content-Type": application/json
        # "quality": quality,
        "min_duration": min_dur,
        # "max_duration": 25,
        # "has_talent_released": has_talent_released,
        # "has_property_released": has_property_released,
        # "has_alpha": has_alpha,
        # "is_editorial": is_editorial,
        # "categories": categories,
        "page": 1,
        "results_per_page": it,
        # "sort_by": sort_by,
        # "sort_order": sort_order,
        # "required_keywords":required_keywords,
        # "filtered_keywords":filtered_keywords,
    }

    # Build URL
    url = "https://api.storyblocks.com/api/v2/videos/search"

    response = requests.get(url, headers=headers, params=params)

    response.raise_for_status()

    return response.json()


def call_shutterstock_api(query: str, it, min_dur):

    results = []

    # Shutterstock search
    shutterstock_url = "https://api.shutterstock.com/v2/videos/search"
    shutterstock_headers = {"Authorization": f"Bearer {SUTTERSTOCK_TOKEN}"}
    shutterstock_params = {"query": query, "per_page": it, "duration_from": min_dur}

    shutterstock_response = requests.get(
        shutterstock_url, headers=shutterstock_headers, params=shutterstock_params
    )
    if shutterstock_response.status_code == 200:
        shutterstock_data = shutterstock_response.json()
        for video in shutterstock_data.get("data", []):
            results.append(
                {
                    "source": "Shutterstock",
                    "id": video["id"],
                    "title": video["description"],
                    "preview_url": video["assets"]["preview_mp4"]["url"],
                }
            )

    return results


def search_stock_videos(query: str, api_keys: Dict[str, str]) -> List[Dict]:
    """
    Search for stock videos on Getty Images and Shutterstock.

    :param query: The search term
    :param api_keys: A dictionary containing API keys for both services
    :return: A list of dictionaries containing video information
    """
    results = []

    # Getty Images search
    getty_url = "https://api.gettyimages.com/v3/search/videos"
    getty_headers = {"Api-Key": GETTY_IMAGES_API_KEY}
    getty_params = {"phrase": query, "fields": "id,title,preview_url", "page_size": 10}

    getty_response = requests.get(getty_url, headers=getty_headers, params=getty_params)
    if getty_response.status_code == 200:
        getty_data = getty_response.json()
        for video in getty_data.get("videos", []):
            results.append(
                {
                    "source": "Getty Images",
                    "id": video["id"],
                    "title": video["title"],
                    "preview_url": video["preview_url"],
                }
            )

    return results


api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"

# This script requires Python 3.6+ because it uses string interpolation


def search_for_creative_images(phrase, orientations, number_of_people, oauth):
    """Search for creative images given a search phrase and some filters"""
    url = "https://api.gettyimages.com/v3/search/images/creative"
    query_params = {
        "phrase": phrase,
        "orientations": orientations,
        "number_of_people": number_of_people,
    }
    headers = {
        "Api-Key": oauth["api_key"],
        "Authorization": f"Bearer {oauth['access_token']}",
    }
    response = requests.get(url, params=query_params, headers=headers)
    return response


def get_client_credentials_token(key, secret):
    """Get an access token using client credentials grant"""
    url = "https://api.gettyimages.com/v4/oauth2/token"
    payload = f"grant_type=client_credentials&client_id={key}&client_secret={secret}"
    headers = {"content-type": "application/x-www-form-urlencoded"}
    response = requests.request("POST", url, data=payload, headers=headers)
    oauth = json.loads(response.content)
    return oauth


# oauth = get_client_credentials_token(api_key, api_secret)
# oauth["api_key"] = api_key
# search_response = search_for_creative_images(
#     "office workers", "square,vertical", 3, oauth
# )
# print(search_response.text)
