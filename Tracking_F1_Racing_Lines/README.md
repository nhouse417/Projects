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

- Python
- Ultralytics YOLO model
- Roboflow
- MLFlow
- AWS S3 and Lambda functions
- Docker

## Preprocessing Data

## Performance Metrics

## Deployment

## Improvements

## Problems

## Resources

