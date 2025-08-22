"""
This file creates and trains the object detection model for F1 cars.
Also it'll track the racing lines of the cars against the optimal line.

A requirements.txt file will be included in the repo if you want to 
replicate this project.
"""

# Standard Library imports
from pathlib import Path

# Third Party imports
from ultralytics import YOLO, settings


class TrackCars:
    """
    This class will train the model and perform inference.
    """

    def __init__(self, model_path: str | Path | None = None, yaml_path: str | Path | None = None) -> None:
        """
        Initialize the model. Both model and yaml path have to be None or have values.

        Inputs:
            - model: str = path to the model that you want to train
        """

        # if given a model then assign it along with the yaml path
        if model_path is not None and yaml_path is not None:
            self.model_path = YOLO(model=model_path)
            self.yaml_path = yaml_path
        else:
            self.model_path = YOLO(model='yolo12s.pt')
            self.yaml_path = "annotations/data.yaml"

        # variable for saving results
        self.results: dict | None

        # change ultralytics settings for MLflow
        settings.update({"mlflow": True})


    def train_model(self) -> dict | None:
        """
        Split the data into train and test. Then train the model using YOLOv12.
        """

        self.results = self.model_path.train(data=self.yaml_path, epochs=50, imgsz=640, device='mps')

        if self.results is not None:
            return self.results


if __name__ == "__main__":

    model = TrackCars(model_path='runs/detect/train2/weights/best.pt')
    results = model.train_model()
