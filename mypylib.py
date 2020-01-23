#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import os
import sys
import time
import json
import zlib
import base64
import psutil
import hashlib
import threading
import datetime as DateTimeLibrary
from urllib.request import urlopen
from shutil import copyfile


# self.buffer
_myName = "myName"
_myPath = "myPath"
_myFullName = "myFullName"
_myFullPath = "myFullPath"
_logFileName = "logFileName"
_localdbFileName = "localdbFileName"
_lockFileName = "lockFileName"
_logList = "logList"
_memoryUsing = "memoryUsing"
_freeSpaceMemory = "freeSpaceMemory"
_threadCount = "threadCount"
_threadCountOld = "threadCountOld"

# self.db
_config = "config"

# self.db.config
_logLevel = "logLevel"
_info = "info"
_warning = "warning"
_error = "error"
_debug = "debug"
_isLimitLogFile = "isLimitLogFile"
_isDeleteOldLogFile = "isDeleteOldLogFile"
_isIgnorLogWarning = "isIgnorLogWarning"
_isStartOnlyOneProcess = "isStartOnlyOneProcess"
_memoryUsinglimit = "memoryUsinglimit"
_isSelfUpdating = "isSelfUpdating"
_isLocaldbSaving = "isLocaldbSaving"
_isWritingLogFile = "isWritingLogFile"
_md5Url = "md5Url"
_appUrl = "appUrl"


class bcolors:
	'''This class is designed to display text in color format'''
	DEBUG = '\033[95m'
	INFO = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	ERROR = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'
#end class

