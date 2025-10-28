from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
import shutil
from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		self.master.bind("<Configure>", lambda event: self.updateMovie(CACHE_FILE_NAME + str(self.sessionId) + "-" + str(self.frameNbr) + CACHE_FILE_EXT))
		self.label = Label(self.master, bg="gray")
		self.label.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)
		self.master.rowconfigure(0, weight=1)
		self.master.columnconfigure((0,1,2,3), weight=1)

		
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=40, width=80)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
	def setupMovie(self):
		"""Setup button handler."""
		if self.state == self.INIT:
				self.sendRtspRequest(self.SETUP)
	
	def exitClient(self):
		"""Teardown button handler."""
		# Send TEARDOWN
		self.sendRtspRequest(self.TEARDOWN)
		# Wait for server ack
		self.master.destroy()

	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
				self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
		if self.state == self.READY:
		# start listening RTP packets in a new thread
			threading.Thread(target=self.listenRtp, daemon=True).start()
			self.sendRtspRequest(self.PLAY)
	
	def listenRtp(self):		
		"""Listen for RTP packets."""
		while True:
			try:
				data, _ = self.rtpSocket.recvfrom(65536)
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)
					seq = rtpPacket.seqNum()
					# only process new frame
					if seq > self.frameNbr:
						self.frameNbr = seq
						payload = rtpPacket.getPayload()
						imageFile = self.writeFrame(payload)
						# update GUI in main thread
						self.master.after(0, self.updateMovie, imageFile)
			except socket.timeout:
				# timeout is normal: continue checking state
				if self.state != self.PLAYING:
					break
				continue
			except Exception as e:
				# connection closed or other error
				# print(traceback.format_exc())
				break
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		# Tạo thư mục cache nếu chưa có
		session_folder = f"cache/session_{self.sessionId}"
		os.makedirs(session_folder, exist_ok=True)

		# Tạo file frame trong thư mục riêng
		filename = os.path.join(session_folder, f"frame_{self.frameNbr}.jpg")
		try:
			with open(filename, "wb") as f:
				f.write(data)
		except:
			# Nếu lỗi, fallback sang file cache tạm
			filename = os.path.join(session_folder, "frame_latest.jpg")
			with open(filename, "wb") as f:
				f.write(data)
		return filename

	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		try:
			image = Image.open(imageFile)

			# Lấy kích thước cửa sổ hiện tại
			window_width = self.master.winfo_width()
			window_height = self.master.winfo_height() - 100  # trừ vùng nút bấm

			# Lấy kích thước gốc ảnh
			img_width, img_height = image.size

			# Tính tỉ lệ scale theo khung (giữ nguyên aspect ratio)
			ratio = min(window_width / img_width, window_height / img_height)
			new_width = int(img_width * ratio)
			new_height = int(img_height * ratio)

			# Resize ảnh đúng tỉ lệ (không méo)
			image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

			# Tạo nền trống màu xám để căn giữa ảnh
			background = Image.new("RGB", (window_width, window_height), (180, 180, 180))
			pos_x = (window_width - new_width) // 2
			pos_y = (window_height - new_height) // 2
			background.paste(image, (pos_x, pos_y))

			# Hiển thị ảnh
			photo = ImageTk.PhotoImage(background)
			self.label.configure(image=photo)
			self.label.image = photo
		except Exception as e:
			# print(e)  # bật debug nếu cần
			pass



		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkinter.messagebox.showwarning("Connection Error", "Cannot connect to server.")
			return
		# start thread to receive RTSP replies
		threading.Thread(target=self.recvRtspReply, daemon=True).start()
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		# increment sequence number
		self.rtspSeq += 1

		if requestCode == self.SETUP and self.state == self.INIT:
			request = "SETUP " + self.fileName + " RTSP/1.0\nCSeq: " + str(self.rtspSeq) + "\nTransport: RTP/UDP; client_port= " + str(self.rtpPort)
			self.requestSent = self.SETUP
			self.rtspSocket.send(request.encode())
		elif requestCode == self.PLAY and self.state == self.READY:
			request = "PLAY " + self.fileName + " RTSP/1.0\nCSeq: " + str(self.rtspSeq) + "\nSession: " + str(self.sessionId)
			self.requestSent = self.PLAY
			self.rtspSocket.send(request.encode())
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			request = "PAUSE " + self.fileName + " RTSP/1.0\nCSeq: " + str(self.rtspSeq) + "\nSession: " + str(self.sessionId)
			self.requestSent = self.PAUSE
			self.rtspSocket.send(request.encode())
		elif requestCode == self.TEARDOWN:
			request = "TEARDOWN " + self.fileName + " RTSP/1.0\nCSeq: " + str(self.rtspSeq) + "\nSession: " + str(self.sessionId)
			self.requestSent = self.TEARDOWN
			self.rtspSocket.send(request.encode())
	
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True:
			try:
				reply = self.rtspSocket.recv(1024)
				if reply:
					self.parseRtspReply(reply.decode("utf-8"))
			except Exception as e:
				break
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		lines = data.split('\n')
		# first line: RTSP/1.0 200 OK
		status = lines[0].split(' ')
		if len(status) < 2:
			return
		code = status[1]
		# get CSeq
		cseq = None
		session = None
		for line in lines[1:]:
			if "CSeq" in line:
				parts = line.split(':')
				if len(parts) >= 2:
					cseq = parts[1].strip()
			if "Session" in line:
				parts = line.split(':')
				if len(parts) >= 2:
					session = parts[1].strip()
		# only accept 200 OK
		if code == '200':
			if session:
				# set session id on SETUP
				try:
					self.sessionId = int(session)
				except:
					self.sessionId = session
			# react to request that was sent
			if self.requestSent == self.SETUP:
				# open RTP port to receive
				self.openRtpPort()
				self.state = self.READY
			elif self.requestSent == self.PLAY:
				self.state = self.PLAYING
			elif self.requestSent == self.PAUSE:
				self.state = self.READY
			elif self.requestSent == self.TEARDOWN:
				# close sockets and stop
				try:
					self.rtpSocket.close()
				except:
					pass
				self.rtspSocket.close()
				self.master.quit()
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...
		
		# Set the timeout value of the socket to 0.5sec
		# ...
		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		# Bind to the client's RTP port
		try:
			self.rtpSocket.bind(('', self.rtpPort))
		except:
			tkinter.messagebox.showwarning("RTP Port Error", "Unable to bind RTP port.")
		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)

	def handler(self):
		try:
			if self.state != self.INIT:
				self.sendRtspRequest(self.TEARDOWN)
		except:
			pass
		self.master.destroy()

		# Xóa thư mục cache của phiên
		try:
			session_folder = f"cache/session_{self.sessionId}"
			if os.path.exists(session_folder):
				shutil.rmtree(session_folder)
		except:
			pass

