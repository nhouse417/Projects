# Tracking Formula 1 Racing Lines

The purpose of this project is to track F1 racing lines to determine if the driver is taking the optimal racing line on difficult corners. First, an objection detection model is built to recognize these cars and then tracking is implemented on this model to track the racers' racing lines.

## Table of Contents

* [Setup](#setup)
* [Workflow](#workflow)
* [Technologies](#technologies)
* [Preprocessing Data](#preprocessing-data)
* [Performance Metrics](#performance-metrics)
* [Deployment](#deployment)
* [Improvements](#improvements)
* [Problems](#problems)
* [Resources](#resources)

## Setup

This project uses an Ultralytics YOLOv12s model on initial training then uses the newly trained model for future training. Model performance metrics which include training and validation are uploaded to an MLFlow server. For the dataset, it's collected and annotated using Roboflow where an AWS Lambda function is used to upload images to the dataset. 

## Workflow

## Technologies

- Python 3.12
- Ultralytics YOLO model
- Roboflow
- MLFlow
- AWS S3 and Lambda functions
- Docker

## Preprocessing Data

For this I used Roboflow's dataset annotation tools to preprocess this data. The dataset is public and can be seen [here](https://universe.roboflow.com/personal-projects-1z8ra/f1-tracking-ccjlv).

Also, the pictures in the dataset are obtained from public sources such as the F1 official website and youtube videos (this dataset is not going to be used for commercial use but for a personal project).

## Performance Metrics

The metrics used to evaluate this model are: precision, recall, f1 score, and precision-recall curve. These metrics are based on the bounding boxes. Also pictures of these metrics are sent to an MLFlow server which is locally hosted for now. Also a CSV file is created which shows the instances, images, and the bounding box metrics that include precision, recall, f1 score, mAP50, and mAP50-95. Pictures of the metrics shown on the server are shown in the performance metrics folder in this project. 

Shown below is what the MLFlow server looks like. 
<img width="1189" height="579" alt="image" src="https://github.com/user-attachments/assets/6b137bef-8ba4-4fa7-81c2-e1bb8605b8a0" />

## Deployment

I have not deployed this model publicly yet. But the plan is to deploy this model on a cloud service that can be used for F1 object detection projects. I plan to deploy this model on AWS.

## Improvements

These are the improvements that I want to implement for this project:
1. Implement tracking a F1 car through the video and trace its racing line
2. Create a bash script that labels and organizes new images without manual intervention
3. automatic retraining when new data is inserted into the dataset
4. update the model to the latest version if retraining was done
5. deploying model on a cloud service so that others can use it
6. monitor the model for model drift

## Problems

1. The first problem I had was setting up the MLFlow server. In the [documentation](https://mlflow.org/docs/latest/ml/tracking/tutorials/remote-server/) for setting up a remote tracking server, it uses port 5000. But when setting up this remote server on a macbook, port 5000 was already being used by the Airplay Receiver feature. So either you turn that feature off or use another port. I chose to use another port which is 5001.

2. The AWS Lambda function that's used to send new images to the Roboflow dataset wasn't completing its operation. The Roboflow dataset wasn't receiving the new images because the AWS Lambda function was timing out before the images could be sent to Roboflow. The default timeout was 3s which was not enough time. I know this because I looked at the Cloudwatch Logs which showed no problems with the function itself, but it showed that the function timed out. So I increased the timeout of the function incrementally from 3s to 10s. It still wasn't enough and so I increased it to 20s, and it worked for 1 new image. But when I increased the new images to 2 new images. The twenty seconds wasn't enough and so I increased it to 30s. My conclusion was that the more images that are added to the S3 bucket at one time, the longer the function needs before timing out. 

## Resources

- [How to set up remote tracking server with MLFlow](https://mlflow.org/docs/latest/ml/tracking/tutorials/remote-server/)
- [How to connect AWS S3 to Roboflow](https://blog.roboflow.com/how-to-use-s3-computer-vision-pipeline/)
- [AWS Documentation](https://docs.aws.amazon.com)
- [AWS Event dictionary for lambda handler](https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-content-structure.html)
- [Log Ultralytics YOLO experiments using MLFlow integration](https://www.ultralytics.com/blog/log-ultralytics-yolo-experiments-using-mlflow-integration)
