"""
Main driver file for object tracking using a YOLOv11 model.
The model is tested and trained on MOT16 dataset which is already annotated.
"""

# Standard Library imports
import configparser
from pathlib import Path
import shutil

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
        """
        Holds the CLASS_MAP for the dataset yaml files.
        Also contained a dict of (dataset_training : .yaml relative file paths) for training later
        """
        self.class_map = {
            0: 'Nothing',
            1: 'Pedestrian',
            2: 'Person on Vehicle',
            3: 'Car',
            4: 'Bicycle',
            5: 'Motorbike',
            6: 'Non motorized vehicle',
            7: 'Static person',
            8: 'Distractor',
            9: 'Occluder',
            10: 'Occluder on the ground',
            11: 'Occluder full',
            12: 'Reflection'
        }

        self.class_map_len = len(self.class_map)

        self.dataset_training_yaml_paths = {
            'MOT17-02' : 'dataset_training/MOT17-02/dataset.yaml',
            'MOT17-04' : 'dataset_training/MOT17-04/dataset.yaml',
            'MOT17-05' : 'dataset_training/MOT17-05/dataset.yaml',
            'MOT17-09' : 'dataset_training/MOT17-09/dataset.yaml',
            'MOT17-10' : 'dataset_training/MOT17-10/dataset.yaml',
            'MOT17-11' : 'dataset_training/MOT17-11/dataset.yaml',
            'MOT17-13' : 'dataset_training/MOT17-13/dataset.yaml'
        }


    def normalize_gt(self, filepath: str) -> None:
        """
        Iterates through the ground truth file (gt.txt) to normalize the values between 0 and 1 
        so that it can be used for the YOLO model.

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


    def create_training_folders(self, filepath: str) -> None:
        """
        Formats preprocessed dataset for YOLO model training.

        The format is:
            dataset_name/
                |_ train/
                    |_ images/
                    |_ labels/
                |_ val/
                    |_ images/
                    |_ labels/

        Input:
            - filepath for the directory to be formatted

        An example input would be "MOT17Det/train"

        IMPORTANT: This function must be called AFTER 'normalize_gt' AND 'create_image_annotations'
        """

        path_to_iterate = Path(filepath)
        subdirectories = [item for item in path_to_iterate.iterdir() if item.is_dir()]
        dataset_training_path = Path('dataset_training')

        for subdirectory in subdirectories:

            # count how many images there are then divide into an 80/20 split
            image_folder_path = subdirectory / 'img1'
            labels_folder_path = subdirectory / 'labels'
            img_count = sum(1 for item in image_folder_path.iterdir() if item.is_file())

            # create new directory in 'dataset_training'
            new_dataset_training_path = dataset_training_path / image_folder_path.parent.name
            new_dataset_training_path.mkdir(parents=True, exist_ok=True)

            # create 'train' directory with 'images' and 'labels' subdirectories
            train_directory = new_dataset_training_path / 'train'
            train_directory.mkdir(parents=True, exist_ok=True)

            # create train subdirectories
            train_images_directory = train_directory / 'images'
            train_images_directory.mkdir(parents=True, exist_ok=True)

            train_labels_directory = train_directory / 'labels'
            train_labels_directory.mkdir(parents=True, exist_ok=True)

            # create 'val' directory with 'images' and 'labels' subdirectories
            val_directory = new_dataset_training_path / 'val'
            val_directory.mkdir(parents=True, exist_ok=True)

            # create val subdirectories
            val_images_directory = val_directory / 'images'
            val_images_directory.mkdir(parents=True, exist_ok=True)

            val_labels_directory = val_directory / 'labels'
            val_labels_directory.mkdir(parents=True, exist_ok=True)

            # transfer images from MOT17Det/train to this directory
            self.transfer_images_and_labels_for_model_training(src_filepath=[image_folder_path, labels_folder_path],
                                                               dest_filepath=[train_images_directory, val_images_directory,
                                                                              train_labels_directory, val_labels_directory],
                                                                img_count=img_count)

            # create .yaml file for these training folders
            self.create_dataset_yaml_file(filepath=new_dataset_training_path)


    def transfer_images_and_labels_for_model_training(self,
                                                      src_filepath: list[Path],
                                                      dest_filepath: list[Path],
                                                      img_count: int) -> None:
        """
        Transfers images and labels from the 'MOT17Det/Train' directory to the 'dataset_training/MOT17-XX' training or val
        directories.

        Input:
            - src_filepath: list[Path] = contains the filepaths 'train/MOT17-XX/img1' and 'train/MOT17-XX/labels'
            - dest_filepath: list[Path] = contains the destination filepaths for images and labels
            - img_count: int = number of images and labels which is the same number
        """

        # divide the img_count into an 80/20 split for training and validation
        train_count = int(img_count * 0.8)

        # transfer the images
        image_counter = 1
        for image, label in zip(sorted(src_filepath[0].iterdir()), sorted(src_filepath[1].iterdir())):

            # check if counter > train_count, if so then start transferring files to validation
            if image_counter > train_count:
                shutil.copy2(src=image, dst=dest_filepath[1])
                shutil.copy2(src=label, dst=dest_filepath[3])
            else:
                shutil.copy2(src=image, dst=dest_filepath[0])
                shutil.copy2(src=label, dst=dest_filepath[2])

            image_counter += 1

    def create_dataset_yaml_file(self, filepath: Path) -> None:
        """
        For each subdirectory in 'dataset_training', create a .yaml file so that each subdirectory can be run
        by a YOLO model.

        Input:
            - filepath: str = to the 'dataset_training' directory
        """

        # create yaml file
        dataset_path = filepath / 'dataset.yaml'

        # write to the file
        with open(file=dataset_path, mode='w', encoding='utf-8') as f:
            f.write('train: train\n')
            f.write('val: val\n')
            f.write(f'nc: {self.class_map_len}\n')
            f.write('names:\n')
            for key, val in self.class_map.items():
                f.write(f'  {key}: {val}\n')

    def create_video_sequence(self) -> None:
        """
        Create a video sequence from the 'runs/detect/predict2' folder to show the model's inference.
        This is hard coded to that filepath just to show inference.
        """

        # create video capture but from a sequence of images
        cap = cv2.VideoCapture('runs/detect/predict2/%06d.jpg')

        # check if it's opened correctly
        if not cap.isOpened():
            print('Error: could not open image sequence')
        else:
            print('Image sequence opened correctly!')

        # loop through the images
        while True:
            ret, frame = cap.read()

            if not ret:
                print('End of image sequence')
                break

            # show the image
            cv2.imshow('Image sequence', frame)

            # keep the image sequence going until q is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # release resources and destory all windows
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":

    model = PedestrianDetection()

    model.normalize_gt(filepath='MOT17Det/train')
    model.create_image_annotations(filepath='MOT17Det/train')
    model.create_training_folders(filepath='MOT17Det/train')
    model.create_video_sequence()

    # run trained model on MOT17-02
    # batch= -1 for 60% GPU utilization; using all my GPU slows down my computer for other things
    # mot17_02_model = YOLO('runs/detect/train3/weights/best.pt')
    # mot17_02_train_results = mot17_02_model.train(data=model.dataset_training_yaml_paths['MOT17-02'],
    #                                               epochs=5,
    #                                               imgsz=640,
    #                                               device='mps',
    #                                               batch=-1)

    # resume MOT17-02 training
    # mot17_02_resume_training = YOLO('runs/detect/train6/weights/last.pt')
    # mot17_02_resume_training_results = mot17_02_resume_training.train(resume=True)

    # run inference using the previously trainined model
    # mot17_02_prediction = YOLO('runs/detect/train6/weights/best.pt')
    # mot17_02_prediction_results = mot17_02_prediction.predict(source='MOT17Det/test/MOT17-01/img1',
    #                                                           conf=0.65,
    #                                                           save=True,
    #                                                           imgsz=640,
    #                                                           show=True)
