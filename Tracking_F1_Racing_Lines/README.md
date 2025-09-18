# Tracking Formula 1 Racing Lines

The purpose of this project is to track F1 racing lines to determine if the driver is taking the optimal racing line on difficult corners. First, an objection detection model is built to recognize these cars and then tracking is implemented on this model to track the racers' racing lines.

## Table of Contents

* [Setup](#setup)
* [Technologies](#technologies)
* [Preprocessing Data](#preprocessing-data)
* [Performance Metrics](#performance-metrics)
* [Deployment](#deployment)
* [Improvements](#improvements)
* [Problems](#problems)
* [Resources](#resources)

## Setup

This project uses an Ultralytics YOLOv12s model on initial training then uses the newly trained model for future training. Model performance metrics which include training and validation are uploaded to an MLFlow server. For the dataset, it's collected and annotated using Roboflow where an AWS Lambda function is used to upload images to the dataset. 

## Technologies

- Python 3.12
- Ultralytics YOLO model
- Roboflow
- MLFlow
- AWS S3 and Lambda functions
- Docker

## Preprocessing Data

For this I used Roboflow's dataset annotation tools to preprocess this data. The dataset is public and can be seen [here](https://universe.roboflow.com/personal-projects-1z8ra/f1-tracking-ccjlv).

## Performance Metrics

The metrics used to evaluate this model are: precision, recall, f1 score, and precision-recall curve. These metrics are based on the bounding boxes. Also pictures of these metrics are sent to an MLFlow server which is locally hosted for now. Also a CSV file is created which shows the instances, images, and performance metrics said before. Pictures of the metrics shown on the server are shown in the performance metrics folder in this project. 

## Deployment

## Improvements

## Problems

## Resources

