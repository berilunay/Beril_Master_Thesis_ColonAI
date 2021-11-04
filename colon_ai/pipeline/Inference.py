import os
import torch
import numpy as np
from pathlib import Path

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from cv2 import imshow
from matplotlib import pyplot as plt
from numpy import shape
from torchvision.datasets import VisionDataset
import cv2
from torch.utils.data import DataLoader

from colon_ai.pipeline.DatasetLocation_Inference import InferenceDatasetLocation
from colon_ai.train_location.DataModelLocation import ColonDataModelLocation
from colon_ai.traınıng.DataModelColon import ColonDataModel


class InferenceDatasetQuality(VisionDataset):
    def __init__(self, root, transform=None, target_transform=None, num_samples=None):
        super(InferenceDatasetQuality, self).__init__(root, transform=transform, target_transform=target_transform)
        self.video_dirs = []
        self.video_dirs.append(self.root)
        self.sample_dirs = []  # image0,image1 ...
        for video_dir in self.video_dirs:
            self.sample_dirs += (sorted(Path(video_dir).iterdir())) # gets image and labels(folder)
        if num_samples:
            self.sample_dirs = self.sample_dirs[:num_samples]



    def __getitem__(self, index):
        sample_dir = self.sample_dirs[index]
        colon= self._load_and_transform_colon(sample_dir)
        return colon


    def _load_and_transform_colon(self, sample_dir):
        colon = self._load_colon(sample_dir)
        colon = self._apply_transforms(colon)

        return colon


    def _load_colon(self, sample_dir):

        im_path = str(sample_dir / "colon.png")
        colon=cv2.imread(im_path)
        resized_image = cv2.resize(colon, (224, 224),interpolation=cv2.INTER_NEAREST)
        img_new=cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
        colon = np.array(img_new)
        colon=np.moveaxis(colon,-1,0)
        colon = torch.from_numpy(colon)
        colon= colon/255.0

        return colon


    def _apply_transforms(self, colon):
        if self.transform is not None:
            colon = self.transform(colon)

        return colon


    def __len__(self):
        return len(self.sample_dirs)

#print the average quality for every 10 frames and visualize it with grid
def show_ouput_quality(model, dataloader, class_dict=None):
    quality_labels=[]
    dict_map = {'G':4,'M':3,'B':2,'p':1}
    for features in dataloader:
        with torch.no_grad():
            features = features
            logits = model(features)
            predictions = torch.argmax(logits,dim=1)
            pred_numpy=predictions.numpy()
            quality_labels.append(pred_numpy)
        break

    #coversion
    converted_arr=[] #output labels coming from model
    count=0
    result=""
    output=[] #avg of the each 10 elements
    output_label=[] #corresponding average quality label
    calc=0
    index=0

    for num in quality_labels[0]:
        converted_arr.append(class_dict[num])
    print("converted array: ",converted_arr)
    print("len converted array: ",len(converted_arr))

    #calculation
    #1 sec has 25 frames, to print avg every 10 sec count must be 250
    for i in range(len(converted_arr)):
        calc=calc+dict_map[converted_arr[i]]
        count+=1
        index+=1
        if count==250:
            avg = calc /250
            if avg < 1.5:
                result = "poor"
            elif avg >= 1.5 and avg < 2.5:
                result = "bad"
            elif avg >= 2.5 and avg < 3.5:
                result = "middle"
            else:
                result = "good"
            output.append(avg)
            output_label.append(result)
            print("average quality "+"between frames "+str(index-250)+"-"+str(index)+ " is:",result)
            count=0
            calc=0

    #checking the avg quality labels for 10 frame
    print("output_label_avg: ", output_label)
    print("output_label_avg length: ", len(output_label))


    #adding the last remaining elements
    sum_elem=0
    remained_elem= len(converted_arr)%250
    if remained_elem!=0:
        for k in range(remained_elem):
            sum_elem = sum_elem + dict_map[converted_arr[k-remained_elem]]
        avg_add=sum_elem/remained_elem
        if avg_add< 1.5:
            result = "poor"
        elif avg_add >= 1.5 and avg < 2.5:
            result = "bad"
        elif avg_add>= 2.5 and avg < 3.5:
            result = "middle"
        else:
            result = "good"
        output.append(avg_add)
        output_label.append(result)
        print("average quality " + "between frames " + str(len(converted_arr)-remained_elem) + "-" + str(len(converted_arr)) + " is:", result)
        print("avg output: ",output)
        print("avg output label: ", output_label)


    fig, axes = plt.subplots(nrows=4, ncols=5,
                             sharex=True, sharey=True)

    nhwc_img = np.transpose(features, axes=(0, 2, 3, 1))

    if nhwc_img.shape[-1] == 1:
        nhw_img = np.squeeze(nhwc_img.numpy(), axis=3)

        for idx, ax in enumerate(axes.ravel()):
            ax.imshow(nhw_img[idx], cmap='binary')
            if class_dict is not None:
                ax.title.set_text(f'P: {class_dict[predictions[idx].item()]}')
            else:
                ax.title.set_text(f'P: {predictions[idx]}')
            ax.axison = False
    else:

        for idx, ax in enumerate(axes.ravel()):
            ax.imshow(nhwc_img[idx])
            if class_dict is not None:
                ax.title.set_text(f'P: {class_dict[predictions[idx].item()]}')
            ax.axison = False
    plt.tight_layout()
    plt.show()

    return converted_arr,output_label

