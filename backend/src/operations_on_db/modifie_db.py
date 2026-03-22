import json

with open("neo4j_query_table_data_2026-3-10.json", "r") as f:
    data = json.load(f)

cypher = data[0]["cypherStatements"]

# Ajouter provisioning et configuration après composition_static pour cloudify
old = '{start: {id:"O.cloudify"}, end: {id:"C.composition_static"}, properties:{}}, {start: {id:"O.cloudify"}, end: {id:"C.deployment"}'
new = '{start: {id:"O.cloudify"}, end: {id:"C.composition_static"}, properties:{}}, {start: {id:"O.cloudify"}, end: {id:"C.provisioning"}, properties:{}}, {start: {id:"O.cloudify"}, end: {id:"C.configuration"}, properties:{}}, {start: {id:"O.cloudify"}, end: {id:"C.deployment"}'

cypher_fixed = cypher.replace(old, new)

data[0]["cypherStatements"] = cypher_fixed

with open("neo4j_query_table_data_2026-3-10_V2.json", "w") as f:
    json.dump(data, f)

print("Done — vérifie que la modification a été appliquée :")
print("provisioning" in cypher_fixed and "configuration" in cypher_fixed)