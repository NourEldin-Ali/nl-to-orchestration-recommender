import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config.neo4j_config import Neo4jConnector

CYPHER_FILE = "02_data.cypher"

def import_to_local(cypher_file):
    with open(cypher_file, "r") as f:
        cypher = f.read()
    
    # Découper en statements individuels
    statements = [s.strip() for s in cypher.split(";\n") if s.strip()]
    
    driver = Neo4jConnector().get_driver()
    
    with driver.session() as session:
        for i, statement in enumerate(statements):
            try:
                session.run(statement)
                print(f"[{i+1}/{len(statements)}] OK")
            except Exception as e:
                print(f"[{i+1}/{len(statements)}] ERREUR : {e}")
    
    driver.close()
    print("\nImport terminé !")

if __name__ == "__main__":
    import_to_local(CYPHER_FILE)