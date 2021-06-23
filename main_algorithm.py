# -*- coding: utf-8 -*-
"""Final.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/15X0T-JsEtwQO_dZgJudVg5l6AftxEhqz

Submitted by Md Mahabub Uz Zaman
"""

from google.colab import drive
drive.mount('/content/drive')

# Commented out IPython magic to ensure Python compatibility.
# %%shell
# 
# # Install pycocotools
# git clone https://github.com/cocodataset/cocoapi.git
# cd cocoapi/PythonAPI
# python setup.py build_ext install

import os
import numpy as np
import torch
import torch.utils.data
from PIL import Image
import numpy as np
import pandas as pd

class PCB_Dataset(object):
    
    def __init__(self, txt_file, root_dir , transform = None):
        
        self.txt_file = txt_file
        df = pd.read_csv(self.txt_file, header = None)
        df['img_dir'], df['box_dir'] = df[0].str.split(' ',1).str
        df = df.drop([0], axis = 1)
        
        self.df = df[0:100]
        self.root_dir = root_dir
        self.transform = transform
     
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()
        
        raw_path = os.path.join(self.root_dir, self.df.iloc[idx,0])
        img_path = raw_path[:-4]+str("_test.jpg")
        img = Image.open(img_path).convert('RGB')
        
        #test = Image.open(img_path)
        temp_path = raw_path[:-4]+str("_temp.jpg")
        temp = Image.open(temp_path).convert('RGB')
        masks = np.logical_xor(img, temp)
        #masks = np.invert(masks)
        masks = torch.as_tensor(masks, dtype=torch.uint8)
        
        
        #Boxes start here
        ann_path = os.path.join(self.root_dir, self.df.iloc[idx,1])
        ann = np.loadtxt(ann_path)
        temp2 = ann
        num_error = ann.shape[0]

        boxes = []
        labels = []
        for i in range(num_error):
          xmin = temp2[i,0]
          ymin = temp2[i,1]
          xmax = temp2[i,2]
          ymax = temp2[i,3]
          l = temp2[i,-1]
          boxes.append([xmin, ymin, xmax, ymax])
        
        labels = temp2[:,-1]
        for i in range(len(labels)):
          if labels[i] > 2:
            labels[i] = 3
        boxes = torch.as_tensor(boxes, dtype=torch.float32)
        labels = torch.as_tensor(labels, dtype=torch.int64)

        
        image_id = torch.tensor([idx])
        area = (boxes[:, 3] - boxes[:, 1]) * (boxes[:, 2] - boxes[:, 0])
        iscrowd = torch.zeros((num_error,), dtype=torch.int64)
        
        target = {}
        target["boxes"] = boxes
        target["labels"] = labels
        target["masks"] = masks
        target["image_id"] = image_id
        target["area"] = area
        target["iscrowd"] = iscrowd

        if self.transform is not None:
            img, target = self.transform(img, target)


        return img, target

dataset = PCB_Dataset('/content/trainval.txt', root_dir = '/content/drive/My Drive/Colab Notebooks/Data')
dataset_test = PCB_Dataset('/content/test.txt', root_dir = '/content/drive/My Drive/Colab Notebooks/Data')
dataset[0][0]
dataset_test[0][0]

import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor

      
def MaskRCNN_model(num_classes):
    '''
    # load an instance segmentation model pre-trained on COCO
    model = torchvision.models.detection.maskrcnn_resnet50_fpn(pretrained=True)

    # get the number of input features for the classifier
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    # replace the pre-trained head with a new one
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    # now get the number of input features for the mask classifier
    in_features_mask = model.roi_heads.mask_predictor.conv5_mask.in_channels
    hidden_layer = 256
    # and replace the mask predictor with a new one
    model.roi_heads.mask_predictor = MaskRCNNPredictor(in_features_mask,
                                                       hidden_layer,
                                                       num_classes)
    '''
    model = torchvision.models.detection.maskrcnn_resnet50_fpn(pretrained=True)
    return model

