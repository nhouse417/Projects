import requests

url = "http://127.0.0.1:5000/recipes"
newRecipe = {
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

resp = requests.put(url, data=newRecipe)

resp1 = requests.get(url)
print(resp1.json())