"""
This file creates and trains the object detection model for F1 cars.
Also it'll track the racing lines of the cars against the optimal line.

A requirements.txt file will be included in the repo if you want to 
replicate this project.
"""

# Standard Library imports


# Third Party imports
from ultralytics import YOLO, settings


class TrackCars():
    """
    This class will train the model and perform inference.
    """

    def __init__(self) -> None:
        """
        Initialize the model.
        """

        self.model = YOLO(model='yolo12s.pt')
        self.results: dict | None

        # change ultralytics settings for MLflow
        settings.update({"mlflow": True})


    def train_model(self) -> dict | None:
        """
        Split the data into train and test. Then train the model using YOLOv12.
        """

        self.results = self.model.train(data="annotations/data.yaml", epochs=50, imgsz=640, device='mps')

        if self.results is not None:
            return self.results



if __name__ == "__main__":

    model = TrackCars()
    results = model.train_model()
    