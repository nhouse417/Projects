from flask import Flask, jsonify, request, Response, make_response
app = Flask(__name__)

data = {
  "recipes": [
    {
      "name": "scrambledEggs",
      "ingredients": [
        "1 tsp oil",
        "2 eggs",
        "salt"
      ],
      "instructions": [
        "Beat eggs with salt",
        "Heat oil in pan",
        "Add eggs to pan when hot",
        "Gather eggs into curds, remove when cooked",
        "Salt to taste and enjoy"
      ]
    },
    {
      "name": "garlicPasta",
      "ingredients": [
        "500mL water",
        "100g spaghetti",
        "25mL olive oil",
        "4 cloves garlic",
        "Salt"
      ],
      "instructions": [
        "Heat garlic in olive oil",
        "Boil water in pot",
        "Add pasta to boiling water",
        "Remove pasta from water and mix with garlic olive oil",
        "Salt to taste and enjoy"
      ]
    },
    {
      "name": "chai",
      "ingredients": [
        "400mL water",
        "100mL milk",
        "5g chai masala",
        "2 tea bags or 20 g loose tea leaves"
      ],
      "instructions": [
        "Heat water until 80 C",
        "Add milk, heat until 80 C",
        "Add tea leaves/tea bags, chai masala; mix and steep for 3-4 minutes",
        "Remove mixture from heat; strain and enjoy"
      ]
    }
  ]
}


@app.route('/')
def welcome():
  return "Welcome to my simple JSON API where it keeps data about food recipes"

# Part 1 "/recipes"
# Part 3: POST
@app.route('/recipes', methods=['GET', 'POST', 'PUT'])
def recipeReturn():

  if request.method == 'POST':
    newName = request.form['name']  # check if name is in dictionary already
    for i in range(len(data['recipes'])):
      if data['recipes'][i].get('name') == newName:
        result = jsonify({'error': 'Recipe already exists'})
        return make_response(result, 400)

    newIngredients = request.form.getlist('ingredients')
    newInstructions = request.form.getlist('instructions')
    newRecipe = {'name': newName, 'ingredients': newIngredients, 'instructions': newInstructions}
    data['recipes'].append(newRecipe)
    result = jsonify({})
    return make_response(result, 201)
  
  if request.method == 'GET':
    recipeNames = []
    recipes = data['recipes']
    for i in range(len(recipes)):
      name = recipes[i].get('name')
      recipeNames.append(name)
    result = jsonify({'recipeNames' : recipeNames})
    return make_response(result, 200)

  if request.method == 'PUT':
    recipeName = request.form['name']  # check if recipe exists in dictionary
    for i in range(len(data['recipes'])):
      if recipeName == data['recipes'][i].get('name'):
        updatedIngredients = request.form.getlist('ingredients')
        updatedInstructions = request.form.getlist('instructions')
        updatedRecipe = {'name': recipeName, 'ingredients': updatedIngredients, 'instructions': updatedInstructions}
        data['recipes'][i] = updatedRecipe
        result = jsonify({'success': 'Recipe updated'})
        return make_response(result, 204)

    result = jsonify({'error': "Recipe doesn't exist"})
    return make_response(result, 404)
    
# Part 2: /recipes/details/garlicPasta (string parameter)
@app.route('/recipes/details/<string:recipeName>')
def recipeDetails(recipeName):
  recipes = data['recipes']
  for i in range(len(recipes)):
    if recipes[i].get('name') == recipeName:
      ingredientsList = recipes[i].get('ingredients')
      numSteps = len(recipes[i].get('instructions'))
      result = jsonify({'details': {'ingredients': ingredientsList, 'numSteps': numSteps}})
      return make_response(result, 200)

  result = jsonify({})
  return make_response(result, 200)
