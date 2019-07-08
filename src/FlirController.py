import config
import PySpin
import cv2
import ArduinoController as ac
from time import sleep
import tifffile as tif
import numpy as np
import os
import random



class TriggerType:
    SOFTWARE = 1
    HARDWARE = 2


class CameraController(object):

    SERIAL_PORT_PATH = config.SERIAL_PORT_PATH
    BAUDRATE = config.BAUDRATE
    arduinoController = ac.ArduinoController(SERIAL_PORT_PATH, BAUDRATE)
    CHOSEN_TRIGGER = TriggerType.HARDWARE
    FPS = config.FPS
    EXPOSURE = config.EXPOSURE
    WIDTH = config.WIDTH
    HEIGHT = config.HEIGHT
    PULSE_RATE_MS = config.PULSE_RATE_MS
    camList = None
    system = None
    cameras = []
    nodemaps = []


    def __init__(self):
        # Spinnaker Initialization
        self.camList, self.system = self.init_spinnaker()
        print(len(self.camList))
        for i in range(0, len(self.camList)):
            camera, nodemap = self.init_video_stream(i)
            self.cameras.append(camera)
            self.nodemaps.append(nodemap)

    def __del__(self):

        for i in range(0, len(self.camList)):
            self.deinitialize_camera(self.cameras[i], self.nodemaps[i])



    def init_spinnaker(self):
        system = PySpin.System.GetInstance()
        camList = system.GetCameras()
        return camList, system


    def init_video_stream(self, cameraIndex):
        camera = self.camList.GetByIndex(cameraIndex)
        nodemap = self.initialize_camera(camera, True, 'Continuous')
        camera.BeginAcquisition()
        return camera, nodemap

    def initialize_camera(self, camera, configureTrigger, acquisitionMode):

        camera.Init()
        nodemap = camera.GetNodeMap()
        self.set_resolution(nodemap, self.WIDTH, self.HEIGHT)
        self.set_isp(nodemap, False)
        self.set_camera_exposure(camera, self.EXPOSURE)
        self.set_camera_fps(nodemap, self.FPS)


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
            self.configure_trigger(camera)

        return nodemap


    def deinitialize_camera(self, camera, nodemap):

        camera.EndAcquisition()
        self.reset_trigger(nodemap)
        camera.DeInit()
        del camera

    def set_resolution(self, nodemap, width, height):

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

    def set_camera_fps(self, nodemap, fps):

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

    def set_camera_exposure(self, camera, exposure):

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

    def set_isp(self, nodemap, ISPMode):

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

    def configure_trigger(self, camera):

        result = True

        if self.CHOSEN_TRIGGER == TriggerType.SOFTWARE:
            pass
        elif self.CHOSEN_TRIGGER == TriggerType.HARDWARE:
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

            if self.CHOSEN_TRIGGER == TriggerType.SOFTWARE:
                node_trigger_source_software = node_trigger_source.GetEntryByName('Software')
                if not PySpin.IsAvailable(node_trigger_source_software) or not PySpin.IsReadable(
                        node_trigger_source_software):
                    return False
                node_trigger_source.SetIntValue(node_trigger_source_software.GetValue())

            elif self.CHOSEN_TRIGGER == TriggerType.HARDWARE:
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

    def reset_trigger(self, nodemap):

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

    def retrieve_next_image(self, cameraIndex, cameras):

        image_result = cameras[cameraIndex].GetNextImage()
        if image_result.IsIncomplete():
            return False
        else:
            image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
            image_converted = image_converted.GetNDArray()
            return image_converted



    def synchronous_record(self):

        cv2.namedWindow("cam1", cv2.WINDOW_NORMAL)
        cv2.namedWindow("cam2", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("cam1", 720, 540)
        cv2.resizeWindow("cam2", 720, 540)
        cv2.moveWindow("cam1", 0, 0)
        cv2.moveWindow("cam2", 720, 0)

        cam1Frames = []
        cam2Frames = []
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        cam1Vid = cv2.VideoWriter(config.VIDEOS_FOLDER + '/output1.avi', fourcc, self.FPS, (self.WIDTH, self.HEIGHT), False)
        cam2Vid = cv2.VideoWriter(config.VIDEOS_FOLDER + '/output2.avi', fourcc, self.FPS, (self.WIDTH, self.HEIGHT), False)

        print("waiting 5s...")
        sleep(5)
        print("starting pulses...")
        self.arduinoController.start_pulses(self.PULSE_RATE_MS)

        while(1):

            img1 = self.retrieve_next_image(0, self.cameras)
            img2 = self.retrieve_next_image(1, self.cameras)
            cam1Frames.append(img1)
            cam2Frames.append(img2)
            #cv2.imshow("cam1", img1)
            #cv2.imshow("cam2", img2)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        print("CAM1_FRAMES_CAPTURED=" + str(len(cam1Frames)))
        print("CAM2_FRAMES_CAPTURED=" + str(len(cam2Frames)))
        print("TARGET_FPS=" + str(self.FPS))
        for i in range(len(cam1Frames)):

            cam1Vid.write(cam1Frames[i])
            cam2Vid.write(cam2Frames[i])

        cam1Vid.release()
        cam2Vid.release()
        cv2.destroyAllWindows()