#returns the predicted location labels and visualizes the image with predicted labels
def show_ouput_location(model, dataloader, class_dict=None):
    location_labels=[]
    location_dict = {'R':0, 'M':1, 'L':2}
    for features in dataloader:
        with torch.no_grad():
            features = features
            logits = model(features)
            predictions = torch.argmax(logits,dim=1)
            pred_numpy=predictions.numpy()
            location_labels.append(pred_numpy)
        break

    #coversion
    converted_arr=[]

    for num in location_labels[0]:
        converted_arr.append(class_dict[num])
    print("converted array location: ",converted_arr)
    print("len converted array location: ",len(converted_arr))


    fig, axes = plt.subplots(nrows=4, ncols=5,
                             sharex=True, sharey=True)

    nhwc_img = np.transpose(features, axes=(0, 2, 3, 1))

    if nhwc_img.shape[-1] == 1:
        nhw_img = np.squeeze(nhwc_img.numpy(), axis=3)

        for idx, ax in enumerate(axes.ravel()):
            ax.imshow(nhw_img[idx], cmap='binary')
            if class_dict is not None:
                ax.title.set_text(f'P: {class_dict[predictions[idx].item()]}')
            else:
                ax.title.set_text(f'P: {predictions[idx]}')
            ax.axison = False
    else:

        for idx, ax in enumerate(axes.ravel()):
            ax.imshow(nhwc_img[idx])
            if class_dict is not None:
                ax.title.set_text(f'P: {class_dict[predictions[idx].item()]}')
            ax.axison = False
    plt.tight_layout()
    plt.show()
    return converted_arr

#puts predicted location text onto corresponding scope image and saves it
def show_images_with_labels(dataloader,output_array):
    print(".....Location frame preprocesing started.........")
    save_path="/home/beril/Thesis_Beril/Inference/Frames_Loc/Video6"
    index=0
    font_path = "/home/beril/Thesis_Beril/Inference/Font/Swansea-q3pd.ttf"
    font_chs = ImageFont.truetype(font_path, 20)
    for images in dataloader:
        input_img = images
        c, t, h, w = input_img.shape
        input_img = torch.permute(input_img,(0, 2, 3, 1))
        input_img_np=input_img.numpy()

    for i in range(len(input_img)):
        img=input_img_np[i]
        im = Image.fromarray((img*255).astype('uint8'), 'RGB')
        label=output_array[i]
        I1 = ImageDraw.Draw(im)
        I1.text((28, 37), "Location:"+str(label), fill=(150, 48, 27),font=font_chs)
        # plt.imshow(im)
        # plt.show()
        file_path = os.path.join(save_path, "Image" + f'{index:05d}' + ".png")
        im.save(file_path)
        index=index+1

