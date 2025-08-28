"""Fetching metrics about FAIRness and EVERSE software quality"""

import json
import logging
import math
from pathlib import Path
import time
from typing import Tuple, List, Any, Dict

import pandas as pd
import requests


GENOMIC_EDAM_TOPICS: Tuple[str, ...] = (
    "0622",  # genomics
    "0797",  # comparative
    "3173",  # epi
    "3974",  # epistasis
    "0085",  # functional
    "3174",  # metagenomics
    "3943",  # paleo
    "0208",  # pharmaco
    "0194",  # phylo
    "3796",  # population
    "3922",  # proteo
    "0122",  # structural
    "3308",  # transcriptomics
    "3941",  # metatranscriptomics
)
"""EDAM topic IDs related to genomics
"""

PROTEOMICS_EDAM_TOPICS: Tuple[str, ...] = (
    "0121",  # proteomics
    "3922",  # proteogenmics (sub group of genomics in EDAM but counts for both)
)
"""EDAM topic IDs related to proteomics, plus proteogenomics which is only listed in genomics
"""

MACHINE_LEARNING_EDAM_TOPICS: Tuple[str, ...] = ("3474",)
"""EDAM topic IDs related to machine learning
"""

TOOL_CACHE_FILE = Path.cwd().joinpath("bio.tools.json")
"""Cache file path for the bio.tools response
"""

DF_CACHE_FILE = Path.cwd().joinpath("tools.dataframe.tsv")
"""Cache file path for the dataframe
"""


def get_tools(topic: str) -> List[Dict[Any, Any]]:
    """Gets tools for a given EDAM topic from the bio.tools API.

    Parameters
    ----------
    topic: str
        EDAM topic ID

    Returns
    -------
    List of dictionaries with information as stated in the bio.tools documentation
    https://biotools.readthedocs.io/en/latest/api_usage_guide.html#json

    Raises
    ------
    requests.exceptions.* on connection issues

    """
    tools = []

    page = 1
    max_pages = 0
    # Docs state that topic ID needs to in quotes
    while True:
        url = f"https://bio.tools/api/tool/?topicID=%22topic_{topic}%22&format=json&page={page}"
        logging.info("\t\t ... page %i / %s", page, max_pages if max_pages > 0 else "?")
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            tools.extend(data["list"])
            next_page = data.get("next")
            if next_page is None or next_page == "":
                break
            page += 1
            max_pages = math.ceil(data["count"] / len(data["list"]))
        except requests.RequestException as e:
            if (
                e.response is not None
                and e.response.status_code >= 500
                and e.response.status_code < 600
            ):
                logging.warning(
                    (
                        "Seems like bio.tools got some problems. "
                        " %i encountered. Retrying in a few seconds..."
                    ),
                    e.response.status_code,
                )
                time.sleep(5)
            else:
                continue
        except json.JSONDecodeError as e:
            logging.error("Failed to decode JSON response: %s", e)
            break

    return tools


def tools_to_df(tools: List[Dict[Any, Any]]) -> pd.DataFrame:
    """Convert a list of tools to a pandas DataFrame with the columns:
    * id: tool ID (str)
    * name: tool name (str)
    * is_genomics: (bool)
    * is_proteomics: (bool)
    * is_machine_learning: (bool)
    * documentation: comma separated list (str)
    * repository: comma separated list (str)

    Parameters
    ----------
    tools : List[Dict[Any, Any]]
        List of dictionaries with information as stated in the bio.tools documentation
        https://biotools.readthedocs.io/en/latest/api_usage_guide.html#json

    Returns
    -------
    pd.DataFrame
        DataFrame containing tool information.
    """
    ids = []
    names = []
    is_genomics = []
    is_proteomics = []
    is_machine_learning = []
    documentations = []
    repositories = []

    for tool in tools:
        ids.append(tool.get("biotoolsID", ""))
        names.append(tool.get("name", ""))
        topic_uris = {topic["uri"] for topic in tool["topic"]}
        is_genomics.append(
            any(
                f"http://edamontology.org/topic_{gen_topic}" in topic_uris
                for gen_topic in GENOMIC_EDAM_TOPICS
            )
        )
        is_proteomics.append(
            any(
                f"http://edamontology.org/topic_{prot_topic}" in topic_uris
                for prot_topic in PROTEOMICS_EDAM_TOPICS
            )
        )
        is_machine_learning.append(
            any(
                f"http://edamontology.org/topic_{ml_topic}" in topic_uris
                for ml_topic in MACHINE_LEARNING_EDAM_TOPICS
            )
        )
        documentations.append(",".join([doc["url"] for doc in tool["documentation"]]))
        repositories.append(
            ",".join(
                [link["url"] for link in tool["link"] if "Repository" in link["type"]]
            )
        )

    df = pd.DataFrame(
        {
            "id": ids,
            "name": names,
            "is_genomics": is_genomics,
            "is_proteomics": is_proteomics,
            "is_machine_learning": is_machine_learning,
            "documentation": documentations,
            "repository": repositories,
        }
    )
    return df


def main():
    """Main entrypoint: Loads cached data or downloads them"""
    logging.basicConfig(level=logging.INFO)

    df = pd.DataFrame()

    if DF_CACHE_FILE.is_file():
        logging.info("Dataframe cache file found. Loading data from cache.")
        df = pd.read_csv(DF_CACHE_FILE, sep="\t", encoding="utf-8")
    else:
        tools = []
        if TOOL_CACHE_FILE.is_file():
            logging.info("bio.tools cache file found. Loading data from cache.")
            with TOOL_CACHE_FILE.open("r", encoding="utf-8") as f:
                tools = json.load(f)
        else:
            logging.info("Cache file not found. Fetching data from bio.tools API.")

            logging.info("Fetching proteomic tools...")
            for topic in PROTEOMICS_EDAM_TOPICS:
                logging.info("\t... fetching tools for topic '%s'", topic)
                tools.extend(get_tools(topic))

            logging.info("Fetching genomic tools...")
            for topic in GENOMIC_EDAM_TOPICS:
                logging.info("\t... fetching tools for topic '%s'", topic)
                tools.extend(get_tools(topic))

            with TOOL_CACHE_FILE.open("w", encoding="utf-8") as f:
                json.dump(tools, f)

            logging.info("Removing duplicate tools based on biotoolsID.")
            unique_tools = {tool["biotoolsID"]: tool for tool in tools}
            tools = list(unique_tools.values())

        logging.info("Converting tools to DataFrame.")
        df = tools_to_df(tools)

        logging.info("Writing fetched data to cache file.")
        df.to_csv(DF_CACHE_FILE, sep="\t", index=False, encoding="utf-8")


if __name__ == "__main__":
    main()
