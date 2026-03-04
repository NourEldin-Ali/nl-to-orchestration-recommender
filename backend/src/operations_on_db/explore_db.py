import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config.neo4j_config import Neo4jConnector


def explore(driver):
    with driver.session() as session:

        print("=== LABELS ===")
        for record in session.run("CALL db.labels()"):
            print(f"  - {record['label']}")

        print("\n=== TYPES DE RELATIONS ===")
        for record in session.run("CALL db.relationshipTypes()"):
            print(f"  - {record['relationshipType']}")

        print("\n=== PROPRIÉTÉS PAR LABEL ===")
        for record in session.run("CALL db.propertyKeys()"):
            print(f"  - {record['propertyKey']}")

        print("\n=== NOMBRE DE NOEUDS PAR LABEL ===")
        result = session.run("""
            CALL db.labels() YIELD label
            CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) AS count', {})
            YIELD value
            RETURN label, value.count AS count
            ORDER BY count DESC
        """)
        for record in result:
            print(f"  {record['label']}: {record['count']}")

        print("\n=== NOMBRE DE RELATIONS PAR TYPE ===")
        result = session.run("""
            CALL db.relationshipTypes() YIELD relationshipType
            CALL apoc.cypher.run('MATCH ()-[r:`' + relationshipType + '`]->() RETURN count(r) AS count', {})
            YIELD value
            RETURN relationshipType, value.count AS count
            ORDER BY count DESC
        """)
        for record in result:
            print(f"  {record['relationshipType']}: {record['count']}")

        print("\n=== CONTRAINTES ===")
        for record in session.run("SHOW CONSTRAINTS"):
            print(f"  - {record['name']}: {record['type']} on {record['labelsOrTypes']} {record['properties']}")


if __name__ == "__main__":
    driver = Neo4jConnector().get_driver()
    explore(driver)
    driver.close()
