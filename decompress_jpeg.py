# _*_ encoding=utf-8 _*_
from ctypes import *
import numpy as np

class decoded_yuv_t(Structure):
    _fields_ = [('image_width', c_int), ('image_height', c_int), ('buffer_y_width', c_int), ('buffer_y_height', c_int), \
        ('buffer_u_width', c_int), ('buffer_u_height', c_int), ('buffer_v_width', c_int), ('buffer_v_height', c_int), ('buffer_ptr', c_void_p)]

class decoded_rgb_t(Structure):
    _fields_ = [('image_width', c_int), ('image_height', c_int), ('buffer_ptr', c_void_p)]

class jpeg_reader(object):
	def __init__(self, jpeg_file:str):
		super().__init__()
		self.file_name = jpeg_file
		self.reader = CDLL('./libjpeg_read.dll')
		self.reader.read_rgb_from_JPEG_file.restype = c_int
		self.reader.read_rgb_from_JPEG_file.argtypes = (c_char_p, POINTER(decoded_rgb_t))
		self.reader.read_raw_data_from_JPEG_file.restype = c_int
		self.reader.read_raw_data_from_JPEG_file.argtypes = (c_char_p, POINTER(decoded_yuv_t))
	
	def get_yuv_data(self):
		out_yuv = decoded_yuv_t()
		ret = reader.read_raw_data_from_JPEG_file(self.file_name, byref(out_yuv))
		if ret < 0:
			print('call read_raw_data_from_JPEG_file fail')
			return None
		else:
			print('call read_raw_data_from_JPEG_file success')
			y_width, y_height = out_yuv.buffer_y_width, out_yuv.buffer_y_height
			u_width, u_height = out_yuv.buffer_u_width, out_yuv.buffer_u_height
			v_width, v_height = out_yuv.buffer_v_width, out_yuv.buffer_v_height
			buf_from_mem = pythonapi.PyMemoryView_FromMemory
			buf_from_mem.restype = py_object
			buffer = buf_from_mem(c_void_p(out_yuv.buffer_ptr), y_width*y_height+u_width*u_height+v_width*v_height)
			yuv = np.frombuffer(buffer, np.uint8)
			return yuv, out_yuv
			
	def get_rgb_data(self):
		out_rgb = decoded_rgb_t()
		ret = self.reader.read_rgb_from_JPEG_file(self.file_name, byref(out_rgb))
		if ret < 0:
			print('call read_rgb_from_JPEG_file fail')
			return None
		else:
			print('call read_rgb_from_JPEG_file success')
			width, height = out_rgb.image_width, out_rgb.image_height
			buf_from_mem = pythonapi.PyMemoryView_FromMemory
			buf_from_mem.restype = py_object
			buffer = buf_from_mem(c_void_p(out_rgb.buffer_ptr), width*height*3)
			rgb = np.frombuffer(buffer, np.uint8)
			return rgb, out_rgb
			
	def releaseBuffer(self):
		self.reader.release_buffer()
	

