import re
from typing import Union, Dict, List

try:
    from serpapi import GoogleSearch 
    _HAS_GOOGLESEARCH = True
    serpapi = None
except Exception:
    GoogleSearch = None 
    _HAS_GOOGLESEARCH = False
    try:
        import serpapi 
    except Exception:
        serpapi = None 

class SerpAPIClient:
    """
    A client for performing Google searches and fetching currency exchange rates via SerpAPI.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(
        self, 
        query: str, 
        allow_multiple: bool = False
    ) -> Union[Dict, List[Dict]]:
        """
        Perform a Google search via SerpAPI.
        
        Args:
            query: - search query
            allow_multiple: - allow multiple results
        """
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
        }
        if _HAS_GOOGLESEARCH and GoogleSearch is not None:
            search = GoogleSearch(params)
            data = search.get_dict()
        else:
            if serpapi is None:
                raise ImportError("serpapi package is not available")
            data = serpapi.search(params)
            if hasattr(data, "as_dict"):
                data = data.as_dict()
        organic = data.get("organic_results", [])

        if allow_multiple:
            return organic[:10]
        return organic[0] if organic else None

    async def get_exchange_rate(
        self, 
        currency: str, 
        target: str
        ) -> str:
        """
        Fetch the exchange rate of 1 CAD to the target currency.

        Args: 
            currency: - currency name
            target: - currency code
        """
        try:
            params = {
                "engine": "google",
                "q": f"1 Canadian Dollar to {target} {currency}",
                "api_key": self.api_key,
                "num": 3,
            }

            if _HAS_GOOGLESEARCH and GoogleSearch is not None:
                data = GoogleSearch(params).get_dict()
            else:
                if serpapi is None:
                    raise ImportError("serpapi package is not available")
                data = serpapi.search(params)
                if hasattr(data, "as_dict"):
                    data = data.as_dict()
            organic = data.get("organic_results", [])
            if not organic:
                return ""

            combined_text = " ".join(
                f"{r.get('title', '')} {r.get('snippet', '')}"
                for r in organic[:3]
            )

            return combined_text

        except Exception as e:
            print(f"[SerpAPIClient] Error fetching exchange rate: {e}")

        return ""

    async def get_dli_information(
        self, 
        institution_name: str, 
        ) -> str:
        """
        Fetch data on if an Institution is a DLI or not.
        This will be used for when we do not have the institution in the database

        Args: 
            institution_name: - Name of the institution
        """
        try:
            params = {
                "engine": "google",
                "q": f"Is {institution_name} a DLI and what is their DLI Number",
                "api_key": self.api_key,
                "num": 3,
            }

            data = GoogleSearch(params).get_dict()
            organic = data.get("organic_results", [])
            if not organic:
                return ""

            combined_text = " ".join(
                f"{r.get('title', '')} {r.get('snippet', '')}"
                for r in organic[:3]
            )

            return combined_text

        except Exception as e:
            print(f"[SerpAPIClient] Error fetching dli information: {e}")

        return ""
