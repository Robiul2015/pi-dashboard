import os
import asyncio
from notion_client import Client


class NotionService:
    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN")
        self.goals_db = os.getenv("NOTION_GOALS_DATABASE_ID")

        if self.token and self.token != "your_notion_integration_token":
            self.client = Client(auth=self.token)
        else:
            self.client = None

        self._cached_alarms = []

    def _extract_text(self, prop):
        """Extract plain text from a Notion property regardless of type."""
        if not prop:
            return ""
        prop_type = prop.get("type", "")
        if prop_type == "rich_text" and prop.get("rich_text"):
            return prop["rich_text"][0].get("plain_text", "").strip()
        if prop_type == "title" and prop.get("title"):
            return prop["title"][0].get("plain_text", "").strip()
        if prop_type == "select" and prop.get("select"):
            return prop["select"].get("name", "").strip()
        if prop_type == "number" and prop.get("number") is not None:
            return str(prop["number"])
        return ""

    def _parse_item(self, item):
        """Parse a Notion DB row into (name, alarm_time) tuple."""
        props = item.get("properties", {})
        title_prop = props.get("Name", props.get("Goal", {}))
        name = self._extract_text(title_prop) or "Untitled"
        alarm_prop = props.get("Alarm", {})
        alarm_time = self._extract_text(alarm_prop)
        return name, alarm_time

    async def _query_goals(self):
        """Query the Notion goals database."""
        if not self.client or not self.goals_db:
            return None
        return (await asyncio.to_thread(
            self.client.databases.query, database_id=self.goals_db
        )).get("results", [])

    async def get_goals(self):
        """Returns list of goal display strings with alarm info. Also caches alarm data."""
        results = await self._query_goals()
        if results is None:
            return ["1. Finish Pi Project", "2. Learn Textual", "3. Stay hydrated"]

        try:
            goals = []
            alarms = []
            for item in results:
                name, alarm_time = self._parse_item(item)
                if alarm_time:
                    goals.append(f"{name} [{alarm_time}]")
                    alarms.append({"name": name, "alarm": alarm_time})
                else:
                    goals.append(name)
            self._cached_alarms = alarms
            return goals if goals else ["No daily goals."]
        except Exception as e:
            return [f"Error fetching goals: {e}"]

    def get_cached_alarms(self):
        """Return alarm data from the last get_goals() fetch (no API call)."""
        return self._cached_alarms
