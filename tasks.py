import csv
import logging

import redis
from celery import Celery

from scrapper import scrape_page, prepare, scrape_page_async

redis_conn = redis.Redis('localhost', '6379')
celery = Celery("tasks", broker='redis://localhost:6379', backend='redis://localhost:6379')


@celery.task
def scrape(data, filename):
    token = prepare()
    logging.log(20, data)
    logging.log(20, type(data))
    result = []
    data_length = len(data)
    logging.log(20, data_length)
    step = data_length / 25 + 1
    for i, k in enumerate(data):
        if i % step == 0:
            redis_conn.set('status:%s' % filename, i / step * 4)
        result.append(scrape_page(k, token))
    fname = filename + '.csv'
    write_csv(fname, result)
    redis_conn.set('status:%s' % filename, "Finished")
    return fname


N = 7


@celery.task
def scrape_async(data, filename):
    token = prepare()
    data_length = len(data)
    splitted_data = [data[i * N:(i + 1) * N] for i in range(len(data) / N + 1)]
    print data
    result = []
    step = data_length / 25 + 1
    for i, d in enumerate(splitted_data):
        print "OK"
        if i * N % step == 0:
            redis_conn.set('status:%s' % filename, i * 4 * N / step)
        result.extend(scrape_page_async(d, token))
    fname = filename + '.csv'
    write_csv(fname, result)
    redis_conn.set('status:%s' % filename, "Finished")
    return fname


def write_csv(filename, data):
    with open(filename, 'w') as csvfile:
        fieldnames = ['ISBN', 'Rent Price', 'New Price', 'Used Price']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for r in data:
            writer.writerow({'ISBN': r[0],
                             'Rent Price': r[1],
                             'New Price': r[2],
                             'Used Price': r[3]
                             })


if __name__ == "__main__":
    celery.start()
