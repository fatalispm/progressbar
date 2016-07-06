import csv
import os
import time
import uuid
from datetime import datetime
from celery import Celery
from celery.contrib import rdb
import logging
from scrapper import scrape_page


celery = Celery("tasks", broker='redis://localhost:6379', backend='redis://localhost:6379' )


@celery.task
def scrape(data):
    logging.log(20, data)
    logging.log(20, type(data))
    result = []
    for k in data:
        result.append(scrape_page(k))
    filename =str(uuid.uuid4())+'.csv'
    write_csv(filename, result)
    return filename


def write_csv(filename, data):

    with open(filename, 'w') as csvfile:
        fieldnames = ['ISBN', 'New Price', 'Rent Price', 'Used Price']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for r in data:

            writer.writerow({'ISBN': r[0],
                             'New Price': r[1],
                             'Rent Price':r[2],
                             'Used Price':r[3]
                             })


if __name__ == "__main__":
    celery.start()