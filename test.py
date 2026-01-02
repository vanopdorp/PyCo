import ast

# Python-expressie die we willen omzetten naar een AST
expression = "d.get(c, c)"

# Parse de expressie naar een Abstract Syntax Tree (AST)
tree = ast.parse(expression, mode='eval')

# Weergeven van de AST
print(ast.dump(tree, indent=4))
