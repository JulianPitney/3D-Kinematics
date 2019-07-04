import PySpin
import cv2
import ArduinoController as ac
from time import sleep
import tifffile as tif
import numpy as np
import os
import random

FPS = 60
WIDTH = 1440
HEIGHT = 1080
PULSE_RATE_MS = 2

class TriggerType:
    SOFTWARE = 1
    HARDWARE = 2


def init_spinnaker():
    system = PySpin.System.GetInstance()
    camList = system.GetCameras()
    return camList, system


def init_video_stream(cameraIndex, camList):
    camera = camList.GetByIndex(cameraIndex)
    nodemap = initialize_camera(camera, True, 'Continuous')
    camera.BeginAcquisition()
    return camera, nodemap

def initialize_camera(camera, configureTrigger, acquisitionMode):

    global FPS, WIDTH, HEIGHT
    camera.Init()
    nodemap = camera.GetNodeMap()
    set_resolution(nodemap, WIDTH, HEIGHT)
    set_isp(nodemap, False)
    set_camera_exposure(camera, 2000)
    set_camera_fps(nodemap, FPS)


    # In order to access the node entries, they have to be casted to a pointer type (CEnumerationPtr here)
    node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
    if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
        return False

    node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName(acquisitionMode)
    if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(
            node_acquisition_mode_continuous):
        return False

    acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
    node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

    if configureTrigger:
        configure_trigger(camera)

    return nodemap


def deinitialize_camera(camera, nodemap):

    camera.EndAcquisition()
    reset_trigger(nodemap)
    camera.DeInit()
    del camera



def set_resolution(nodemap, width, height):

    node_width = PySpin.CIntegerPtr(nodemap.GetNode('Width'))
    if PySpin.IsAvailable(node_width) and PySpin.IsWritable(node_width):
        node_width.SetValue(width)
    else:
        print("Failed to set Width")

    node_height = PySpin.CIntegerPtr(nodemap.GetNode('Height'))
    if PySpin.IsAvailable(node_height) and PySpin.IsWritable(node_height):
        node_height.SetValue(height)
    else:
        print("Failed to set Height")









def set_camera_fps(nodemap, fps):

    enableAcquisitionFrameRateNode = PySpin.CBooleanPtr(nodemap.GetNode("AcquisitionFrameRateEnable"))
    if enableAcquisitionFrameRateNode.GetAccessMode() != PySpin.RW:
        return False
    else:
        enableAcquisitionFrameRateNode.SetValue(True)

    frameRateNode = PySpin.CFloatPtr(nodemap.GetNode("AcquisitionFrameRate"))
    if frameRateNode.GetAccessMode() != PySpin.RW:
        return False
    else:
        frameRateNode.SetValue(fps)


def set_camera_exposure(camera, exposure):

    if camera.ExposureAuto.GetAccessMode() != PySpin.RW:
        return False
    else:
        camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)

    if camera.ExposureTime.GetAccessMode() != PySpin.RW:
        return False
    else:
        # Ensure desired exposure time does not exceed the maximum
        exposure = min(camera.ExposureTime.GetMax(), exposure)
        camera.ExposureTime.SetValue(exposure)



def set_isp(nodemap, ISPMode):

    ISPNode = PySpin.CEnumerationPtr(nodemap.GetNode('ISP Enable'))

    if not PySpin.IsAvailable(ISPNode) or not PySpin.IsReadable(ISPNode):
        print("Failed to access ISP node!")
    else:
        ISPNode.SetIntValue(ISPMode)




def set_camera_pixel_format(self, nodemap):

    node_pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode('PixelFormat'))
    if PySpin.IsAvailable(node_pixel_format) and PySpin.IsWritable(node_pixel_format):

        # Retrieve the desired entry node from the enumeration node
        node_pixel_format_mono16 = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName('Mono16'))
        if PySpin.IsAvailable(node_pixel_format_mono16) and PySpin.IsReadable(node_pixel_format_mono16):

            # Retrieve the integer value from the entry node
            pixel_format_mono16 = node_pixel_format_mono16.GetValue()
            # Set integer as new value for enumeration node
            node_pixel_format.SetIntValue(pixel_format_mono16)
            self.guiLogQueue.put(self.LOG_PREFIX + "PIXEL_FORMAT=%s" % node_pixel_format.GetCurrentEntry().GetSymbolic())




