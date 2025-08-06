# Pedestrian Detection with YOLOv11 Model

The goal of this project is to detect pedestrians from other objects using a YOLOv11 object detection model.

## Table of Contents 

* [Setup](#setup)
* [Preprocess Data](#preprocess-data)
* [Running the Model](#running-the-model)
* [Metrics](#metrics)
* [Improvements](#improvements)
* [Problems](#problems)
* [Resources](#resources)

## Setup

For this I used a Python virtual environment using Python 3.12.0. I used this version because as of this writing PyTorch isn't supported on Python 3.13. And PyTorch is needed to run the Ultralytics YOLO Models. The libraries I used in this project are listed below.

  - Python 3.12.0
  - Ultralytics 8.3.169
  - Torch 2.7.1
  - Pandas 2.3.1
  - CV2

## Preprocess Data

First, I downloaded a multi-object tracking dataset from the [MOT Challenge website](https://motchallenge.net/data/MOT17Det/), specifically the MOT17Det dataset. This dataset is already annotated with the frame number, identity number, bounding box coordinates, confidence score, class, and visibility. This dataset is the improved version of the MOT16 dataset and the details of that dataset can be seen [here](https://arxiv.org/pdf/1603.00831). 

Now, it's time to prepare the data for the YOLO detection model which requires a specific dataset format for the model to work (format shown below). 

<img width="151" height="152" alt="image" src="https://github.com/user-attachments/assets/d5347e2f-d732-4202-8f28-971ebf503a99" />

But our dataset is in this format (shown below) but without the 'gt_normalized.txt' and 'labels' folders which will be explained.

<img width="259" height="401" alt="image" src="https://github.com/user-attachments/assets/a8f17258-e0b1-4654-8a58-d6793889dcd2" />

