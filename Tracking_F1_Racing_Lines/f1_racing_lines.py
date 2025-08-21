"""
This file creates and trains the object detection model for F1 cars.
Also it'll track the racing lines of the cars against the optimal line.

A requirements.txt file will be included in the repo if you want to 
replicate this project.
"""

# Standard Library imports


# Third Party imports
from ultralytics import YOLO


class TrackCars():
    """
    This class will train the model and perform inference.
    """

    def __init__(self) -> None:
        """
        Initialize the model.
        """

        self.model = YOLO(model='yolo12s.pt')


    def train_model(self) -> None:
        """
        Split the data into train and test. Then train the model using YOLOv12.
        """

if __name__ == "__main__":

    model = TrackCars()
