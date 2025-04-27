import requests

url = "http://127.0.0.1:5000/recipes"
newRecipe = {
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

resp = requests.post(url, data=newRecipe)
print(resp.json())

resp = requests.get(url)
print(resp.json())


