import cv2
import FileManager
import numpy as np
import Initial_pose_estimator as ipe
import ActiveShapeModel as asm

def showControls():
    popup = np.ones((220,355), np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(popup,'Move mouse: Change tooth position',(10,25), font, 0.5,(240,255,255),1,cv2.LINE_AA)
    cv2.putText(popup,'Double click: Place or grab tooth',(10,40), font, 0.5,(240,255,255),1,cv2.LINE_AA)
    cv2.putText(popup,'Left+Right arrows: Change tooth gap',(10,70), font, 0.5,(240,255,255),1,cv2.LINE_AA)
    cv2.putText(popup,'Top+Down arrows: Change tooth size',(10,85), font, 0.5,(240,255,255),1,cv2.LINE_AA)
    cv2.putText(popup,'Pageup/down: Bottom/top tooth distance',(10,55), font, 0.5,(240,255,255),1,cv2.LINE_AA)
    cv2.putText(popup,'" / ": Save current position to file',(10,100), font, 0.5,(240,255,255),1,cv2.LINE_AA)
    cv2.putText(popup,'" . ": Activate automatic initialisation',(10,115), font, 0.5,(240,255,255),1,cv2.LINE_AA)
    cv2.putText(popup,'" \' ": Do segmentation',(10,130), font, 0.5,(240,255,255),1,cv2.LINE_AA)
    cv2.putText(popup,'" , ": Change to next radiograph',(10,145), font, 0.5,(240,255,255),1,cv2.LINE_AA)
    cv2.putText(popup,'" m ": Reset model',(10,160), font, 0.5,(240,255,255),1,cv2.LINE_AA)
    cv2.putText(popup,'" esc ": Close program',(10,175), font, 0.5,(240,255,255),1,cv2.LINE_AA)
    cv2.putText(popup,'" k ": Show/hide this popup',(10,190), font, 0.5,(240,255,255),1,cv2.LINE_AA)
    cv2.putText(popup,'" o ": ASM iteration',(10,205), font, 0.5,(240,255,255),1,cv2.LINE_AA)
    saved = cv2.namedWindow( "Controls", cv2.WINDOW_AUTOSIZE )
    cv2.imshow("Controls",popup)


output = np.empty((1, 8, 40, 2),dtype=np.uint16)
currentImage = 1
img = cv2.imread("_Data/Radiographs/%02d.tif" % currentImage)
height, width, channels = img.shape
scale = 0.3
size = (int(width*scale),int(height*scale))
resized_image = cv2.resize(img, size) 
showControls()

cv2.namedWindow( "Radiograph", cv2.WINDOW_AUTOSIZE )
cv2.imshow("Radiograph",resized_image)

pasted = 0
tooth_size = (0.212*size[0],0.36*size[1]) # (Width, Height)
image_center = (size[0]/2,size[1]/2) # (X,Y)
top_bottom_separation = 0.16*size[1] # space between top and bottom incisors
tooth_gap = 0.035*size[0] # space between teeth on same row
all_landmarks_std = np.empty((1, 8, 40, 2))

def resetModel():
    global tooth_size
    global image_center
    global top_bottom_separation
    global tooth_gap
    tooth_size = (0.212*size[0],0.36*size[1]) # (Width, Height)
    image_center = (size[0]/2,size[1]/2) # (X,Y)
    top_bottom_separation = 0.16*size[1] # space between top and bottom incisors
    tooth_gap = 0.035*size[0] # space between teeth on same row

def changeImage():
    global img
    global height, width, channels
    global scale
    global size
    global resized_image
    global currentImage
    currentImage +=1
    if(currentImage>14):
        currentImage = 1
    img = cv2.imread("_Data/Radiographs/%02d.tif" % currentImage)
    height, width, channels = img.shape
    scale = 0.3
    size = (int(width*scale),int(height*scale))
    resized_image = cv2.resize(img, size) 
    cv2.namedWindow( "Radiograph", cv2.WINDOW_AUTOSIZE )
    cv2.imshow("Radiograph",resized_image)

def showImages(image,model):
    cv2.namedWindow( "Radiograph", cv2.WINDOW_AUTOSIZE )
    cv2.imshow("Radiograph",image)
    pasted = 0
    cv2.setMouseCallback('Radiograph',mousePosition,(resized_image,model))
    cv2.waitKey(0)

def reloadImage(image):
    cv2.imshow("Radiograph",image)

def mousePosition(event,x,y,flags,param):
    global pasted
    if pasted==True:
        if event == cv2.EVENT_LBUTTONDBLCLK:
            reloadImage(param[0])
            pasted=False
            return

    if pasted==False:
        reloadImage(param[0])
        image = param[0].copy()
        if event == cv2.EVENT_MOUSEMOVE:
            # print (x,y)
            # cv2.circle(image,(x,y),40,(255,0,0))
            cropy = param[0].shape[0] - y
            cropx = param[0].shape[1] - x
            image[y:y+param[1].shape[0],x:x+param[1].shape[1]] = param[1][0:cropy,0:cropx]
            cv2.imshow('Radiograph',image)
            # param = (x,y)

        if event == cv2.EVENT_LBUTTONDBLCLK:
            print(x,y)
            print("Placing model")
            # cv2.circle(param[0],(x,y),40,(255,0,0))
            cropy = param[0].shape[0] - y
            cropx = param[0].shape[1] - x
            image[y:y+param[1].shape[0],x:x+param[1].shape[1]] = param[1][0:cropy,0:cropx]
            cv2.imshow('Radiograph',image)
            pasted=True

def moveTeeth(event,x,y,flags,param):
    global pasted
    global tooth_size
    global image_center
    global top_bottom_separation
    global tooth_gap
    landmarks = param[1]
    backdrop = param[0]

    if pasted==True:
        if event == cv2.EVENT_LBUTTONDBLCLK:
            reloadImage(backdrop)
            pasted=False
            return

    if pasted==False:
        reloadImage(backdrop)
        image = backdrop.copy()
        if event == cv2.EVENT_MOUSEMOVE:
            # print (x,y)
            # cv2.circle(image,(x,y),40,(255,0,0))
            drawTeeth(landmarks, image, tooth_size, (x,y), tooth_gap, top_bottom_separation)
            image_center = (x,y)
            # param = (x,y)

        if event == cv2.EVENT_LBUTTONDBLCLK:
            image = backdrop.copy()
            drawTeeth(landmarks, image, tooth_size, (x,y), tooth_gap, top_bottom_separation)
            pasted=True
def drawTeethOutput(model,backdrop):
    for j in range(0,4):
        for i in range(0,40):
            cv2.circle(backdrop, (model[0][j][i][0],model[0][j][i][1]),1,(255,255,255),-1)
    for j in range(4,8):
        for i in range(0,40):
            cv2.circle(backdrop, (model[0][j][i][0],model[0][j][i][1]),1,(255,255,255),-1)
    cv2.imshow("Radiograph",backdrop)


def drawTeeth(landmarks,backdrop,tooth_size,image_center,tooth_gap,top_bottom_separation):
    for j in range(0,4):
            for i in range(0,40):
                    x = int(landmarks[0][j][i][0]*tooth_size[0]+image_center[0]+tooth_gap*j)
                    output[0][j][i][0] = x
                    y = int(landmarks[0][j][i][1]*tooth_size[1]+image_center[1])
                    output[0][j][i][1] = y
                    # print(x)
                    # print(y)
                    cv2.circle(backdrop,(x,y),1,(255,255,255),-1)
    bottom_tooth_size = (tooth_size[0]*0.843,tooth_size[1])
    bottom_tooth_gap = tooth_gap*0.789
    side_fix = tooth_gap*(1-0.789)*3
    for j in range(4,8):
        for i in range(0,40):
                x = int(side_fix/2+landmarks[0][j][i][0]*bottom_tooth_size[0]+image_center[0]+bottom_tooth_gap*(j-4))
                output[0][j][i][0] = x
                y = int(landmarks[0][j][i][1]*bottom_tooth_size[1]+image_center[1]+top_bottom_separation)
                output[0][j][i][1] = y
                # print(x)
                # print(y)
                cv2.circle(backdrop,(x,y),1,(255,255,255),-1)
    cv2.imshow("Radiograph",backdrop)

def tempShow(text="Hello World"):
    popup = np.ones((50,330), np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(popup,text,(10,25), font, 0.5,(240,255,255),1,cv2.LINE_AA)
    saved = cv2.namedWindow( "Saved", cv2.WINDOW_AUTOSIZE )
    cv2.imshow("Saved",popup)
    cv2.waitKey(2500)
    cv2.destroyWindow("Saved")

def InitializeASM(directory = "_Data\\Radiographs\\*.tif"):
    dir_radiographs = directory
    radiographs = FileManager.load_files(dir_radiographs)
    global all_landmarks_std
    all_landmarks = FileManager.load_landmarks()
    all_landmarks_std = FileManager.total_procrustes_analysis(all_landmarks)
    test = np.mean(all_landmarks_std,axis=0)
    test = test.reshape(1,8,40,2)
    all_landmarks_std = test

    global pasted
    global tooth_size
    global image_center
    global top_bottom_separation
    global tooth_gap
    global size
    global scale
    global output
    global currentImage
    
    contourEnabled = False
    matchingEnabled = True

    alpha = 1.0 
    distance = 3 
    showpopup=1
    cv2.setMouseCallback('Radiograph',moveTeeth,(resized_image,all_landmarks_std))

    tempShow("Calculating Edges + PCA...")
    global img
    grays = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
    edge_img, pca_teeth = asm.preperation_all(grays, all_landmarks_std)
    edge_img = cv2.resize(edge_img.astype(np.uint8),size)
    tempShow("Calculating Edges + PCA : DONE!")
    
    
    loop=1
    while loop and cv2.getWindowProperty("Radiograph",0) >=0:
        backdrop = resized_image.copy()
        k = cv2.waitKeyEx(10)
        if k == 27:
            loop=0
        elif k == 2424832:
            tooth_gap-=5
            drawTeeth(all_landmarks_std,backdrop,tooth_size,image_center,tooth_gap,top_bottom_separation)
            cv2.setMouseCallback('Radiograph',moveTeeth,(resized_image,all_landmarks_std))
        elif k == 2555904:
            tooth_gap+=5
            drawTeeth(all_landmarks_std,backdrop,tooth_size,image_center,tooth_gap,top_bottom_separation)
            cv2.setMouseCallback('Radiograph',moveTeeth,(resized_image,all_landmarks_std))
        elif k == 2490368:
            tooth_size = (tooth_size[0]+10,tooth_size[1]+5)
            drawTeeth(all_landmarks_std,backdrop,tooth_size,image_center,tooth_gap,top_bottom_separation)
            cv2.setMouseCallback('Radiograph',moveTeeth,(resized_image,all_landmarks_std))
        elif k == 2621440:
            tooth_size = (tooth_size[0]-10,tooth_size[1]-5)
            drawTeeth(all_landmarks_std,backdrop,tooth_size,image_center,tooth_gap,top_bottom_separation)
            cv2.setMouseCallback('Radiograph',moveTeeth,(resized_image,all_landmarks_std))
        elif k == 2162688:
            top_bottom_separation += 5
            drawTeeth(all_landmarks_std,backdrop,tooth_size,image_center,tooth_gap,top_bottom_separation)
            cv2.setMouseCallback('Radiograph',moveTeeth,(resized_image,all_landmarks_std))
        elif k == 2228224:
            top_bottom_separation -= 5
            drawTeeth(all_landmarks_std,backdrop,tooth_size,image_center,tooth_gap,top_bottom_separation)
            cv2.setMouseCallback('Radiograph',moveTeeth,(resized_image,all_landmarks_std,tooth_size,image_center,tooth_gap,top_bottom_separation))
        elif k == 46:
            grays = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
            gaps,gap_size, new_img = ipe.gap_splits(grays, 20, size[1]/2+size[1]/30, 400)
            # cv2.namedWindow("fuck", cv2.WINDOW_AUTOSIZE)
            # cv2.imshow("fuck",new_img)
            # print(gaps[int(len(gaps)/2)])
            image_center = (size[0]/2-42,gaps[int(len(gaps)/2)]-40) # fixed values, needs changing
            pasted = 1
            drawTeeth(all_landmarks_std, backdrop, tooth_size, image_center, tooth_gap, top_bottom_separation)
            cv2.setMouseCallback('Radiograph',moveTeeth,(resized_image,all_landmarks_std,tooth_size,image_center,tooth_gap,top_bottom_separation))
        elif k == 44:
            changeImage()
            # resetModel() 
            cv2.setMouseCallback('Radiograph',moveTeeth,(resized_image,all_landmarks_std,tooth_size,image_center,tooth_gap,top_bottom_separation))
            backdrop = resized_image.copy()
            drawTeeth(all_landmarks_std, backdrop, tooth_size, image_center, tooth_gap, top_bottom_separation)
        elif k == 107:
            if showpopup == 1:
                showpopup = 0
                cv2.destroyWindow("Controls")
            else:
                showpopup = 1
                showControls()
        elif k == 109:
            resetModel()
            drawTeeth(all_landmarks_std, backdrop, tooth_size, image_center, tooth_gap, top_bottom_separation)
            cv2.setMouseCallback('Radiograph',moveTeeth,(resized_image,all_landmarks_std,tooth_size,image_center,tooth_gap,top_bottom_separation))
        elif k == 39:
            grays = cv2.cvtColor(backdrop, cv2.COLOR_BGR2GRAY)
            # print(all_landmarks_std.shape)
            # print(output[0,0,:,:])
            mask = np.zeros(grays.shape, np.uint8)
            for i in range(0,8):
                test = output[0,i,:,:].astype(np.int32)
                # print(test)
                # mask2 = np.zeros(backdrop.shape, np.uint8)
                # poly = np.array([ [50,50], [50,70], [70,70], [70,50] ], np.int32)
                cv2.fillConvexPoly(mask, test,(255,255,255))
                # cv2.fillConvexPoly(mask2, test,(255,255,255))
                # cv2.imshow("Radiograph",mask)
                
                
                # cv2.addWeighted(mask2, 1, backdrop, 1, 0, backdrop)
                # drawTeeth(all_landmarks_std, backdrop, tooth_size, image_center, tooth_gap, top_bottom_separation)
                # cv2.setMouseCallback('Radiograph',moveTeeth,(resized_image,all_landmarks_std,tooth_size,image_center,tooth_gap,top_bottom_separation))
            segmentation = cv2.bitwise_and(grays, grays, mask=mask)
            cv2.namedWindow("Segmentation",cv2.WINDOW_AUTOSIZE)
            cv2.imshow("Segmentation", segmentation)
        elif k == 92:
            grays = cv2.cvtColor(backdrop, cv2.COLOR_BGR2GRAY)
            mask = np.zeros(grays.shape, np.uint8)
            for i in range(0,8):
                test = output[0,i,:,:].astype(np.int32)
                cv2.fillConvexPoly(mask, test,(255,255,255))
            segmentation = cv2.bitwise_and(grays, grays, mask=mask)
            cv2.namedWindow("Segmentation",cv2.WINDOW_AUTOSIZE)
            cv2.imshow("Segmentation", mask)
        elif k == 93:
            grays = cv2.cvtColor(backdrop, cv2.COLOR_BGR2GRAY)
            mask = np.zeros(grays.shape, np.uint8)
            test = output[0,0,:,:].astype(np.int32)
            cv2.fillConvexPoly(mask, test,(255,255,255))
            segmentation = cv2.bitwise_and(grays, grays, mask=mask)
            mask = cv2.resize(mask, (int(size[0]/2),int(size[1]/2)))
            retval, mask = cv2.threshold(mask, 5, 255, cv2.THRESH_BINARY)
            cv2.namedWindow("Segmentation",cv2.WINDOW_AUTOSIZE)
            cv2.imshow("Segmentation", mask)
            dir_segmentations = "_Data\\Segmentations\\%02d-0.png" % currentImage

            segCompare = cv2.imread(dir_segmentations, 0)
            segCompare = cv2.resize(segCompare, (int(size[0]/2),int(size[1]/2)))
            retval, segCompare = cv2.threshold(segCompare, 5, 255, cv2.THRESH_BINARY)
            cv2.namedWindow("ExampleSeg",cv2.WINDOW_AUTOSIZE)
            cv2.imshow("ExampleSeg", segCompare)

            err1 = segCompare-mask
            err2 = mask-segCompare
            err = cv2.bitwise_or(err1, err2)
            totalpix = cv2.bitwise_or(mask,segCompare)
            # retval, err = cv2.threshold(err, 5, 255, cv2.THRESH_BINARY)
            # print(np.sum(err)/np.count_nonzero(err))
            # print(np.count_nonzero(segCompare))
            # print(np.count_nonzero(err))
            
            # err = np.equal(segCompare,mask).astype(np.uint8)
            retval, err = cv2.threshold(err, 1, 255, cv2.THRESH_BINARY)
            print("The segmentation is %0.2f %% correct" % ((1-(np.count_nonzero(err)/np.count_nonzero(totalpix)))*100))
            cv2.namedWindow("diff",cv2.WINDOW_AUTOSIZE)
            cv2.imshow("diff", err)

        elif k == 105:
            tempShow("Calculating Edges + PCA...")
            grays = cv2.cvtColor(backdrop, cv2.COLOR_BGR2GRAY)
            edge_img, pca_teeth = asm.preperation_all(grays, all_landmarks_std)
            tempShow("Calculating Edges + PCA : DONE!")
        elif k == 111:
            for i in range(0,8):
                tooth_points = output[0,i,:,:]

                points = asm.active_shape(edge_img, tooth_points, pca_teeth[i], distance,alpha,contourEnabled,matchingEnabled)
                # print(all_landmarks_std[0,0,:,:])
                output[0,i,:,:] = points
            drawTeethOutput(output, backdrop)
            # print(output)
            # tempShow("ASM iteration complete!")
        elif k == 47:
            # print(output)
            np.save("initial_position", output)
            popup = np.ones((50,330), np.uint8)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(popup,'Position saved as initial_position.py',(10,25), font, 0.5,(240,255,255),1,cv2.LINE_AA)
            saved = cv2.namedWindow( "Saved", cv2.WINDOW_AUTOSIZE )
            cv2.imshow("Saved",popup)
            cv2.waitKey(1000)
            cv2.destroyWindow("Saved")
        elif k == 120:
            alpha += 0.5
            print("alpha value = " + str(alpha))
        elif k == 122:
            alpha -= 0.5
            print("alpha value = " + str(alpha))
        elif k == 114:
            distance += 1
            print("pixel distance to check = " + str(distance))
        elif k == 97:
            distance -= 1
            print("pixel distance to check = " + str(distance))
        elif k == 102:
            cv2.namedWindow("Edge image",cv2.WINDOW_AUTOSIZE)
            cv2.imshow("Edge image", edge_img.astype(np.uint8)*255)
        elif k == 113:
            contourEnabled = not contourEnabled
            if(contourEnabled):
            	print("contourEnabled=True: Using fitContour for fitting +++")
            else:
            	print("contourEnabled=False: Using fitFunction for fitting ---")
        elif k == 119:
            matchingEnabled = not matchingEnabled
            if(matchingEnabled):
            	print("matchingEnabled=True: Adjusting fitting to model +++")
            else:
            	print("matchingEnabled=False: Not adjusting fitting ---")





    # cv2.setMouseCallback('Radiograph',mousePosition,(resized_image,model))
    
if __name__ == "__main__": 
    # img = cv2.imread("_Data/Radiographs/01.tif")
    # resized_image = cv2.resize(img, (800, 400)) 
    # model = cv2.imread("_Data/Radiographs/02.tif")
    # resized_model = cv2.resize(model,(200,100))
    # showImages(resized_image,resized_model)
    InitializeASM()

