import requests

url = "http://127.0.0.1:5000/recipes"
newRecipe = {
  "name" : "butterBagel",
  "ingredients" : [
    "1 bagel",
    "butter"
  ],
  "instructions" : [
    "cut the bagel",
    "spread butter on bagel"
  ]
}

requests.post(url, data=newRecipe)