#puts predicted quality text onto corresponding colon image and saves it
def show_images_with_labels_quality(dataloader,output_array):
    print(".....Quality frame preprocesing started.........")
    save_path="/home/beril/Thesis_Beril/Inference/Frames_Quality/Video6"
    index=0
    font_path="/home/beril/Thesis_Beril/Inference/Font/Swansea-q3pd.ttf"
    font_chs = ImageFont.truetype(font_path, 20)
    for images in dataloader:
        input_img = images
        c, t, h, w = input_img.shape
        input_img = torch.permute(input_img,(0, 2, 3, 1))
        input_img_np=input_img.numpy()


    for i in range(len(input_img)):
        img=input_img_np[i]
        im = Image.fromarray((img*255).astype('uint8'), 'RGB')
        label=output_array[i]
        I1 = ImageDraw.Draw(im)
        I1.text((28, 37), "Quality:"+str(label), fill=(9, 28, 173),font=font_chs)
        # plt.imshow(im)
        # plt.show()
        file_path = os.path.join(save_path, "Image" + f'{index:05d}' + ".png")
        im.save(file_path)
        index=index+1

#concats scope and colon view into one image
def concat_images():
    print("............Concat Location and Quality Started............")
    main_path="/home/beril/Thesis_Beril/Inference/Frames_Loc/Video6"
    copy_path = "/home/beril/Thesis_Beril/Inference/Frames_Concat/Video6"

    count=0
    for file_name in sorted(os.listdir(main_path)):
        im1_path = '/home/beril/Thesis_Beril/Inference/AVG_Quality_Concat/Video6/'+str(file_name)
        img1 = Image.open(im1_path)
        im2_path='/home/beril/Thesis_Beril/Inference/Frames_Loc/Video6/' + str(file_name)
        img2 = Image.open(im2_path)
        print(im2_path)
        new_img = Image.new('RGB', (img1.width + img2.width, img1.height))
        new_img.paste(img1, (0, 0))
        new_img.paste(img2, (img1.width, 0))
        file_path = os.path.join(copy_path, "Image_Concat" + f'{count:05d}' + ".png")
        new_img.save(file_path)
        count = count+ 1

def concat_quality_and_avg_quality(avg_quality_out_arr):
    #concataned img size with avg_quality is(448,274)
    print(".........concataneting quality frames................")
    quality_frame_path="/home/beril/Thesis_Beril/Inference/Frames_Quality/Video6"
    save_concat_path="/home/beril/Thesis_Beril/Inference/AVG_Quality_Concat/Video6"
    count=0
    length_array=0
    font_path = "/home/beril/Thesis_Beril/Inference/Font/Swansea-q3pd.ttf"
    font_chs = ImageFont.truetype(font_path, 18)

    for file_name in sorted(os.listdir(quality_frame_path)):
        im1_path = '/home/beril/Thesis_Beril/Inference/Frames_Quality/Video6/' + str(file_name)
        img1 = Image.open(im1_path)
        img2 = Image.new('RGB', (img1.width, 50), color=(172, 184, 191))
        new_img1 = Image.new('RGB', (img1.width, img1.height + img2.height))
        new_img1.paste(img1, (0, 0))
        new_img1.paste(img2, (0, img1.height))

        if(count!=0 and count%250==0):
            I1 = ImageDraw.Draw(img2)
            I1.text((13, 20), "Average quality is: " + str(avg_quality_out_arr[length_array]), fill=(25, 25, 26),font=font_chs)
            # plt.imshow(img2)
            # plt.show()
            new_img = Image.new('RGB', (img1.width, img1.height + img2.height))
            new_img.paste(img1, (0, 0))
            new_img.paste(img2, (0, img1.height))
            file_path = os.path.join(save_concat_path, "Image" + f'{count:05d}' + ".png")
            new_img.save(file_path)
            length_array=length_array+1
        else:
            if(count>250):
                I2 = ImageDraw.Draw(img2)
                I2.text((13, 20), "Average quality is: " + str(avg_quality_out_arr[length_array-1]), fill=(25, 25, 26),font=font_chs)
                new_img2 = Image.new('RGB', (img1.width, img1.height + img2.height))
                new_img2.paste(img1, (0, 0))
                new_img2.paste(img2, (0, img1.height))
                file_path = os.path.join(save_concat_path, "Image" + f'{count:05d}' + ".png")
                new_img2.save(file_path)
            else:
                file_path_org = os.path.join(save_concat_path, "Image" + f'{count:05d}' + ".png")
                new_img1.save(file_path_org)

        count = count + 1


