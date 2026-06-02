"""
This file creates and trains the object detection model for F1 cars.
Also it'll track the racing lines of the cars against the optimal line.

A requirements.txt file will be included in the repo if you want to 
replicate this project.
"""

# Standard Library imports
from collections import defaultdict
import os
from pathlib import Path

# Third Party imports
import cv2
from dotenv import load_dotenv
import mlflow
import numpy as np
import polars as pl
from ultralytics import YOLO, settings
from ultralytics.engine.results import Results


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
        if model_path is not None:
            self.model_path = YOLO(model=model_path)
        else:
            self.model_path = YOLO(model='yolo12s.pt')

        if yaml_path is not None:
            self.yaml_path = yaml_path
        else:
            self.yaml_path = "annotations/data.yaml"

        # for saving training results
        self.train_results: dict | None

        # change ultralytics settings for MLflow
        settings.update({"mlflow": True})


    def train_model(self) -> dict | None:
        """
        Split the data into train and test. Then train the model using YOLOv12.
        """

        self.train_results = self.model_path.train(data=self.yaml_path, epochs=50, imgsz=640, device='mps')

        if self.train_results is not None:
            return self.train_results


    def validate_model(self) -> None:
        """
        This function uses the val() function to evaluate the model. Then logs these metrics to MLflow.
        """

        load_dotenv()

        # set the mlflow server uri and set active experiment
        mlflow.set_tracking_uri(uri=os.getenv('MLFLOW_TRACKING_URI', 'file:./mlruns'))
        mlflow.set_experiment(experiment_name=os.getenv('MLFLOW_EXPERIMENT_NAME', 'default'))

        # # start the mlflow run
        with mlflow.start_run():

            # validate the model
            val_results = self.model_path.val()

            # log validation metrics
            val_results_df = pl.DataFrame(val_results.to_df())
            logging_path: Path = val_results.save_dir / "validation_metrics.csv"
            val_results_df.write_csv(logging_path, separator=',')

            # save validation pictures that were produced
            mlflow.log_artifacts(local_dir=val_results.save_dir)

        # end the mlflow run
        mlflow.end_run()


    def run_inference(self, data: str | Path) -> list[Results] | Results:
        """
        Run inference on the given data.

        Inputs:
            - data: str | Path = to the source of the data

        Output:
            - a list of Results objects or a Python generator of Results objects
                - depends on the value for the 'stream' parameter in predict function
                    - if False (default) -> list of Results objects
                    - if True -> generator of Results objects
        """

        inference_results = self.model_path.predict(source=data,
                                                    imgsz=640,
                                                    conf=0.6,
                                                    save=True,
                                                    show=True)
        return inference_results


    def track_racing_lines(self) -> None:
        """
        This code is from the YOLO documentation about how to track objects 
        through multiple video frames. I added some checks as well.

        Link here: https://docs.ultralytics.com/modes/track/#plotting-tracks-over-time
        """

        # Open the video file
        video_path = "miami_gp_t17.mov"
        cap = cv2.VideoCapture(video_path)

        # Store the track history
        track_history = defaultdict(lambda: [])

        if not cap.isOpened():
            print("Can't open video file.")
            exit()

        # Loop through the video frames
        while cap.isOpened():
            # Read a frame from the video
            success, frame = cap.read()

            if not success:
                print("Can't receive the frame.")
                break

            if success:
                # Run YOLO12 tracking on the frame, persisting tracks between frames
                result = self.model_path.track(frame, persist=True)[0]

                # Get the boxes and track IDs
                if result.boxes and result.boxes.is_track:
                    boxes = result.boxes.xywh.cpu()
                    track_ids = result.boxes.id.int().cpu().tolist()

                    # Visualize the result on the frame
                    frame = result.plot()

                    # Plot the tracks
                    for box, track_id in zip(boxes, track_ids):
                        x, y, _, _ = box
                        track = track_history[track_id]
                        track.append((float(x), float(y)))  # x, y center point
                        if len(track) > 30:  # retain 30 tracks for 30 frames
                            track.pop(0)

                        # Draw the tracking lines
                        points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
                        cv2.polylines(frame, [points], isClosed=False, color=(230, 230, 230), thickness=10)

                # Display the annotated frame
                cv2.imshow("YOLO12 Tracking", frame)

                # Break the loop if 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            else:
                # Break the loop if the end of the video is reached
                break

        # Release the video capture object and close the display window
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":

    model = TrackCars(model_path='runs/detect/train5/weights/best.pt')
    # training_results = model.train_model()
    # model.validate_model()
    # results = model.run_inference(data='example_videos/example.mp4')
    model.track_racing_lines()
