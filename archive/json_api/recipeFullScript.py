import requests

url="http://127.0.0.1:5000/recipes"

# POST data 
postRecipe = {
  "name" : "butteredBagel",
  "ingredients": [
    "1 bagel",
    "butter"
  ],
  "instructions": [
    "cut the bagel",
    "spread butter on bagel"
  ]
}

# PUT data
putRecipe = {
  "name" : "butteredBagel",
  "ingredients" : [
    "1 bagel",
    "2 tbsp butter"
  ],
  "instructions" : [
    "cut the bagel",
    "spread butter on bagel"
  ]
}

# recipe for testing PUT
putRecipe2 = {
  "name" : "spaghetti",
  "ingredients" : [
    "1 bagel",
    "2 tbsp butter"
  ],
  "instructions" : [
    "cut the bagel",
    "spread butter on bagel"
  ]
}

# Part 1
# Get all recipes in database
print('Getting all recipes')
resp = requests.get(url)
print(resp.json())

# Part 2: Get details on specific recipe
# details: ingredients and number of steps of instruction
# if user puts inputs recipe that doesn't exist, output is {}
print('\nGetting details for garlic pasta recipe')
resp = requests.get('{}/details/garlicPasta'.format(url))
print(resp.json())

# Part 3: add new recipe (POST)
print('\nAdding a butteredBagel recipe to database')
resp = requests.post(url, data=postRecipe)
print(resp.json())

# Get recipe list again
print('\nGetting all recipes')
resp = requests.get(url)
print(resp.json())

# Add duplicate recipe to get error using POST
print('\nAdding a duplicate recipe')
resp = requests.post(url, data=postRecipe)
print(resp.json())

# updating a recipe that exists
print('\nUpdating an existing recipe')
resp = requests.put(url, data=putRecipe)
print(resp)

# trying to update a recipe that doesn't exist
print('\nUpdating a non-existent recipe')
resp = requests.put(url, data=putRecipe2)
print(resp)

# Get details of updated recipe (butteredBagel)
print('\nGetting details of an updated butteredBagel recipe')
resp = requests.get('{}/details/butteredBagel'.format(url))
print(resp.json())