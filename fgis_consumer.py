import pika
import json
from fgis_worker import FgisWorker
import argparse
from settings import mode_dict
from loggerInit import init_logger
import logging
import os

"""
	Функция устанавливает соединение с очередью и слушает прослушивания сообщений в зависимости от мода 
"""
def run(mode, env): # order, status or download
	
	conn_mode = mode_dict.get(str(mode), None)

	if conn_mode is None:
		try:
			raise Exception("НЕВЕРНОЕ ЗНАЧЕНИЕ MODE: {}".format(str(mode)))
		except Exception as e:
			print(e)

	conn_param = conn_mode.get(str(env), None)

	if conn_param is None:
		try:
			raise Exception("НЕВЕРНОЕ ЗНАЧЕНИЕ QUEUE: {}".format(str(env)))
		except Exception as e:
			print(e)

	# logger init
	init_logger(mode, env)
	logger = logging.getLogger(mode)

	credentials = pika.PlainCredentials(conn_param['user'], conn_param['password'])

	connection = pika.BlockingConnection(pika.ConnectionParameters(host=conn_param['host'], 
		                                                           virtual_host=conn_param['virtual_host'],
		                                                           credentials=credentials))

	channel = connection.channel()

	channel.queue_declare(queue=conn_param['queue'], durable=True)

	logger.info(' [*] Start Consumer | Mode {}'.format(mode))

	# функция колбека полученного сообщения
	def receiver(ch, method, properties, body):
	    logger.info(" [+] Received Message %r" % (body,))
	    fgisWorker = FgisWorker(mode, env) # обьект воркера с указанным модом и конфигом окружения
	    fgisWorker.receive(body) # обработка полученного сообщения
	    ch.basic_ack(delivery_tag = method.delivery_tag)

	channel.basic_qos(prefetch_count=1)
	channel.basic_consume(receiver,
	                      queue=conn_param['queue'])

	channel.start_consuming()

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="RRDoc Ordering Worker")
	parser.add_argument("--mode", 
						"-m", type=str, 
						default='order', 
						help="order-заказ документа, status-проверка статуса, download-загрузка документа")
	parser.add_argument("--env",
						"-e", type=str,
						default='dev', 
						help="конфигурации окружения: dev | kt | prod")

	options = parser.parse_args()
	run(options.mode, options.env)