import Image
import numpy as np
import cv2
import math
import matplotlib.pyplot as plt
from scipy import ndimage, signal
from tqdm import *

RIGHT_IMAGE = 'view0.png'
LEFT_IMAGE = 'view1.png'

'''
flow :
- get Images 
- apply gaussian smoothening
- run mathcing and generate the disparityMap
- apply nearest neighbour and mean filter to depthMap
- run for multiple Views
'''

data_directories = ["Aloe"]
def mean2(x):
    y = np.sum(x) / np.size(x);
    return y

def corr2(a,b):
    a = a - mean2(a)
    b = b - mean2(b)
    r = (a*b).sum() / math.sqrt((a*a).sum() * (b*b).sum());
    return r

def load_image( infilename ) :
	rgbimg = cv2.imread(infilename,0)
	data = np.asarray(rgbimg, dtype='double')
	return data

def save_image( npdata, outfilename ) :
	img = Image.fromarray( np.asarray( np.clip(npdata,0,255), dtype="uint8"), "L" )
	img.save( outfilename )

def preProcessImage(image,type,filterParam):
	if(type=='gaussian'):
		filteredImage = ndimage.filters.gaussian_filter(image,sigma=filterParam)
		return filteredImage

def postProcessDepth(depthMap, edgeRight, height, width,type, iters):
	filteredDepth = np.array(depthMap,copy=True)
	for k in range(1,iters):
		for i in range(height+1,height-1):
			for j in range(width+1,width-1):
				if(edgeRight[i][j] == 0):
					filteredDepth[i][j] = (depthMap[i][j+1] + depthMap[i][j-1] + depthMap[i+1][j] + depthMap[i-1][j])/4
		depthMap = filteredDepth
	return filteredDepth


def getDepthMap(rightImage,leftImage, edgeRight, edgeLeft, corrWindowSize , minOffset, maxOffset, matchType ):
	height,width = rightImage.shape[0],leftImage.shape[1]
	disparityMap = np.zeros((height,width))
	disparityMask = np.zeros((height,width))
	windowSize = (corrWindowSize-1)/2
	for i in tqdm(range(windowSize, height - windowSize)):
	# for i in tqdm(range(windowSize, windowSize+1)):
		for j in range(windowSize,width - windowSize):
			if(edgeRight[i][j]):
				patchSumRight = np.sum(rightImage[i-windowSize:i+windowSize][j-windowSize:j+windowSize] * rightImage[i-windowSize:i+windowSize][j-windowSize:j+windowSize])**(0.5)
				patchSumLeft = np.sum(leftImage[i-windowSize:i+windowSize][j-windowSize:j+windowSize] * leftImage[i-windowSize:i+windowSize][j-windowSize:j+windowSize])**(0.5)
				patchValLeft = np.array(rightImage[i-windowSize:i+windowSize][j-windowSize:j+windowSize] / patchSumLeft,copy=True)
				patchValRight = np.array(leftImage[i-windowSize:i+windowSize][j-windowSize:j+windowSize] / patchSumRight,copy=True)
				# print rightImage[i-windowSize:i+windowSize][j-windowSize:j+windowSize].shape
				# print leftImage[i-windowSize:i+windowSize][j-windowSize:j+windowSize].shape
				print j 
				print i
				print windowSize
				maxCorr = corr2(patchValRight,patchValLeft)
				for k in range(j,width-windowSize-1):
					newPatchValLeft = leftImage[i-windowSize:i+windowSize][k-windowSize:k+windowSize] / np.sum(leftImage[i-windowSize:i+windowSize][k-windowSize:k+windowSize] * leftImage[i-windowSize:i+windowSize][k-windowSize:k+windowSize])**(0.5)
					Corr = corr2(patchValRight,newPatchValLeft)
					if(maxCorr < Corr):
						maxCorr = Corr
						disparityMap[i][j] = k-j

				disparityMask[i][j]	= 1
				if(maxCorr < 0.7 or disparityMap[i][j] > maxOffset):
					disparityMap[i][j] = 0
					# edgeRight[i][j] = 0
					disparityMask[i][j] = 0
			else:
				disparityMask[i][j]	= 0
	return disparityMap,disparityMask

if __name__ == "__main__":
	rightImage = load_image(RIGHT_IMAGE)
	leftImage = load_image(LEFT_IMAGE)
	
	height,width = rightImage.shape[0],leftImage.shape[1]

	filteredRightImage = preProcessImage(rightImage,'gaussian',1)
	filteredLeftImage = preProcessImage(rightImage,'gaussian',1)
	
	edgeRight = cv2.Canny(rightImage.astype(dtype=np.uint8),100,200)
	edgeLeft = cv2.Canny(leftImage.astype(dtype=np.uint8),100,200)

	

	depthMap, depthMask = getDepthMap(filteredRightImage,filteredLeftImage,edgeLeft,edgeRight,19,0,16,'SSD')
	
	imgplot = plt.imshow(depthMap)
	plt.show()

	filteredDepth = postProcessDepth(depthMap, height, width, edgeRight, 1, 2000)
	imageDepth  = filteredDepth.astype(np.uint8)
	imgplot = plt.imshow(depthMap,cmap="hot")
	plt.show()