import PySpin
import cv2
import tifffile as tif
import numpy as np
import os
import random


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

    camera.Init()
    nodemap = camera.GetNodeMap()
    set_camera_exposure(camera, 1000)


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

# Spinnaker Initialization
camList, system = init_spinnaker()
cameras = []
nodemaps = []
lastFrame = []
print(len(camList))
for i in range(0, len(camList)):
    camera, nodemap = init_video_stream(i, camList)
    cameras.append(camera)
    nodemaps.append(nodemap)


cam1ImgNum = 0
cam2ImgNum = 0
cv2.namedWindow("cam1", cv2.WINDOW_AUTOSIZE)
#cv2.namedWindow("cam2", cv2.WINDOW_AUTOSIZE)


while(1):

    img1 = retrieve_next_image(0, cameras)
    #img2 = retrieve_next_image(1, cameras)

    cv2.imshow("cam1", img1)
    cv2.waitKey(1)
    #cv2.imshow("cam2", img2)
    #cv2.waitKey(1)

    #cv2.imwrite("./cam1/" + str(cam1ImgNum) + ".png", img1)
    #cv2.imwrite("./cam2/" + str(cam2ImgNum) + ".png", img2)
    #cam1ImgNum += 1
    #cam2ImgNum += 1

