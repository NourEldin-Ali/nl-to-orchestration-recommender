import os
from urllib.parse import urlparse

from dotenv import load_dotenv


class Neo4jConnector:
    """
    Connector for Neo4j settings and driver creation.

    Attributes:
        uri (str): Neo4j bolt/neo4j/http URI.
        username (str): Neo4j username.
        password (str): Neo4j password.
        database (str): Neo4j database name.
        http_uri (str): Neo4j HTTP base URI used for transaction API fallback.
    """

    def __init__(
        self,
        uri: str | None = None,
        username: str | None = None,
        password: str | None = None,
        database: str | None = None,
        http_uri: str | None = None,
    ):
        load_dotenv()

        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username if username is not None else os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password if password is not None else os.getenv("NEO4J_PASSWORD", "password")
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")
        self.http_uri = http_uri or os.getenv("NEO4J_HTTP_URI") or self._http_base_from_neo4j_uri(self.uri)

    def __call__(self):
        return self.get_driver()

    def get_auth(self) -> tuple[str, str] | None:
        if self.username == "" and self.password == "":
            return None
        return self.username, self.password

    def get_http_endpoint(self) -> str:
        return f"{self.http_uri.rstrip('/')}/db/{self.database}/tx/commit"

    def get_driver(self):
        from neo4j import GraphDatabase

        return GraphDatabase.driver(self.uri, auth=self.get_auth())

    @staticmethod
    def _http_base_from_neo4j_uri(uri: str) -> str:
        parsed = urlparse(uri)
        scheme = parsed.scheme.lower()
        host = parsed.hostname or "localhost"

        if scheme in {"http", "https"}:
            port = parsed.port or (443 if scheme == "https" else 80)
            return f"{scheme}://{host}:{port}"

        if scheme in {"neo4j+s", "neo4j+ssc", "bolt+s", "bolt+ssc"}:
            return f"https://{host}:7473"

        return f"http://{host}:7474"
