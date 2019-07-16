import config
import serial


class ArduinoController(object):


	def __init__(self):


		# Hardware interface

		self.serialInterface = self.open_serial_interface()
		self.wait_for_arduino_confirmation()



	def __del__(self):
		if self.serialInterface != None:
			self.serialInterface.close()


	def open_serial_interface(self):

		# Try to open serial connection until it works
		while(1):
			serialInterface = serial.Serial(config.SERIAL_PORT_PATH, config.BAUDRATE, timeout=3)
			if serialInterface.is_open:
				return serialInterface
			else:
				print("Unable to open serial interface!")
				return None


	def wait_for_arduino_confirmation(self):

		# Wait for arduino to say it's ready
		while(1):
			confirmation = self.serialInterface.readline().decode()
			if confirmation == "ARDUINO READY\n":
				print(confirmation)
				break
			else:
				print("No response from arduino!")
				break

	def pulse(self):
		command = "PULSE " + "\n"
		self.serialInterface.write(command.encode('UTF-8'))
		response = self.serialInterface.readline().decode()
		if response == 'PC\n':
			return True
		else:
			return False
