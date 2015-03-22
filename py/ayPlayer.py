import serial, struct, time, sys
import RPi.GPIO as GPIO     # для GPIO

# параметры COM порта
comPort = "/dev/ttyAMA0"
baudRate = 38400

# сообщение, по получению которого надо отправить 256 байт
message = 8

#GPIO сброса модуля
resetPin = 11

def readNullTermString(fileConn):
    """
    Для обработки заголовка YM-файла. Там используется несколько NT-строк.
    Читает символы, прибавляет к строке, пока не найдет нулевой.
    """
    currString = ''
    currChar = fileConn.read(1)

    # тут на всякий случай еще условие на EoF, а то мало ли
    while ( (currChar != b'\x00') and (currChar)):
        currString += chr(struct.unpack('b',currChar)[0])
        currChar = fileConn.read(1)
    return currString

def readAllInterleaved(fileConn, frameCount):
    """
    Запускается после обработки заголовка. Возвращает "последовательный" дамп регистров.
    Обрабатываемый массив данных выглядит как "все состояния регистра 0, 
    все состояния регистра 1..." и т.д. до 15. Это чтобы файл паковался знатно.
    Нам же надо пачки состояний регистров.
    """

    registerDump = []

    # в качестве базы используем текущую позицию, полученную после обработки заголовка
    baseOffset = fileConn.tell() 

    # интерпретируем байты как unsigned char (C) в Integer
    for frame in range(0,frameCount):
        for register in range(0,16):
            fileConn.seek(baseOffset + frameCount*register + frame)
            registerDump.append(struct.unpack('B',fileConn.read(1))[0])

    return registerDump

def gpioInit():
    """
    Инициализировать пин /сброса
    """
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(resetPin, GPIO.OUT)
    GPIO.output(resetPin, 1)
    time.sleep(0.5)

def moduleReset():
    """
    Сброс модуля
    """
    GPIO.output(resetPin, 0)
    time.sleep(0.5)
    GPIO.output(resetPin, 1)

# инициализировать GPIO
gpioInit()

# взять имя файла из параметра командной строки, открыть его
testFile = sys.argv[1]
print(testFile)
fileConn = open(testFile, 'rb')

fileConn.read(4) # ID типа файла, напр. YM6!
fileConn.read(8) # Проверочная строка LeOnArD!

# кол-во фреймов в файле. 4 байта Big Endian (>L) в unsigned Long (L)
# unsigned long - это по-сишному, в Питоне будет integer
frameCount = struct.unpack('>L',fileConn.read(4))[0]

fileConn.read(4) # какие-то атрибуты

# количество сэмплов digidrum, в unsigned short (H)
# unsigned short - это по-сишному, в Питоне будет integer
digidrumCount = struct.unpack ('H',fileConn.read(2))[0]
 
# частота YM в Гц, 1.7M - Speccy, 2M - Atari
YMClock = struct.unpack('>L',fileConn.read(4))[0]

fileConn.read(2) # частота обновления, обычно 50 Гц
fileConn.read(4) # loop frame
fileConn.read(2) # кол-во дополнительных байт заголовка. Сейчас всегда 0, игнор

# дальше пропустить cэмплы digidrums. 
for digidrum in range (0, digidrumCount):
    sampleSize = struct.unpack('>L',fileConn.read(4))[0] # размер сэмпла
    fileConn.read(sampleSize) # сэмпл

trackName = readNullTermString(fileConn) # название трека
trackAuthor = readNullTermString(fileConn) # автор
trackComment = readNullTermString(fileConn) # комментарий

print('Frames:',frameCount)
print('YM Clock:',YMClock,'Hz')
print('Digidrum samples:', digidrumCount)
print('Track:', trackName)
print('Author:', trackAuthor)
print('Comment:', trackComment)

# обработка заголовка закончена, дальше пошли данные

print('Processing interleaved data...')
registerDump = readAllInterleaved(fileConn, frameCount)
print('...done reading', len(registerDump)//16,'frames!')

# закрыть файл 
fileConn.close()

# открыть последовательный порт
serialConn = serial.Serial(comPort, baudRate, timeout = 1)

print('Now Playing!')

# сбросить модуль
moduleReset()

currentPos = 0 # текущая позиция в большом массиве
endPos = frameCount * 16 # конечная позиция

while (currentPos < endPos):

    # ждать запроса
    request = serialConn.read()
    while ( not request ):
        request = serialConn.read()

    # по получению запроса отправить в порт 256 байт из массива
    for currByte in range(0,256):
        
        # если данные в массиве есть, записать их в порт. Если 
        # массив кончился - отдать нули
        if ( (currentPos + currByte) < len(registerDump) ):
            regState = bytes([registerDump[currentPos + currByte]])
        else:
            regState = bytes([0])
        
        serialConn.write(regState)

    currentPos += 256

# закрыть порт
serialConn.close()
time.sleep(0.5)

# сбросить модуль
moduleReset()