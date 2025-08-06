# Pedestrian Detection with YOLOv11 Model

The goal of this project is to detect pedestrians from other objects using a YOLOv11 object detection model.

## Table of Contents 

* [Setup](#setup)
* [Preprocess Data](#preprocess-data)
* [Running the Model](#running-the-model)
* [Performance Metrics](#performance-metrics)
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

### Normalize the data between 0 and 1 for the YOLO Model

Now, it's time to prepare the data for the YOLO detection model which requires a specific dataset format for the model to work (format shown below). 

<img width="151" height="152" alt="image" src="https://github.com/user-attachments/assets/d5347e2f-d732-4202-8f28-971ebf503a99" />

But our dataset is in this format (shown below) but without the 'gt_normalized.txt' and 'labels' folders which will be explained.

<img width="259" height="401" alt="image" src="https://github.com/user-attachments/assets/a8f17258-e0b1-4654-8a58-d6793889dcd2" />

First, in order for the YOLO model to do it's calculations, the data needs to be normalized between 0 and 1. The 'gt.txt' file in the 'gt' folder is the data that needs to be normalized. In gt.txt, the data is ordered as frame number, identity number, bounding box coordinates, confidence score, class, and visibility. We only need to normalize the bounding box coordinates which are 'bounding box left', 'bounding box top', 'bounding box width', 'bounding box height'. 'Bounding box left' is the x-coordinate of the top left corner of the bounding box and 'bounding box top' is the y-coordinate. 

To normalize all of this data efficiently, I put all the data into a pandas dataframe and normalized the bounding box coordinates along with the height and width. The formulas used are shown below (bounding box = bb):

  - bb_left: bb_left + (bb_width / 2) / img_width
  - bb_top: bb_top + (bb_height / 2) / img_height
  - bb_width: bb_width / img_width
  - bb_height: bb_height / img_height

This can be seen in the function **'convert_data_to_yolo'**. Also the reason that I divide the bb_width and bb_height by 2 is to find the center of the bounding box for the (x, y) coordinates.

After normalizing the data, a new file is created called 'normalized_gt' that contains the normalized data.

### Creating labels for each image

For the YOLO model to work, it needs to have a 'labels' folder in the dataset. The model uses the labels folder to help with object detection for each picture. The labels provide the object detections in each image which include the class and the bounding box coordinates. This can be seen in the function **'create_image_annotations'**.

In this function, I create a new folder called 'labels'. Then I implement a for loop iterating through the normalized values by 'Frame_Number' so that I iterate in order of the frames. In the loop, I drop the columns that aren't needed such as 'Frame_Number', 'Identity_Number', 'confidence_score', and 'visibility' which leave the class number and bounding box coordinates. I also trim the floating point numbers to 6 decimal places for readability and more decimal places aren't needed. 

Then I create a new .txt file with the image number as the name. It's important that the labels files are exactly the same name as the image filename because the model finds the labels according to the image name.

An example is shown below. 

<img width="473" height="502" alt="image" src="https://github.com/user-attachments/assets/f2b878be-63cc-4ab7-a05e-66e04c49d74a" />


### Formatting the dataset to YOLO format

As shown above in the introduction, the YOLO model needs a certain dataset format to work. In the **transfer_images_and_labels_for_model_training** function, I transfer the images and labels to a new directory called 'dataset_training' in the YOLO format. 

**Another important file that the YOLO model needs is the .yaml file**. This is key for the model to know which directories are for training and validation, the number of classes, and the names of the classes for object detection. The creation of this .yaml file is seen in function **create_dataset_yaml_file**. 

An example for a dataset is shown below.

<img width="367" height="418" alt="image" src="https://github.com/user-attachments/assets/1555df97-d455-4cad-b562-c2d1b96e12d9" />


## Running the Model

Now that the data is preprocessed and formatted correctly for the model. It's time to train the model. There are a lot of hyperparemeters that can be changed, but I decided to keep it simple for now since this is my first time using this model.

```python
yolo_model = YOLO('yolo11m.pt')
yolo_model.train(data=model.dataset_training_yaml_paths['MOT17-02'], epochs=10, imgsz=640, device='mps')
```

- data -> contains the relative path for the dataset that you want to train
- epochs -> how many times you want the model to run
- imgsz -> the image size which needs to a multiple of 32 because that's the model's max stride
  - for example, if you want to go through 1080 size pictures, the imgsz would need to 1088
- device -> 'mps' because I'm running this model on an Apple silicon chip laptop

Other common training parameters are 'batch' and 'save'. Batch refers to the batch size which refers to the number of training examples processed in one iteration before the model's weights are updated. There are three modes for batch but I used the default number which is 16. In another training run, I was processing 1080 images and there wasn't enough computer memory to support processing 16 images at once at that resolution so I changed the default batch value to 4.

The runtime of training depends on how many epochs and how big of a model you're running (in the above example, I'm running a medium model) and also how large your dataset is. For me on average, it's taken around 8 hours for one training run of 10 epochs. I think I could significantly cut this time down if I chose a smaller YOLO model, but I wanted more object detection accuracy for when I run inference on a dataset the model hasn't seen.

After training the model, a folder is created containing performance metrics and pictures, best weights, PyTorch models for best weight and last saved model, and example pictures of the model doing object detection on certain frames.

<img width="262" height="556" alt="image" src="https://github.com/user-attachments/assets/e17133b2-3345-4673-a088-5ab303281469" />

## Performance Metrics







