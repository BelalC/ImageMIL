from keras.applications.vgg16 import VGG16, preprocess_input
from keras.preprocessing import image
from keras.layers import Input
from keras.layers.pooling import GlobalAveragePooling2D, AveragePooling2D
from keras.models import Model

import joblib
import numpy as np
import util
from linear_classifier import LinearClassifier
from sil import SIL


### PARAMETERS ###
model_name = "vgg16"
layer = "block4_pool" # layer from which to generate feature map to pass to SVM
instance_size = None # instance size, default = None
instance_stride = None # instance stride, default = None
pool_size = 5 # mean pooling size, default = 5

#img_path = ("/home/paperspace/Data/break_his/BreaKHis_v1/histology_slides/"
#            "breast/benign/SOB/adenosis/SOB_B_A_14-22549AB/100X/SOB_B_A-14-22549AB-100-001.png")

pool_size = 5


def generate_feature_map(img_path):
    # load image file + pre-process
    img = image.load_img(img_path)

    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_preprocess = preprocess_input(img_array)

    print("img shape: {}".format(img_preprocess.shape))

    # create VGG16 model
    input_tensor = Input(shape=(None, None, 3))

    base_model = VGG16(input_tensor=input_tensor,
                       include_top=False,
                       weights='imagenet')

    # get chosen convolution block used to generate a feature map
    x = base_model.get_layer("block4_pool").output
    x = AveragePooling2D((pool_size, pool_size), name='avgpool')(x)

    # define prediction model
    model = Model(inputs=base_model.input, outputs=x)

    # generate feature map
    print("generating feature map...")

    p = model.predict(img_preprocess)

    print(p.shape)

    if len(p.shape) > 2:
        feat = [p[:, r, c, :].squeeze() for r in range(p.shape[1]) for c in range(p.shape[2])]
    else:
        feat = [p.squeeze()]

    if len(feat) > 0:
        print('size of resized feature map: %d x %d' % (len(feat), feat[0].shape[0]))

    return feat


def predict_svm(model_path, feat_map):

    model = joblib.load(model_path)
    p = model.predict(feat_map)

    return p


def execute(model_path, img_path):

    # generate feature map from VGG16
    feat_map = np.expand_dims(generate_feature_map(img_path), axis=0) # expand dimensions to pass 3-dimensional object to model.predict()

    # predict probability
    prediction = predict_svm(model_path = model_path, feat_map = feat_map)

    return np.argmax(prediction, axis=1)

if __name__ == '__main__':
    img_path = ("/home/paperspace/Data/break_his/BreaKHis_v1/histology_slides/"
            "breast/benign/SOB/adenosis/SOB_B_A_14-22549AB/100X/SOB_B_A-14-22549AB-100-001.png")
    model_path = "/home/paperspace/Data/break_his/BreaKHis200/model_median_Fold 1.joblib"
    x = execute(model_path, img_path)
    print(x)
