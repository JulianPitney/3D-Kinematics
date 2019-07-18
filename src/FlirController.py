import config
import PySpin
import cv2
import ArduinoController as ac
import numpy as np
from ctypes import sizeof, c_uint8
from mmap import mmap
import multiprocessing as mp
from math import floor
from time import sleep

class TriggerType:
    SOFTWARE = 1
    HARDWARE = 2



def shared_array(shape, path, mode='rb', dtype=c_uint8):
    for n in reversed(shape):
        dtype *= n
    with open(path, mode) as fd:

        size = fd.seek(0, 2)
        if size < sizeof(dtype):
            fd.truncate(sizeof(dtype))
        buf = mmap(fd.fileno(), sizeof(dtype))
        return np.ctypeslib.as_array(dtype.from_buffer(buf))



def concurrent_save(shape, path, queue):


    windows = []
    windowNames = []
    videoWriters = []
    fourcc = cv2.VideoWriter_fourcc(*'XVID')

    for i in range(0, config.NUM_CAMERAS):

        vidName = "/output" + str(i) + ".avi"
        windowNames.append("cam" + str(i))
        videoWriters.append(cv2.VideoWriter(config.VIDEOS_FOLDER + vidName, fourcc, config.FPS, (config.WIDTH, config.HEIGHT), False))
        windows.append(cv2.namedWindow(windowNames[i], cv2.WINDOW_NORMAL))
        cv2.resizeWindow(windowNames[i], 720, 540)
        cv2.moveWindow(windowNames[i], 720, 0)


    sharedArray = shared_array(shape, path, 'r+b')
    frameIndex = None
    currentCameraIndex = 0
    queue.put('READY')


    while True:
        if not queue.empty():

            nextFrameIndex = queue.get()
            frame = sharedArray[nextFrameIndex]
            cv2.imshow(windowNames[currentCameraIndex], frame)
            currentCameraIndex += 1
            if currentCameraIndex >= config.NUM_CAMERAS:
                currentCameraIndex = 0
            cv2.waitKey(1)



class CameraController(object):


    def __init__(self):

        self.arduinoController = ac.ArduinoController()
        self.CHOSEN_TRIGGER = TriggerType.HARDWARE
        self.FPS = config.FPS
        self.EXPOSURE = config.EXPOSURE
        self.WIDTH = config.WIDTH
        self.HEIGHT = config.HEIGHT
        self.RECORDING_DURATION_S = config.RECORDING_DURATION_S
        self.camList = None
        self.system = None
        self.cameras = []
        self.nodemaps = []

        # Spinnaker Initialization
        self.camList, self.system = self.init_spinnaker()
        for i in range(0, len(self.camList)):
            camera, nodemap = self.init_video_stream(i)
            self.cameras.append(camera)
            self.nodemaps.append(nodemap)

        if len(self.camList) != config.NUM_CAMERAS:
            print("Assertion Error: config.NUM_CAMERAS does not match number of attached cameras!")
            exit()


        # Setup shared memory for concurrent frame recording/saving
        shape = (config.MAX_FRAMES_IN_BUFFER, config.HEIGHT, config.WIDTH)
        path = 'tmp.buffer'
        self.sharedArray = shared_array(shape, path, 'w+b')
        self.saveProcQueue = mp.Queue()
        saveProc = mp.Process(target=concurrent_save, args=(shape, path, self.saveProcQueue,))
        saveProc.start()
        while True:
            if not self.saveProcQueue.empty():
                msg = self.saveProcQueue.get()
                if msg == 'READY':
                    print('CONFIRMED READY')
                    break



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

    def retrieve_next_image(self, cameraIndex):

        image_result = self.cameras[cameraIndex].GetNextImage()
        if image_result.IsIncomplete():
            return False
        else:
            image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
            image_converted = image_converted.GetNDArray()
            return image_converted


    def synchronous_record(self):

        sharedArrayWriteIndex = 0
        numFramesToAcquire = int(config.FPS * self.RECORDING_DURATION_S)

        for frameNum in range(0, numFramesToAcquire):

            pulseConfirmed = False
            while not pulseConfirmed:
                pulseConfirmed = self.arduinoController.pulse()

                sleep(1/config.FPS - ((1/config.FPS)/5))


            for camIndex in range(0, len(self.cameras)):

                self.sharedArray[sharedArrayWriteIndex] = self.retrieve_next_image(camIndex)
                self.saveProcQueue.put(sharedArrayWriteIndex)

                sharedArrayWriteIndex += 1
                if sharedArrayWriteIndex == config.MAX_FRAMES_IN_BUFFER:
                    sharedArrayWriteIndex = 0

        self.saveProcQueue.put('RESET')
