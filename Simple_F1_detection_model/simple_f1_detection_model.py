"""
This file implements a simple F1 detection model using an Ultralytics YOLOv11 model.
"""

# Standard Library Imports
from pathlib import Path

# Third Party Imports
from ultralytics import YOLO, settings
from ultralytics.engine.results import Results


class SimpleF1DetectionModel:

    def __init__(self, model_path: str | Path | None = None) -> None:
        """
        Initialize the model with the given model path.

        Inputs:
            model: str | Path = path to the model 
        """

        # check if given a model
        if model_path is None:
           self.model = YOLO(model='yolo11s.pt')
        else:
            self.model = YOLO(model=model_path)


    def train_model(self) -> None:
        """
        Trains the model.
        """
        train_results = self.model.train()


    def validate_model(self) -> None:
        """
        Validate the model.
        """

    def run_inference(self, data: str | Path) -> list[Results] | Results:
        """
        Run inference on the given video or image sequence.
        """


if __name__ == "__main__":

    model = SimpleF1DetectionModel(model_path=)