#creates video from image frames
def image_to_video():
    print("converting to video...")
    image_folder = "/home/beril/Thesis_Beril/Inference/Frames_Concat/Video6"
    video_name = "/home/beril/Thesis_Beril/Inference/Video_output/video6_outlast_25fps.mp4"

    images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')

    video = cv2.VideoWriter(video_name, fourcc, 25, (width, height))


    for image in sorted(images):
        video.write(cv2.imread(os.path.join(image_folder, image)))

    cv2.destroyAllWindows()
    video.release()

 # checkpoint_model_path="/home/beril/BerilCodes/ColonAI_LocationDetection/colon_ai/traınıng/uncategorized/best_model/checkpoints/run4-epoch=149-val_loss=0.74-val_acc=0.80.ckpt"
 # checkpoint_model_path_loc="/home/beril/BerilCodes/ColonAI_LocationDetection/colon_ai/train_location/uncategorized/best_model_loc/checkpoints/run1--epoch=99-val_loss=0.14-val_acc=0.96.ckpt"
if __name__ == '__main__':
    # print("Code is running...")
    # Test_Path="/home/beril/Thesis_Beril/Dataset_preprocess_new/Train_Location_Labels/Video6"
    # quality_dict = {0: 'G', 1: 'M', 2: 'p', 3: 'B'}
    # quality_dataset = InferenceDatasetQuality(root=Test_Path)
    # quality_loader = DataLoader(quality_dataset, batch_size=len(quality_dataset))
    # checkpoint_model_path = "/home/beril/BerilCodes/ColonAI_LocationDetection/colon_ai/traınıng/uncategorized/bestnew(96acc)/checkpoints/best1--epoch=32-val_loss=0.13-val_acc=0.96--train_loss=0.02-train_acc=1.00.ckpt"
    # pretrained_model = ColonDataModel.load_from_checkpoint(checkpoint_path= checkpoint_model_path)
    # pretrained_model.eval()
    # pretrained_model.freeze()
    # output_arr_quality,output_avg_qua_label=show_ouput_quality(pretrained_model, quality_loader, quality_dict)
    # show_images_with_labels_quality(quality_loader,output_arr_quality)
    # concat_quality_and_avg_quality(output_avg_qua_label)


    #test location
    # location_dataset = InferenceDatasetLocation(root=Test_Path)
    # location_loader = DataLoader(location_dataset, batch_size=len(location_dataset))
    # location_dict = {0: 'R', 1: 'M', 2: 'L'}
    # checkpoint_model_path_loc="/home/beril/BerilCodes/ColonAI_LocationDetection/colon_ai/uncategorized/run1_loc2d_bestmodel/checkpoints/run1--epoch=22-val_loss=0.03-val_acc=0.99.ckpt"
    # pretrained_model_loc = ColonDataModelLocation.load_from_checkpoint(checkpoint_path=checkpoint_model_path_loc)
    # pretrained_model_loc.eval()
    # pretrained_model_loc.freeze()
    # conv_arr_loc=show_ouput_location(pretrained_model_loc, location_loader, location_dict)
    # show_images_with_labels(location_loader,conv_arr_loc)


    #test_output_video
    #concat_images()
    #image_to_video()
    #img1 = Image.open("/home/beril/Thesis_Beril/Inference/Frames_Concat/Video6_temp/Image_Concat00010.png")