def fasterRCNN_model(num_classes):
    '''
    backbone = torchvision.models.mobilenet_v2(pretrained=True).features

    backbone.out_channels = 1280

    anchor_generator = AnchorGenerator(sizes=((32, 64, 128, 256, 512),),
                                      aspect_ratios=((0.5, 1.0, 2.0),))

    roi_pooler = torchvision.ops.MultiScaleRoIAlign(featmap_names=[0],output_size=7, sampling_ratio=2)
    
    model = FasterRCNN(backbone, num_classes,rpn_anchor_generator=anchor_generator,box_roi_pool=roi_pooler)
    '''
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
    '''
    >>> model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
    >>> model.eval()
    >>> x = [torch.rand(3, 300, 400), torch.rand(3, 500, 400)]
    >>> predictions = model(x)

    '''
    #model.fc = nn.Sequential(nn.Dropout(p=0.5))


    return model

# Commented out IPython magic to ensure Python compatibility.
# %%shell
# 
# # Download TorchVision repo to use some files from
# # references/detection
# git clone https://github.com/pytorch/vision.git
# cd vision
# git checkout v0.3.0
# 
# cp references/detection/utils.py ../
# cp references/detection/transforms.py ../
# cp references/detection/coco_eval.py ../
# cp references/detection/engine.py ../
# cp references/detection/coco_utils.py ../

from engine import train_one_epoch, evaluate
import utils
import transforms as T


def get_transform(train):
    transforms = []
    # converts the image, a PIL image, into a PyTorch Tensor
    transforms.append(T.ToTensor())
    if train:
        # during training, randomly flip the training images
        # and ground-truth for data augmentation
        transforms.append(T.RandomHorizontalFlip(0.5))
    return T.Compose(transforms)

# use our dataset and defined transformations
dataset = PCB_Dataset('/content/trainval.txt', root_dir = '/content/drive/My Drive/Colab Notebooks/Data', transform = get_transform(True))
dataset_test = PCB_Dataset('/content/trainval.txt', root_dir = '/content/drive/My Drive/Colab Notebooks/Data', transform = get_transform(False))

# split the dataset in train and test set
torch.manual_seed(1)
indices = torch.randperm(len(dataset)).tolist()
dataset = torch.utils.data.Subset(dataset, indices)

torch.manual_seed(1)
indices = torch.randperm(len(dataset)).tolist()
dataset_test = torch.utils.data.Subset(dataset_test, indices)

# define training and validation data loaders
data_loader = torch.utils.data.DataLoader(
    dataset, batch_size=2, shuffle=False, num_workers=4,
    collate_fn=utils.collate_fn)

data_loader_test = torch.utils.data.DataLoader(
    dataset_test, batch_size=4, shuffle=False, num_workers=4,
    collate_fn=utils.collate_fn)

torch.cuda.is_available()

device = torch.device('cuda') #if torch.cuda.is_available() else torch.device('cpu')

#device = torch.device('cpu')
# our dataset has four classes 
num_classes = 4

# get the model using our helper function
model = MaskRCNN_model(num_classes)
# move model to the right device
model.to(device)

ct = 0
for child in model.children():
  ct += 1
if ct < 5:
    for param in child.parameters():
        param.requires_grad = False



# construct an optimizer
params = [p for p in model.parameters() if p.requires_grad]
optimizer = torch.optim.SGD(params, lr=0.01,
                            momentum=0.9, weight_decay=0.0005)

# and a learning rate scheduler which decreases the learning rate by
# 10x every 3 epochs
lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer,
                                               step_size=1,
                                               gamma=0.001)

# let's train it for 2 epochs
num_epochs = 2

for epoch in range(num_epochs):
    # train for one epoch, printing every 10 iterations
    train_one_epoch(model, optimizer, data_loader, device, epoch, print_freq=10)
    # update the learning rate
    lr_scheduler.step()
    # evaluate on the test dataset
    evaluate(model, data_loader_test, device=device)

# pick one image from the test set
img, _ = dataset_test[10]
# put the model in evaluation mode
model.eval()
with torch.no_grad():
    prediction = model([img.to(device)])

prediction[0]['boxes'][0:10]

prediction[0]['labels'][0:10]

prediction[0]['scores'][0:10]

Image.fromarray(img.mul(255).permute(1, 2, 0).byte().numpy())

_ , target = dataset_test[10]
target