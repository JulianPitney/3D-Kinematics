import config
import PySpin
import cv2
import ArduinoController as ac
import numpy as np
from ctypes import sizeof, c_uint8, c_uint64
from mmap import mmap
import multiprocessing as mp
from time import sleep
from time import time

class TriggerType:
    SOFTWARE = 1
    HARDWARE = 2



def shared_array(shape, path, mode, dtype):
    for n in reversed(shape):
        dtype *= n
    with open(path, mode) as fd:

        size = fd.seek(0, 2)
        if size < sizeof(dtype):
            fd.truncate(sizeof(dtype))
        buf = mmap(fd.fileno(), sizeof(dtype))
        return np.ctypeslib.as_array(dtype.from_buffer(buf))



def init_video_windows():

    windowNames = []

    for i in range(0, config.NUM_CAMERAS):
        windowNames.append("cam" + str(i))
        cv2.namedWindow(windowNames[i], cv2.WINDOW_NORMAL)
        cv2.resizeWindow(windowNames[i], 720, 540)
        cv2.moveWindow(windowNames[i], 720, 0)

    return windowNames



def init_video_writers():

    videoWriters = []
    fourcc = cv2.VideoWriter_fourcc(*'XVID')

    for i in range(0, config.NUM_CAMERAS):
        vidName = "/output" + str(i) + ".avi"
        videoWriters.append(
            cv2.VideoWriter(config.VIDEOS_FOLDER + vidName, fourcc, config.FPS, (config.WIDTH, config.HEIGHT), False))

    return videoWriters



def concurrent_save(shape, path, queue, shape2, path2):

    sharedFrameBuffer = shared_array(shape, path, 'r+b', dtype=c_uint8)
    sharedFramesSavedCounter = shared_array(shape2, path2, 'r+b', dtype=c_uint64)
    videoWriters = []
    readyToSave = False
    currentCameraIndex = 0

    if config.DISPLAY_VIDEO_FEEDS:
        windowNames = init_video_windows()

    queue.put('READY')

    while True:
        if not queue.empty():

            msg = queue.get()

            # Start recording signal
            if msg == 'START':
                videoWriters = init_video_writers()
                readyToSave = True
                print("SAVE_PROC: Starting save!")
            # Save frame request from capture process
            elif isinstance(msg, int) and readyToSave:

                bufferIndex = msg
                frame = sharedFrameBuffer[bufferIndex]
                videoWriters[currentCameraIndex].write(frame)
                if config.DISPLAY_VIDEO_FEEDS:
                    cv2.imshow(windowNames[currentCameraIndex], frame)
                    cv2.waitKey(1)

                currentCameraIndex += 1
                if currentCameraIndex >= config.NUM_CAMERAS:
                    currentCameraIndex = 0

                sharedFramesSavedCounter[0][0] += 1

            # End of recording signal from capture process. Reset.
            elif msg == 'END':

                currentCameraIndex = 0
                sharedFramesSavedCounter[0][0] = 0
                readyToSave = False
                for videoWriter in videoWriters:
                    videoWriter.release()
                videoWriters = []
                print("SAVE_PROC: Done saving!")


            # Exit application signal
            elif msg == 'SHUTDOWN':
                cv2.destroyAllWindows()
                for videoWriter in videoWriters:
                    videoWriter.release()
                return 0




class CameraController(object):


    def __init__(self):

        self.arduinoController = ac.ArduinoController()
        self.CHOSEN_TRIGGER = TriggerType.HARDWARE
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
        sharedFrameArrayShape = (config.MAX_FRAMES_IN_BUFFER, config.HEIGHT, config.WIDTH)
        sharedFrameArrayPath = 'frames.buffer'
        sharedFrameSaveCounterShape = (1, 1)
        sharedFrameSaveCounterPath = 'frameCounter.buffer'
        self.sharedFrameBuffer = shared_array(sharedFrameArrayShape, sharedFrameArrayPath, 'w+b', dtype=c_uint8)
        self.sharedFrameSaveCounter = shared_array(sharedFrameSaveCounterShape, sharedFrameSaveCounterPath, 'w+b', dtype=c_uint64)
        self.saveProcQueue = mp.Queue()
        self.saveProc = mp.Process(target=concurrent_save, args=(sharedFrameArrayShape, sharedFrameArrayPath, self.saveProcQueue,                                                            sharedFrameSaveCounterShape, sharedFrameSaveCounterPath,))
        self.saveProc.start()

        while True:
            if not self.saveProcQueue.empty():
                msg = self.saveProcQueue.get()
                if msg == 'READY':
                    print('CONFIRMED READY')
                    break



    def __del__(self):

        for i in range(0, len(self.camList)):
            self.deinitialize_camera(self.cameras[i], self.nodemaps[i])

        self.saveProcQueue.put('SHUTDOWN')
        self.saveProc.join()


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
        self.set_resolution(nodemap, config.WIDTH, config.HEIGHT)
        self.set_isp(nodemap, False)
        self.set_camera_exposure(camera, config.EXPOSURE)
        self.set_camera_fps(nodemap, config.FPS)


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


    def synchronous_record(self):

        sharedFrameBufferIndex = 0
        numFramesToAcquire = int(config.FPS * config.RECORDING_DURATION_S)
        print("CAP_PROC: Starting capture!")
        self.saveProcQueue.put('START')
        startrec = time()
        for frameNum in range(0, numFramesToAcquire):

            # Check that we're not lapping the frame saving process
            if frameNum * config.NUM_CAMERAS >= self.sharedFrameSaveCounter[0][0] + config.MAX_FRAMES_IN_BUFFER:
                print("Error: Out of memory!")
                exit(0)

            # Send pulse command to Arduino (Do not wait for confirmation)
            self.arduinoController.pulse()
            sleep(config.EXPOSURE/1000000)


            # Get the frames synchronously captured by all cameras and dump them into shared memory
            start = time()
            for camIndex in range(0, config.NUM_CAMERAS):

                img_result = self.cameras[camIndex].GetNextImage()
                self.sharedFrameBuffer[sharedFrameBufferIndex] = img_result.GetNDArray()
                self.saveProcQueue.put(sharedFrameBufferIndex)
                sharedFrameBufferIndex += 1
                if sharedFrameBufferIndex == config.MAX_FRAMES_IN_BUFFER:
                    sharedFrameBufferIndex = 0
            end = time()
            print(str(end-start))
        # Let the save process know this recording is done so it should reset all it's shared memory counters
        endrec = time()
        print("REC TIME=" + str(endrec-startrec))
        print("CAP_PROC: Ending capture!")
        self.saveProcQueue.put('END')
