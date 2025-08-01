"""
Main driver file for object tracking using a YOLOv11 model.
The model is tested and trained on MOT16 dataset which is already annotated.
"""

# Standard Library imports
import configparser
from pathlib import Path


# Third Party imports
import cv2
import pandas as pd
import torch
from ultralytics import YOLO


class PedestrianDetection:
    """
    This class will:
        - preprocess MOT17 data to YOLO format for YOLO model
        - run YOLO model to show pedestrian detection in various sequences
    """

    def __init__(self):
        pass


    def normalize_gt(self, filepath: str) -> None:
        """
        Iterates through gt.txt to normalize the values between 0 and 1 so that it can 
        be used for the YOLO model.

        Input: 
            - filepath to the 'gt' directory

        Output: 
            - None, but a new 'gt.txt' file is created named 'gt_normalized.txt'  
        """
        # MOT17Det/train (relative path)
        path_to_iterate = Path(filepath)
        subdirectories = [item for item in path_to_iterate.iterdir() if item.is_dir()]

        # iterate through gt.txt files in each sequence
        for subdirectory in subdirectories:

            # create path towards the gt.txt file
            subdirectory_gt = subdirectory / 'gt' / 'gt.txt'
            gt_df = pd.read_csv(subdirectory_gt, header=None)

            # get imWidth and imHeight from sequence info file
            seq_info_path = subdirectory / 'seqinfo.ini'
            config = configparser.ConfigParser()
            config.read(seq_info_path)
            img_width = int(config['Sequence']['imWidth'])
            img_height = int(config['Sequence']['imHeight'])

            # print(seq_info_path)
            # print(f"img_width: {img_width} and img_height: {img_height}")

            # normalize the bounding box coordinates, image height and width
            normalized_data = self.convert_data_to_yolo(data=gt_df, img_width=img_width, img_height=img_height)

            # how to replace these new values into the gt.txt file??
            normalized_data.to_csv(f"{subdirectory / 'gt_normalized' / 'gt_normalized'}.txt", header=False, index=False)


    def convert_data_to_yolo(self, data: pd.DataFrame, img_width: int, img_height: int) -> pd.DataFrame:
        """
        Normalizes the bounding box coordinates so that it can be used for the YOLO model.

        Input: 
            - data: pd.DataFrame = containing the annotations data
            - img_width: int = image width of the sequence being tested
            - img_height: int = image height of the sequence being tested

        Output:
            - data: pd.DataFrame = containing the normalized values
        """

        # find the center of the bounding box then normalize, normalize width, and normalize height
        # column 2 (bb left), column 3 (bb top), column 4 (bb width), column 5 (bb height)
        # to find the center of the bound box with just the top left coordinates, the formula is
        # x_center = bb_left + (bb_width / 2); y_center = bb_top + (bb_height / 2)
        data[2] = (data[2] + (data[4] / 2)) / img_width
        data[3] = (data[3] + (data[5] / 2)) / img_height
        data[4] = data[4] / img_width
        data[5] = data[5] / img_height

        return data


    def create_image_annotations(self, filepath: str) -> None:
        """
        This function will create the image_annotations.txt files using the normalized ground truth.
        Each image will have its own .txt file containing the object detections in that image.

        The YOLO format for image annotations is: <class_id> <center_x> <center_y> <bb_width> <bb_height>
            - it's space-delimited
        
        IMPORTANT: This function must be run AFTER the 'normalize_gt' function

        Input:
            - filepath for the train or test path
        """

        path_to_iterate = Path(filepath)
        subdirectories = [item for item in path_to_iterate.iterdir() if item.is_dir()]

        # iterate through the MOT subdirectories to create annotated image sets
        for subdirectory in subdirectories:

            # create a 'labels' folder
            labels_path = subdirectory / 'labels'
            labels_path.mkdir(parents=True, exist_ok=True)

            # create path towards 'gt_normalized.txt'
            gt_normalized_path = subdirectory / 'gt_normalized' / 'gt_normalized.txt'
            normalized_gt_df = pd.read_csv(filepath_or_buffer=gt_normalized_path, header=None,
                                           names=['Frame_Number', 'Identity_Number',
                                                  'Bounding_box_left', 'Bounding_box_top',
                                                  'Bounding_box_width', 'Bounding_box_height',
                                                  'confidence_score', 'Class', 'Visibility'])

            # group by 'Frame_Number' to go throguh annotations for each frame
            for region, group in normalized_gt_df.groupby(by='Frame_Number'):

                # create name for .txt file; it has to be exact format as the names in the 'img1' folder
                # which is 000000.txt
                image_number = str(region).zfill(6) + '.txt'

                # filter out unneccessary columns in the dataframe
                group.drop(labels=['Frame_Number', 'Identity_Number', 'confidence_score', 'Visibility'],
                           axis=1, inplace=True)

                # reorder columns: [Class, bb_left, bb_top, bb_width, bb_height]
                yolo_order = ['Class', 'Bounding_box_left', 'Bounding_box_top',
                               'Bounding_box_width', 'Bounding_box_height']
                group_reordered = group[yolo_order]

                # round floats to 6 decimal places
                group_reordered = group_reordered.round({'Bounding_box_left' : 6, 'Bounding_box_top' : 6,
                                                         'Bounding_box_width' : 6, 'Bounding_box_height' : 6})

                # create .txt file for image number
                image_annotations_path = labels_path / image_number
                group_reordered.to_csv(path_or_buf=image_annotations_path,
                                       header=False,
                                       index=False,
                                       sep=' ')


if __name__ == "__main__":

    model = PedestrianDetection()

    model.normalize_gt(filepath='MOT17Det/train')
    model.create_image_annotations(filepath='MOT17Det/train')

    model.normalize_gt(filepath='MOT17Det/validation')
    model.create_image_annotations(filepath='MOT17Det/validation')

    yolo_model = YOLO('yolo11m.pt')
    yolo_model.train(data='dataset.yaml', epochs=10, imgsz=640, device='mps')
