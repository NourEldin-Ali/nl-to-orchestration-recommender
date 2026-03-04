import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config.neo4j_config import Neo4jConnector

# Fichier JSON exporté depuis Aura
JSON_FILE = "neo4j_query_table_data_2026-3-4.json"

def import_to_local(json_file):
    # Lire le JSON et extraire le Cypher
    with open(json_file, "r") as f:
        data = json.load(f)
    
    cypher = data[0]["cypherStatements"]
    
    # Découper en statements individuels (séparés par ;\n)
    statements = [s.strip() for s in cypher.split(";\n") if s.strip()]
    
    # Se connecter à Neo4j local via le connecteur
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
    import_to_local(JSON_FILE)