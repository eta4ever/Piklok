"""
Работа с модулем индикации на ИН-12 с последовательным интерфейсом
"""

try:
	import RPi.GPIO as GPIO 	# для GPIO
	import time 				# для задержек
	from datetime import datetime # для получения системного времени
	import random # для случайного вывода в эффектах

	nData = 3; #GPIO3 - линия данных
	nCLK = 5; #GPIO5 - линия тактирования

	def gpioInit():
		"""
		Инициализируем GPIO
		"""
		# Режим GPIO
		GPIO.setmode(GPIO.BOARD)
		# Отключение предупреждений
		GPIO.setwarnings(False)

		# GPIO выходы
		GPIO.setup(nData, GPIO.OUT)
		GPIO.setup(nCLK, GPIO.OUT)
		GPIO.output(nData, 0)
		GPIO.output(nCLK, 0)

	def pushBits (halfByte):
		"""
		выдать 4 бита в последовательный интерфейс модуля индикации
		"""
		for bit in range(0,4):
			# получить один бит сдвигом и &
			# и записать в GPIO
			current_bit = (halfByte >> bit) & 1
			GPIO.output(nData, current_bit)

		# такт загрузки
		time.sleep(0.01)
		GPIO.output(nCLK, 1)
		time.sleep(0.01)
		GPIO.output(nCLK, 0)
		time.sleep(0.01)

	def outputTime (hH, hL, mH, mL):
		"""
		вывести время. hH - старший полубайт часов, hL - младший,
		аналогично для минут
		"""

		# так уж схемотехнически странно получилось. На старших пинах регистров
        # сидят старшие разряды. Поэтому порядок запихивания битов такой:
    	# старший полубайт часов, младший часов, старший минут, младший минут.
		
    	pushBits(hH)
    	pushBits(hL)
    	pushBits(mH)
    	pushBits(mL)

	def effectShuffle(iterNo, iterDelay):
		"""
		Показываем случайные цифры
		iterNo итераций, задерка итерации iterDelay
		"""
		for dummy_counter in range(0,iterNo):
			outputTime(random.randrange(0,10), random.randrange(0,10), random.randrange(0,10), random.randrange(0,10))
			time.sleep(iterDelay)

	# основная программа
	gpioInit()
	effectDisplayed = False # флаг показанного эффекта

	while (True):
		
		# получение даты-времени
		now = datetime.now()
		
		# формирование разрядов
		digits = [now.minute % 10, now.minute // 10, now.hour % 10, now.hour // 10] 
		
		# каждые 10 минут - эффект случайных цифр
		# надо запустить только один раз! Поэтому поставить флаг, а на
		# следующей минуте его сбросить

		if ( (values[0] == 0) and not(effect_displayed)):
			effectShuffle(20, 0.1)
			effectDisplayed = True

		if (values[0] == 1):
			effectDisplayed = False

		# вывод
		outputTime(digits[3], digits[2], digits[1], digits[0])
		
		# пауза
		time.sleep(1)

finally: 
	# освободить GPIO по завершению программы
	GPIO.cleanup() 
