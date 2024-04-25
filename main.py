
import os
from models.apnn import APNN
from models.bdpn import BDPN
from models.dicnn import DICNN
from models.drpnn import DRPNN
from models.fusionnet import FusionNet
from models.msdcnn import MSDCNN
from models.pannet import PanNet
from models.pnn import PNN


import torch
import cv2 as cv
import h5py
import numpy as np

from dataloader import Dataset_h5py_fr, Dataset_h5py_rr

def generate_image_in(image_in, batch_n, model_name):
    count = batch_n * image_in.shape[0]
    for index,image in enumerate(image_in):
        print(image.shape, "image_in")
        print(image.max())
        string = f"out/in_images/image_in_{count + index}.png"
        cv.imwrite(string, image)

def generate_image_out (image_out,batch_n, model_name):
    count = batch_n * image_out.shape[0]
    for index,image in enumerate(image_out):
        print(image.shape, "image_out")
        print(image.max())
        path_out = f"out/{model_name}/image_out_{count + index}.png"
        cv.imwrite(path_out, image)

# Define the model and the wieghts an wether the model needs highpass filtering or not

models = [
    (APNN,"apnn.pth",False,"apnn"),
    (BDPN,"bdpn.pth",False,"bdpn"),
    (DICNN,"dicnn1.pth",False,"dicnn"),
    (DRPNN,"drpnn.pth",False,"drpnn"),
    (FusionNet,"fusionnet.pth",False,"fusionnet"),
    (MSDCNN,"msdcnn.pth",False,"msdcnn"),
    (PanNet,"panet.pth",True,"pannet"),
    (PNN,"pnn.pth",False,"pnn")
]

# Choose the model
model_index = 4
model, wieght_path, highpass, model_name = models[model_index] 


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load the data 
#data_path1 = os.path.join(".","data","h5py","qb","full_examples","test_qb_OrigScale_multiExm1.h5")
#data = Dataset_h5py_fr(data_path1, img_scale=2047.0, highpass=highpass)
data_path2 = os.path.join(".","data","h5py","qb","reduced_examples","test_qb_multiExm1.h5")
data = Dataset_h5py_rr(data_path2, img_scale=2047.0, highpass=highpass)
data_loader = torch.utils.data.DataLoader(data, batch_size=1, shuffle=False, num_workers=0, drop_last=False)

# Load the model and the weights
model = model(4).to(device) # 4 spectral bands + 1 panchromatic band added inside the model
path = os.path.join(".","weights","QB",wieght_path) 
model.load_state_dict(torch.load(path))
model.eval()
iter_data = iter(data_loader)

gt_data = []
out_data = []


with torch.no_grad(): 
    for batch_n,in_data in enumerate(data_loader):

        x_batch,gt_batch = in_data

        # lms = x[0]
        # image_in = lms.detach().cpu().numpy()[:,:3].transpose(0,2,3,1)*255
        # generate_image_in (image_in , batch_n, model_name)
        
        x_batch = [i.to(device) for i in x_batch]
        result = model(x_batch)
        out = result.detach().cpu().numpy() # get output from the model

        out_data.append(out*2047.0)
        gt_data.append(gt_batch.numpy()*2047.0)

        image_out = out[:,:3].transpose(0,2,3,1)*255 #get bgr image and transform to 0-255
        generate_image_out(image_out,batch_n,model_name)

with h5py.File("mytestfile.hdf5", "w") as f:
    dset = f.create_dataset("out_data", data=np.array(out_data))
    dset = f.create_dataset("gt_data", data=np.array(gt_data))