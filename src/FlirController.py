import config
import PySpin
import cv2
import ArduinoController as ac
import numpy as np
from ctypes import sizeof, c_uint8, c_uint64
from mmap import mmap
import multiprocessing as mp


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
            cv2.VideoWriter(config.VIDEOS_FOLDER + vidName, fourcc, config.MAX_TRIGGERED_FPS, (config.WIDTH, config.HEIGHT), False))

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
        self.saveProc = mp.Process(target=concurrent_save, args=(sharedFrameArrayShape, sharedFrameArrayPath, self.saveProcQueue, sharedFrameSaveCounterShape, sharedFrameSaveCounterPath,))
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
        self.configure_chunk_data(nodemap)
        camera.BeginAcquisition()
        return camera, nodemap

    def initialize_camera(self, camera, configureTrigger, acquisitionMode):

        camera.Init()
        nodemap = camera.GetNodeMap()
        self.set_binning_mode(nodemap)
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
            print("Unable to set framerate!")
            return False
        else:
            frameRateNode.SetValue(fps)
            print("Framerate set to " + str(fps))

    def set_camera_exposure(self, camera, exposure):

        if camera.ExposureAuto.GetAccessMode() != PySpin.RW:
            return False
        else:
            camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)

        if camera.ExposureTime.GetAccessMode() != PySpin.RW:
            print("Unable to set exposure!")
            return False
        else:
            # Ensure desired exposure time does not exceed the maximum
            exposure = min(camera.ExposureTime.GetMax(), exposure)
            camera.ExposureTime.SetValue(exposure)
            print("Exposure set to " + str(exposure))

    def set_binning_mode(self, nodemap):

        binningHorizontalNode = PySpin.CEnumerationPtr(nodemap.GetNode('BinningHorizontalMode'))
        if not PySpin.IsAvailable(binningHorizontalNode) or not PySpin.IsWritable(binningHorizontalNode):
            return False

        binningHorizontalModeNode = binningHorizontalNode.GetEntryByName('Average')
        if not PySpin.IsAvailable(binningHorizontalModeNode) or not PySpin.IsReadable(
                binningHorizontalModeNode):
            return False

        mode = binningHorizontalModeNode.GetValue()
        binningHorizontalNode.SetIntValue(mode)



        binningHorizontalNode = PySpin.CIntegerPtr(nodemap.GetNode('BinningHorizontal'))
        if not PySpin.IsAvailable(binningHorizontalNode) or not PySpin.IsWritable(binningHorizontalNode):
            return False
        else:
            binningHorizontalNode.SetValue(1)



        binningVerticalNode = PySpin.CEnumerationPtr(nodemap.GetNode('BinningVerticalMode'))
        if not PySpin.IsAvailable(binningVerticalNode) or not PySpin.IsWritable(binningVerticalNode):
            return False

        binningVerticalModeNode = binningVerticalNode.GetEntryByName('Average')
        if not PySpin.IsAvailable(binningVerticalModeNode) or not PySpin.IsReadable(
                binningVerticalModeNode):
            return False

        mode = binningVerticalModeNode.GetValue()
        binningVerticalNode.SetIntValue(mode)

        binningVerticalNode = PySpin.CIntegerPtr(nodemap.GetNode('BinningVertical'))
        if not PySpin.IsAvailable(binningVerticalNode) or not PySpin.IsWritable(binningVerticalNode):
            return False
        else:
            binningVerticalNode.SetValue(1)



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
            node_pixel_format_mono8 = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName('Mono8'))
            if PySpin.IsAvailable(node_pixel_format_mono8) and PySpin.IsReadable(node_pixel_format_mono8):

                # Retrieve the integer value from the entry node
                pixel_format_mono8 = node_pixel_format_mono8.GetValue()
                # Set integer as new value for enumeration node
                node_pixel_format.SetIntValue(pixel_format_mono8)

    def configure_chunk_data(self, nodemap):
        """
        This function configures the camera to add chunk data to each image. It does
        this by enabling each type of chunk data before enabling chunk data mode.
        When chunk data is turned on, the data is made available in both the nodemap
        and each image.

        :param nodemap: Transport layer device nodemap.
        :type nodemap: INodeMap
        :return: True if successful, False otherwise
        :rtype: bool
        """
        try:
            result = True
            print('\n*** CONFIGURING CHUNK DATA ***\n')

            # Activate chunk mode
            #
            # *** NOTES ***
            # Once enabled, chunk data will be available at the end of the payload
            # of every image captured until it is disabled. Chunk data can also be
            # retrieved from the nodemap.
            chunk_mode_active = PySpin.CBooleanPtr(nodemap.GetNode('ChunkModeActive'))

            if PySpin.IsAvailable(chunk_mode_active) and PySpin.IsWritable(chunk_mode_active):
                chunk_mode_active.SetValue(True)

            print('Chunk mode activated...')

            # Enable all types of chunk data
            #
            # *** NOTES ***
            # Enabling chunk data requires working with nodes: "ChunkSelector"
            # is an enumeration selector node and "ChunkEnable" is a boolean. It
            # requires retrieving the selector node (which is of enumeration node
            # type), selecting the entry of the chunk data to be enabled, retrieving
            # the corresponding boolean, and setting it to be true.
            #
            # In this example, all chunk data is enabled, so these steps are
            # performed in a loop. Once this is complete, chunk mode still needs to
            # be activated.
            chunk_selector = PySpin.CEnumerationPtr(nodemap.GetNode('ChunkSelector'))

            if not PySpin.IsAvailable(chunk_selector) or not PySpin.IsReadable(chunk_selector):
                print('Unable to retrieve chunk selector. Aborting...\n')
                return False

            # Retrieve entries
            #
            # *** NOTES ***
            # PySpin handles mass entry retrieval in a different way than the C++
            # API. Instead of taking in a NodeList_t reference, GetEntries() takes
            # no parameters and gives us a list of INodes. Since we want these INodes
            # to be of type CEnumEntryPtr, we can use a list comprehension to
            # transform all of our collected INodes into CEnumEntryPtrs at once.
            entries = [PySpin.CEnumEntryPtr(chunk_selector_entry) for chunk_selector_entry in
                       chunk_selector.GetEntries()]

            print('Enabling entries...')

            # Iterate through our list and select each entry node to enable
            for chunk_selector_entry in entries:
                # Go to next node if problem occurs
                if not PySpin.IsAvailable(chunk_selector_entry) or not PySpin.IsReadable(chunk_selector_entry):
                    continue

                chunk_selector.SetIntValue(chunk_selector_entry.GetValue())

                chunk_str = '\t {}:'.format(chunk_selector_entry.GetSymbolic())

                # Retrieve corresponding boolean
                chunk_enable = PySpin.CBooleanPtr(nodemap.GetNode('ChunkEnable'))

                # Enable the boolean, thus enabling the corresponding chunk data
                if not PySpin.IsAvailable(chunk_enable):
                    print('{} not available'.format(chunk_str))
                    result = False
                elif chunk_enable.GetValue() is True:
                    print('{} enabled'.format(chunk_str))
                elif PySpin.IsWritable(chunk_enable):
                    chunk_enable.SetValue(True)
                    print('{} enabled'.format(chunk_str))
                else:
                    print('{} not writable'.format(chunk_str))
                    result = False

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            result = False

        return result

    def display_chunk_data_from_image(self, image):

        chunk_data = image.GetChunkData()
        frame_id = chunk_data.GetFrameID()
        timestamp = chunk_data.GetTimestamp()
        return timestamp


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
        numFramesToAcquire = int(config.MAX_TRIGGERED_FPS * config.RECORDING_DURATION_S)
        self.saveProcQueue.put('START')
        self.arduinoController.start_pulses(numFramesToAcquire)
        timestamps = [[], []]

        for frameNum in range(0, numFramesToAcquire):

            # Check that we're not lapping the frame saving process
            if frameNum * config.NUM_CAMERAS >= self.sharedFrameSaveCounter[0][0] + config.MAX_FRAMES_IN_BUFFER:
                print("Error: Out of memory!")
                exit(0)

            # Get the frames synchronously captured by all cameras and dump them into shared memory
            for camIndex in range(0, config.NUM_CAMERAS):

                img_result = self.cameras[camIndex].GetNextImage()
                timestamps[camIndex].append(self.display_chunk_data_from_image(img_result))
                self.sharedFrameBuffer[sharedFrameBufferIndex] = img_result.GetNDArray()
                self.saveProcQueue.put(sharedFrameBufferIndex)
                img_result.Release()
                sharedFrameBufferIndex += 1
                if sharedFrameBufferIndex == config.MAX_FRAMES_IN_BUFFER:
                    sharedFrameBufferIndex = 0
            print(str(frameNum))
        # Let the save process know this recording is done so it should reset all it's shared memory counters
        self.saveProcQueue.put('END')
        return 0
        for i in range(0 , len(timestamps[0]) - 1):
            ts1 = timestamps[0][i]
            ts1b = timestamps[0][i+1]
            ts2 = timestamps[1][i]
            ts2b = timestamps[1][i+1]
            print("CAM1 " + str(ts1b - ts1))
            print("CAM2 " + str(ts2b - ts2))
