# Simple JSON API

This API keeps data of food recipes such as a recipe's name, ingredients, and instructions. 

## Table of Contents
* [Description](#description)
* [Setup](#setup)
* [How to Use](#howtouse)
* [Technologies](#technologies)

## Description

The API is able to add new recipes to its dataset through POST requests, and it's able to update existing recipes in the dataset through PUT requests. There is currently not option for deleting a recipe in the dataset. 

The POST requests can be done individually using the recipePost.py script that I've included in this directory. Also the PUT requests can be done individually using the recipePut.py script that I've also included. To run all of the tests that I ran for the API, you can use the recipeFullScript.py script to run all of the tests. Also in these scripts, I've included print statements so that the user can look at the feedback from the server. 

## Setup 

For setup, I followed this person on youtube linked [here](https://www.youtube.com/watch?v=Xw6F4N1j9v4). I used Python3 with the Flask library to create this simple API. There are other ways to do this, but I wanted to expand my Python API skills so that's why I chose to do it this way. 

The link will show you how to setup your environment so that the server will be running with your api on it. Unlike the video I didn't use vim as my code editor, but I used Visual Studio Code. Also I used two terminals, one acting as the client, and the other acting as the server. Through the client terminal, I would use the scripts I made to POST or PUT information towards the server. And then on the server side, I would analyze the output from the server to see if the POST and PUT operations behaved correctly. 

Also, if you followed the video, I was using the server in a virtual environment. The setup for this is in the video. The advantage of a virtual environment is that you can run different versions of libraries. This helps when you have multiple Python files that use different versions of libraries. 

## How to Use

First, I opened two terminals, one for the server, and one for the client. On the client side, the current working directory should contain the scripts that you want to run. And to run these scripts, type "python3 <script_name.py>" on the command line. For the server, type "python3 __main__.py" which will start up the server. 
