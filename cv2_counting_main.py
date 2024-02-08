#ITERATION ! IN VEHICLE COUNTING


import cv2
import numpy as np
from datetime import datetime
#Import username, password, ports
from feed_access import keys #File not uploaded to Github

#============================================================================= <<<<<<<<<<<<<<<<<<<<<<<<<<
#Choose camera feed 1. to 3.  (4. and 5. is in testing)
CAM = 3
#============================================================================= <<<<<<<<<<<<<<<<<<<<<<<<<<


#Inbound
in_vehicles = 0
#Outbound
out_vehicles = 0
#Direction unknown
unknown_vehicles = 0


#Function for producing output count logs
def printout(direction_search_margin, matches, line_height, vehicles):
    found_direction_flag = 0
    global in_vehicles
    global out_vehicles
    #Loop through all abjects found in this frame (their center points)
    for (x, y) in matches:
        #Different checks for different video feeds
        if CAM == 1:
            #If point found in area of reference under the line
            if y < line_height and y > (line_height-direction_search_margin):
                in_vehicles = in_vehicles + 1
                found_direction_flag = 1
                break
            #If point found in area of reference above the line
            if y > line_height and y < (line_height+direction_search_margin):
                out_vehicles= out_vehicles + 1
                found_direction_flag = 1
                break
        elif CAM == 2:
            if y < line_height and y > (line_height-direction_search_margin):
                out_vehicles= out_vehicles + 1
                found_direction_flag = 1
                break
            if y > line_height and y < (line_height+direction_search_margin):
                in_vehicles = in_vehicles + 1
                found_direction_flag = 1
                break
        elif CAM == 3:
            if y < line_height and y > (line_height-direction_search_margin):
                out_vehicles= out_vehicles + 1
                found_direction_flag = 1
                break
            if y > line_height and y < (line_height+direction_search_margin):
                in_vehicles = in_vehicles + 1
                found_direction_flag = 1
                break
    #If direction of point not established
    if found_direction_flag == 0:
        global unknown_vehicles
        unknown_vehicles = unknown_vehicles + 1
    f.write(("\n************Update at " + current_time + "*************\n"))
    f.write("Stats:" +
            "{\n" +
            "Total vehicles: "+ str(vehicles) + "\n" +
            "Vehicles inbound: "+ str(in_vehicles) + "\n" +
            "Vehicles outbound: "+ str(out_vehicles) + "\n" +
            "Vehicles with unknown direction: "+ str(unknown_vehicles) + "\n" +
            "}\n")
    f.flush()

#Get central point
def get_centrolid(x, y, w, h):
   x1 = int(w / 2)
   y1 = int(h / 2)
 
   cx = x + x1
   cy = y + y1
   return cx, cy

username = keys.USER
password = keys.PASS

#Different count settings and parameters for each camera feed
if CAM == 1:
    min_contour_width = 180  
    min_contour_height = 160
    offset = 16  
    line_height = 370
    line_start = 690
    line_end = 950  
    timeout_frames = 20
    direction_search_margin = 70
    port = keys.PORT1
elif CAM == 2:
    min_contour_width = 90  
    min_contour_height = 90
    offset = 16  
    line_height = 205
    line_start = 60
    line_end = 190  
    timeout_frames = 10
    direction_search_margin = 70
    port = keys.PORT2
elif CAM == 3:
    min_contour_width = 160  
    min_contour_height = 160
    offset = 16  
    line_height = 440
    line_start = 220
    line_end = 520  
    timeout_frames = 16
    direction_search_margin = 70
    port = keys.PORT3

#Output file
f = open(f"output_logs/output_cam{CAM}.txt", "w")

camera_address = f"rtsp://{username}:{password}@vtfw.edi.lv:{port}/axis-media/media.amp"

cap = cv2.VideoCapture(camera_address)

matches = []
#Total count In & Out
vehicles = 0

cap.set(3, 1280)
cap.set(4, 960)
 
if cap.isOpened():
   ret, frame1 = cap.read()
else:
   ret = False
ret, frame1 = cap.read()
ret, frame2 = cap.read()

frame1 = cv2.resize(frame1, (1280, 960))
frame2 = cv2.resize(frame2, (1280, 960))

count = 0
flag = 0
while ret:
    #Establish current time
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    #Establish absolute difference between last two frames, to find moving objects
    d = cv2.absdiff(frame1, frame2)

    grey = cv2.cvtColor(d, cv2.COLOR_BGR2GRAY)    
    blur = cv2.GaussianBlur(grey, (5, 5), 0)
    
    ret, th = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(th, np.ones((3, 3)))

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))    
    closing = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel)
    contours, h = cv2.findContours(
        closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    # With moving objects found, we loop over their list
    for(i, c) in enumerate(contours):
        #BBox
        (x, y, w, h) = cv2.boundingRect(c)
        #Filter legitemate ones by their dimensions
        contour_valid = (w >= min_contour_width) and (
            h >= min_contour_height)
    
        if not contour_valid:
            continue
        
        #Display BBox
        cv2.rectangle(frame1, (x-10, y-10), (x+w+10, y+h+10), (255, 0, 0), 2)

        #Display counting line
        cv2.line(frame1, (line_start, line_height), (line_end, line_height), (0, 255, 0), 2)

        centrolid = get_centrolid(x, y, w, h)
        matches.append(centrolid)

        #Display object center point
        cv2.circle(frame1, centrolid, 5, (0, 255, 0), -1)
        cx, cy = get_centrolid(x, y, w, h)
        #print(matches)

    #If line cooloff timer has not been trigered
    if count == 0:
        #Loop through objects
        for (x, y) in matches:
            #If Line has been triggered
            if y < (line_height+offset) and y > (line_height-offset) and x > line_start and x < line_end:
                #print(f"{y} < {(line_height+offset)} and {y} > {(line_height-offset)}")
                #Add to total vehicles count
                vehicles = vehicles +1
                #Set off cooldown timer for Line triggering
                count = timeout_frames
                #Just triggered flag
                flag = 1
                break
    #If line was recently crossed already
    else:
        #If line crossed in last frame
        if flag == 1:
            #Establish direction and print situation in outputs
            printout(direction_search_margin, matches, line_height, vehicles)
            flag = 0
        #Decreasing timer count
        count = count - 1
    
    matches.clear()
 
    cv2.putText(frame1, "Total Vehicle Detected: " + str(vehicles), (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1,
               (0, 170, 0), 2)
 
 
    
    display = frame1
    display = cv2.resize(display, (1280, 960))
    cv2.imshow("Vehicle Counting", display)
    if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    frame1 = frame2
    ret, frame2 = cap.read()
    frame2 = cv2.resize(frame2, (1280, 960))
 
cv2.destroyAllWindows()
cap.release()
f.close()