def configure_trigger(camera):

    result = True

    if CHOSEN_TRIGGER == TriggerType.SOFTWARE:
        pass
    elif CHOSEN_TRIGGER == TriggerType.HARDWARE:
        pass

    try:
        # Ensure trigger mode off
        # The trigger must be disabled in order to configure whether the source
        # is software or hardware.
        nodemap = camera.GetNodeMap()
        node_trigger_mode = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerMode'))
        if not PySpin.IsAvailable(node_trigger_mode) or not PySpin.IsReadable(node_trigger_mode):
            return False

        node_trigger_mode_off = node_trigger_mode.GetEntryByName('Off')
        if not PySpin.IsAvailable(node_trigger_mode_off) or not PySpin.IsReadable(node_trigger_mode_off):
            return False

        node_trigger_mode.SetIntValue(node_trigger_mode_off.GetValue())

        # Select trigger source
        # The trigger source must be set to hardware or software while trigger
        # mode is off.
        node_trigger_source = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerSource'))
        if not PySpin.IsAvailable(node_trigger_source) or not PySpin.IsWritable(node_trigger_source):
            return False

        if CHOSEN_TRIGGER == TriggerType.SOFTWARE:
            node_trigger_source_software = node_trigger_source.GetEntryByName('Software')
            if not PySpin.IsAvailable(node_trigger_source_software) or not PySpin.IsReadable(
                    node_trigger_source_software):
                return False
            node_trigger_source.SetIntValue(node_trigger_source_software.GetValue())

        elif CHOSEN_TRIGGER == TriggerType.HARDWARE:
            node_trigger_source_hardware = node_trigger_source.GetEntryByName('Line0')
            if not PySpin.IsAvailable(node_trigger_source_hardware) or not PySpin.IsReadable(
                    node_trigger_source_hardware):
                return False
            node_trigger_source.SetIntValue(node_trigger_source_hardware.GetValue())

        # Turn trigger mode on
        # Once the appropriate trigger source has been set, turn trigger mode
        # on in order to retrieve images using the trigger.
        node_trigger_mode_on = node_trigger_mode.GetEntryByName('On')
        if not PySpin.IsAvailable(node_trigger_mode_on) or not PySpin.IsReadable(node_trigger_mode_on):
            return False

        node_trigger_mode.SetIntValue(node_trigger_mode_on.GetValue())

    except PySpin.SpinnakerException as ex:
        return False

    return result


def reset_trigger(nodemap):

    try:
        result = True
        node_trigger_mode = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerMode'))
        if not PySpin.IsAvailable(node_trigger_mode) or not PySpin.IsReadable(node_trigger_mode):
            return False

        node_trigger_mode_off = node_trigger_mode.GetEntryByName('Off')
        if not PySpin.IsAvailable(node_trigger_mode_off) or not PySpin.IsReadable(node_trigger_mode_off):
            return False

        node_trigger_mode.SetIntValue(node_trigger_mode_off.GetValue())

    except PySpin.SpinnakerException as ex:
        result = False

    return result



def retrieve_next_image(cameraIndex, cameras):

    image_result = cameras[cameraIndex].GetNextImage()
    if image_result.IsIncomplete():
        return False
    else:
        image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
        image_converted = image_converted.GetNDArray()
        return image_converted







CHOSEN_TRIGGER = TriggerType.HARDWARE
SERIAL_PORT_PATH = "COM3"
BAUDRATE = 115200
arduinoController = ac.ArduinoController(SERIAL_PORT_PATH, BAUDRATE)

# Spinnaker Initialization
camList, system = init_spinnaker()
cameras = []
nodemaps = []
print(len(camList))
for i in range(0, len(camList)):
    camera, nodemap = init_video_stream(i, camList)
    cameras.append(camera)
    nodemaps.append(nodemap)



cv2.namedWindow("cam1", cv2.WINDOW_NORMAL)
cv2.namedWindow("cam2", cv2.WINDOW_NORMAL)
cv2.resizeWindow("cam1", 720, 540)
cv2.resizeWindow("cam2", 720, 540)
cv2.moveWindow("cam1", 0,0)
cv2.moveWindow("cam2", 720,0)


cam1Frames = []
cam2Frames = []
fourcc = cv2.VideoWriter_fourcc(*'XVID')
cam1Vid = cv2.VideoWriter('output1.avi',fourcc, FPS, (WIDTH,HEIGHT), False)
cam2Vid = cv2.VideoWriter('output2.avi',fourcc, FPS, (WIDTH,HEIGHT), False)


print("waiting 5s...")
sleep(5)
print("starting pulses...")
arduinoController.start_pulses(PULSE_RATE_MS)

while(1):

    img1 = retrieve_next_image(0, cameras)
    img2 = retrieve_next_image(1, cameras)
    cam1Frames.append(img1)
    cam2Frames.append(img2)


    cv2.imshow("cam1", img1)
    cv2.imshow("cam2", img2)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

print("CAM1_FRAMES_CAPTURED=" + str(len(cam1Frames)))
print("CAM2_FRAMES_CAPTURED=" + str(len(cam2Frames)))
print("TARGET_FPS=" + str(FPS))
#for i in range(len(cam1Frames)):
#
#    cam1Vid.write(cam1Frames[i])
#    cam2Vid.write(cam2Frames[i])



for i in range(0, len(camList)):
    cam1Vid.release()
    cam2Vid.release()
    cv2.destroyAllWindows()
    deinitialize_camera(cameras[i], nodemaps[i])

