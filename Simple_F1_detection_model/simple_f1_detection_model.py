"""
This file implements a simple F1 detection model using an Ultralytics YOLOv11 model.
"""

# Standard Library Imports
from pathlib import Path

# Third Party Imports
from ultralytics.models import YOLO
from ultralytics.engine.results import Results
from ultralytics.utils.metrics import DetMetrics


class SimpleF1DetectionModel:
    """
    Defines the F1 detection model and its functions.
    """

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


    def train_model(self) -> dict | None:
        """
        Trains the model and outputs the training results.

        Note: If you're using a Macbook with a silicon chip, you can input the parameter
              device='mps' which leverages Apple's silicon chip for high-performance execution
              of computation and image processing tasks.

        Output:
            - dict containing training metrics
        """

        train_results = self.model.train(data="dataset/data.yaml",
                                         epochs=10,
                                         imgsz=640,
                                         device='mps')

        if train_results is None:
            print("Something went wrong with training.")
        else:
            return train_results


    def validate_model(self) -> DetMetrics | None:
        """
        Validate the model. This function remembers the model's settings so don't have to put 
        anything into the function.

        https://docs.ultralytics.com/modes/val/

        Output:
            - DetMetrics -> Utility class for computing detection metrics such as precision, recall,
                            and mean average precision (mAP). Class can be seen in the link below.

        https://github.com/ultralytics/ultralytics/blob/main/ultralytics/utils/metrics.py
        """

        return self.model.val() if self.model.val() is not None else None


    def run_inference(self, data: str | Path) -> list[Results] | Results:
        """
        Run inference on the given video or image sequence.

        Note: 'Source' is the only required parameter for this function.
              The other parameters are optional:
                - 'imgsz' -> filling in this parameter can improve detection accuracy and processing speed
                - 'conf' -> sets the minimum confidence. Values below this will be disregarded which would 
                            help reducing false positives
                - 'save' -> saves annotated images or videos
                - 'show' -> displays the annotated images or videos in a window

        https://docs.ultralytics.com/modes/predict/#inference-arguments
        """

        inference_results = self.model.predict(source=data,
                                               imgsz=640,
                                               conf=0.6,
                                               save=True,
                                               show=True)

        return inference_results


if __name__ == "__main__":

    # --------------------------------
    # start with the pre-trained model which will default to 'yolo11s.pt'
    # after first training, use the 'runs/detect/train/weights/best.pt' model for further training

    # model = SimpleF1DetectionModel()
    # training_results = model.train_model()
    # ---------------------------------

    # create a new model based on the previously trained model for our dataset
    model = SimpleF1DetectionModel(model_path='runs/detect/train/weights/best.pt')
    training_results = model.train_model()

    # explain that the pre-trained model is trained using the coco model but we
    # need to train the model using our dataset
