"""
Имеется 4 индикатора ИН-12, управляемые дешифраторами К155ИД1.
Каждому надо выдать четыре бита. Считаем 0 разрядом младший разряд
минут, соотв., 3 - старший разряд часов
"""
try:
	import RPi.GPIO as GPIO 	# для GPIO
	import time 				# для задержек
	from datetime import datetime # для получения системного времени
	import random # для случайного вывода в эффектах

	# наборы GPIO, соответствующих разрядам 
	nixie_digit_gpios = [[3,5,7,11],[13,13,13,13],[13,13,13,13],[13,13,13,13]]

	def gpio_init(nixie_digit_gpios):
		"""
		Инициализируем GPIO
		"""
		# Режим GPIO
		GPIO.setmode(GPIO.BOARD)
		# Отключение предупреждений
		GPIO.setwarnings(False)

		# GPIO, соотв. разрядам индикации - выходы
		for nixie_digit in range(0, len(nixie_digit_gpios)):
			for bit in nixie_digit_gpios[nixie_digit]:
				GPIO.setup(bit, GPIO.OUT)
				GPIO.output(bit, 0)

	def print_digit (nixie_digit_gpios, digit, value):
		"""
		Записать в разряд digit списка разрядов цифру value
		"""
		for bit in range(0,4):
				# получаем один бит сдвигом и & 
				# и записываем в GPIO
				current_bit = (value >> bit) & 1
				GPIO.output(nixie_digit_gpios[digit][bit], current_bit)

	def effect_shuffle(nixie_digit_gpios, digits):
		"""
		Показываем в выбранных разрядах случайные цифры
		"""
		effect_time = 2 # длительность эффекта
		effect_delay = 0.1 # время демонстрации цифры
		time_elapsed = 0 # счетчик времени эффекта

		iterations = int(effect_time / effect_delay)

		for dummy_counter in range(0, iterations):
			for digit in digits:
				print_digit(nixie_digit_gpios, digit, random.randrange(0,10))
			time.sleep(effect_delay)

	# основная программа
	gpio_init(nixie_digit_gpios)
	effect_displayed = False # флаг показанного эффекта

	while (True):
		
		# получение даты-времени
		now = datetime.now()
		
		# формирование разрядов
		values = [now.minute % 10, now.minute // 10, now.hour % 10, now.hour // 10] 
		
		# каждые 10 минут - эффект shuffle в разрядах минут
		# надо запустить только один раз! Поэтому ставим флаг, а на
		# следующей минуте его сбрасываем

		if ( (values[0] == 0) and not(effect_displayed)):
			effect_shuffle(nixie_digit_gpios, [0,1])
			effect_displayed = True

		if (values[0] == 1):
			effect_displayed = False

		# вывод
		for digit in range(0, 4):
			print_digit(nixie_digit_gpios, digit, values[digit])
		
		# пауза
		time.sleep(1)

finally: 
	# освободить GPIO по завершению программы
	GPIO.cleanup() 