class MyPyClass:
	def __init__(self):
		self.db = dict()
		self.db[_config] = dict()

		self.buffer = dict()
		self.buffer[_logList] = list()
		self.buffer[_threadCount] = None
		self.buffer[_memoryUsing] = None
		self.buffer[_freeSpaceMemory] = None

		# Get program, log and database file name
		myName = self.GetMyName()
		myPath = self.GetMyPath()
		self.buffer[_myName] = myName
		self.buffer[_myPath] = myPath
		self.buffer[_myFullName] = self.GetMyFullName()
		self.buffer[_myFullPath] = self.GetMyFullPath()
		self.buffer[_logFileName] = myPath + myName + ".log"
		self.buffer[_localdbFileName] = myPath + myName + ".db"
		self.buffer[_lockFileName] = myPath + '.' + myName + ".lock"

		# Ser default settings
		self.SetDefaultConfig()
	#end define

	def Init(self):
		# Start only one process (exit if process exist)
		if self.db[_config][_isStartOnlyOneProcess]:
			self.StartOnlyOneProcess()

		# Start other threads
		threading.Thread(target=self.WritingLogFile, name="Logging", daemon=True).start()
		threading.Thread(target=self.SelfTesting, name="SelfTesting", daemon=True).start()
		threading.Thread(target=self.LocaldbSaving, name="LocdbSaving", daemon=True).start()
		self.buffer[_threadCountOld] = threading.active_count()

		# Remove old log file
		if (self.db[_config][_isDeleteOldLogFile] and os.path.isfile(self.buffer[_logFileName])):
			os.remove(self.buffer[_logFileName])

		# Logging the start of the program
		self.AddLog("Start program '{0}'".format(self.buffer[_myFullPath]))
	#end define

	def SetDefaultConfig(self):
		self.db[_config][_logLevel] = _info # info || debug
		self.db[_config][_isLimitLogFile] = True
		self.db[_config][_isDeleteOldLogFile] = False
		self.db[_config][_isIgnorLogWarning] = False
		self.db[_config][_isStartOnlyOneProcess] = True
		self.db[_config][_memoryUsinglimit] = 50
		self.db[_config][_isSelfUpdating] = False
		self.db[_config][_isLocaldbSaving] = False
		self.db[_config][_isWritingLogFile] = True
	#end define

	def StartOnlyOneProcess(self):
		lockFileName = self.buffer[_lockFileName]
		if os.path.isfile(lockFileName):
			file = open(lockFileName, 'r')
			pid_str = file.read()
			file.close()
			try:
				pid = int(pid_str)
				process = psutil.Process(pid)
				fullProcessName = " ".join(process.cmdline())
			except:
				fullProcessName = ""
			if (fullProcessName.find(self.buffer[_myFullName]) > -1):
				print("The process is already running")
				sys.exit(1)
			#end if
		self.WritePidToLockFile()
	#end define

	def WritePidToLockFile(self):
		pid = os.getpid()
		pid_str = str(pid)
		lockFileName = self.buffer[_lockFileName]
		file = open(lockFileName, 'w')
		file.write(pid_str)
		file.close()
	#end define

	def SelfTesting(self):
		self.AddLog("Start SelfTesting thread.", _debug)
		while True:
			try:
				time.sleep(1)
				self.SelfTest()
			except Exception as err:
				self.AddLog("SelfTesting: {0}".format(err), _error)
	#end define

	def SelfTest(self):
		process = psutil.Process(os.getpid())
		memoryUsing = self.b2mb(process.memory_info().rss)
		freeSpaceMemory = self.b2mb(psutil.virtual_memory().available)
		threadCount = threading.active_count()
		self.buffer[_freeSpaceMemory] = freeSpaceMemory
		self.buffer[_memoryUsing] = memoryUsing
		self.buffer[_threadCount] = threadCount
		if memoryUsing > self.db[_config][_memoryUsinglimit]:
			self.db[_config][_memoryUsinglimit] += 50
			self.AddLog("Memory using: {0}Mb, free: {1}Mb".format(memoryUsing, freeSpaceMemory), _warning)
	#end define

	def PrintSelfTestingResult(self):
		threadCount_old = self.buffer[_threadCountOld]
		threadCount_new = self.buffer[_threadCount]
		memoryUsing = self.buffer[_memoryUsing]
		freeSpaceMemory = self.buffer[_freeSpaceMemory]
		self.AddLog("{0}Self testing informatinon:{1}".format(bcolors.INFO, bcolors.ENDC))
		self.AddLog("Threads: {0} -> {1}".format(threadCount_new, threadCount_old))
		self.AddLog("Memory using: {0}Mb, free: {1}Mb".format(memoryUsing, freeSpaceMemory))
	#end define

	def GetThreadName(self):
		return threading.currentThread().getName()
	#end define

	def GetMyFullName(self):
		myFullName = sys.argv[0]
		return myFullName
	#end define

	def GetMyName(self):
		myFullName = self.GetMyFullName()
		myName = myFullName[:myFullName.rfind('.')]
		return myName
	#end define

	def GetMyFullPath(self):
		myFullName = self.GetMyFullName()
		myFullPath = os.path.abspath(myFullName)
		return myFullPath
	#end define

	def GetMyPath(self):
		myFullPath = self.GetMyFullPath()
		myPath = myFullPath[:myFullPath.rfind('/')+1]
		return myPath
	#end define

	def AddLog(self, inputText, mode=_info):
		inputText = "{0}".format(inputText)
		timeText = DateTimeLibrary.datetime.utcnow().strftime("%d.%m.%Y, %H:%M:%S.%f")[:-3]
		timeText = "{0} (UTC)".format(timeText).ljust(32, ' ')

		# Pass if set log level
		if self.db[_config][_logLevel] != _debug and mode == _debug:
			return
		elif self.db[_config][_isIgnorLogWarning] and mode == _warning:
			return

		# Set color mode
		if mode == _info:
			colorStart = bcolors.INFO + bcolors.BOLD
		elif mode == _warning:
			colorStart = bcolors.WARNING + bcolors.BOLD
		elif mode == _error:
			colorStart = bcolors.ERROR + bcolors.BOLD
		elif mode == _debug:
			colorStart = bcolors.DEBUG + bcolors.BOLD
		else:
			colorStart = bcolors.UNDERLINE + bcolors.BOLD
		modeText = "{0}{1}{2}".format(colorStart, "[{0}]".format(mode).ljust(10, ' '), bcolors.ENDC)

		# Set color thread
		if mode == _error:
			colorStart = bcolors.ERROR + bcolors.BOLD
		else:
			colorStart = bcolors.OKGREEN + bcolors.BOLD
		threadText = "{0}{1}{2}".format(colorStart, "<{0}>".format(self.GetThreadName()).ljust(14, ' '), bcolors.ENDC)
		logText = modeText + timeText + threadText + inputText

		# Queue for recording
		self.buffer[_logList].append(logText)

		# Print log text
		print(logText)
	#end define

	def WritingLogFile(self):
		self.AddLog("Start WritingLogFile thread.", _debug)
		myBool = self.db[_config][_isWritingLogFile]
		while myBool:
			time.sleep(1)
			self.TryWriteLogFile()
	#end define

	def TryWriteLogFile(self):
		try:
			self.WriteLogFile()
		except Exception as err:
			self.AddLog("TryWriteLogFile: {0}".format(err), _error)
	#end define

	def WriteLogFile(self):
		logFileName = self.buffer[_logFileName]

		file = open(logFileName, 'a')
		while len(self.buffer[_logList]) > 0:
			logText = self.buffer[_logList].pop(0)
			file.write(logText + '\n')
		#end for
		file.close()

		# Control log size
		if self.db[_config][_isLimitLogFile] == False:
			return
		allline = self.CountLines(logFileName)
		if allline > 4096 + 256:
			delline = allline - 4096
			f=open(logFileName).readlines()
			i = 0
			while i < delline:
				f.pop(0)
				i = i + 1
			with open(logFileName,'w') as F:
				F.writelines(f)
	#end define

	def CountLines(self, filename, chunk_size=1<<13):
		if not os.path.isfile(filename):
			return 0
		with open(filename) as file:
			return sum(chunk.count('\n')
				for chunk in iter(lambda: file.read(chunk_size), ''))
	#end define

	def b2mb(self, item):
		return int(item/1024/1024)
	#end define

	def DictToBase64WithCompress(self, item):
		string = json.dumps(item)
		original = string.encode("utf-8")
		compressed = zlib.compress(original)
		b64 = base64.b64encode(compressed)
		data = b64.decode("utf-8")
		return data
	#end define

	def Base64ToDictWithDecompress(self, item):
		data = item.encode("utf-8")
		b64 = base64.b64decode(data)
		decompress = zlib.decompress(b64)
		original = decompress.decode("utf-8")
		data = json.loads(original)
		return data
	#end define

	def CorrectExit(self):
		time.sleep(1.1)
		os.remove(self.buffer[_lockFileName])
	#end define

	def LocaldbSaving(self):
		self.AddLog("Start LocaldbSaving thread.", _debug)
		myBool = self.db[_config][_isLocaldbSaving]
		while myBool:
			time.sleep(3) # 3 sec
			threading.Thread(target=self.LocaldbSave).start()
	#end define

	def TryLocaldbSave(self):
		try:
			self.LocaldbSave()
		except Exception as err:
			self.AddLog("TryLocaldbSave: {0}".format(err), _error)
	#end define

	def LocaldbSave(self):
		fileName = self.buffer[_localdbFileName]
		string = self.DictToBase64WithCompress(self.db)
		file = open(fileName, 'w')
		file.write(string)
		file.close()
	#end define

	def LocaldbLoad(self):
		result = False
		try:
			fileName = self.buffer[_localdbFileName]
			file = open(fileName, 'r')
			original = file.read()
			self.db = self.Base64ToDictWithDecompress(original)
			file.close()
			result = True
		except Exception as err:
			self.AddLog("LocaldbLoad: {0}".format(err), _error)
		return result
	#end define

	def SelfUpdating(self):
		self.AddLog("Start SelfUpdating thread.", _debug)
		myBool = self.db[_config][_isSelfUpdating]
		while myBool:
			time.sleep(600) # 600 sec
			threading.Thread(target=self.TrySelfUpdate).start()
	#end define

	def TrySelfUpdate(self):
		try:
			self.SelfUpdate()
		except Exception as err:
			self.AddLog("TrySelfUpdate: {0}".format(err), _error)
	#end define

	def SelfUpdate(self):
		myName = self.buffer[_myName]
		myFullName = self.buffer[_myFullName]
		md5Url = self.db[_config][_md5Url]
		appUrl = self.db[_config][_appUrl]
		if (md5Url == None or appUrl == None):
			return
		myFullPath = self.buffer[_myFullPath]
		text = self.GetRequest(md5Url)
		md5FromServer = self.Pars(text, "{0} md5: ".format(myFullName))
		myMd5 = self.GetHashMd5(myFullPath)
		if (myMd5 == md5FromServer):
			return
		self.AddLog("SelfUpdate", _debug)
		data = urlopen(appUrl).read()
		file = open(myFullPath, 'wb')
		file.write(data)
		file.close()
		os.system("systemctl restart {0}".format(myName))
	#end define

	def GetHashMd5(self, fileName):
		BLOCKSIZE = 65536
		hasher = hashlib.md5()
		with open(fileName, 'rb') as file:
			buf = file.read(BLOCKSIZE)
			while len(buf) > 0:
				hasher.update(buf)
				buf = file.read(BLOCKSIZE)
		return(hasher.hexdigest())
	#end define

	def Pars(self, text, search):
		text = text[text.find(search) + len(search):]
		text = text[:text.find("\n")]
		return text
	#end define

	def Ping(self, hostname):
		response = os.system("ping -c 1 -w 3 " + hostname + " > /dev/null")
		if response == 0:
			result = True
		else:
			result = False
		return result
	#end define

	def GetRequest(self, url):
		link = urlopen(url)
		data = link.read()
		text = data.decode("utf-8")
		return text
	#end define
#end class