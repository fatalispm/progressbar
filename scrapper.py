# coding: utf-8

# In[22]:
import csv
import json
import re

import grequests
import requests

MOZILLA = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5'
link = u"http://www.chegg.com/_ajax/federated/search?query={0}&trackid=03ea4a10&strackid=17c8eee9&search_data=%7B%22chgsec%22%3A%22searchsection%22%2C%22chgsubcomp%22%3A%22serp%22%2C%22profile%22%3A%22textbooks-srp%22%2C%22page-number%22%3A{2}%7D&token={1}"

s = requests.Session()


def prepare():
    r1 = s.get("http://www.chegg.com", headers={"user-agent": MOZILLA})
    token = extract_token(r1.text)
    return token


def extract_token(page):
    p = re.compile('C.global.csrfToken = (.*?);')
    m = p.search(page)
    return m.group(1)[1:-1]


def url(r):
    try:
        r = json.loads(r.text)['textbooks']['responseContent']['docs']
        return r[0]['url']
    except:
        pass


def is_out_of_stock(r):
    p2 = re.compile('"stockStatus":"(.*)"')
    return p2.search(r.text).group(1) == 'out of stock'


def rent_price(r):
    try:
        p = re.compile('"rent-textbooks":({.*})')
        res = p.search(r.text).group(0)
        new_pattern = re.compile('"price":"(\d*\.\d*)",')
        return new_pattern.search(res).group(1)
    except:
        return "NaN"


def find_new_price(r):
    try:
        p2 = re.compile('"new":({.*})')
        res = p2.search(r.text).group(0)
        new_pattern = re.compile('"price":"(\d*\.\d*)",')
        return new_pattern.search(res).group(1)
    except:
        return "NaN"


def find_used_price(r):
    try:
        p2 = re.compile('"used":({.*})')
        res = p2.search(r.text).group(0)
        new_pattern = re.compile('"price":"(\d*\.\d*)",')
        return new_pattern.search(res).group(1)
    except:
        return "NaN"


def get_eans(r):
    try:
        js = json.loads(r.text)
        return map(lambda l: l['ean'], js['textbooks']['responseContent']['docs'])
    except:
        pass


def scrape_page(k, token, page_number='1'):
    p = re.compile("\d+")
    if not p.match(k):
        return k, 'NaN', 'NaN', 'NaN'
    r = s.get(link.format(k, token, page_number), headers={"user-agent": MOZILLA})
    url_ = url(r)
    if not url_:
        return k, 'NaN', 'NaN', 'NaN'
    full_link = "http://www.chegg.com" + url(r)
    r2 = s.get(full_link)
    if is_out_of_stock(r2):
        return k, 'Out of stock', 'Out of stock', 'Out of stock'
    return k, rent_price(r2), find_new_price(r2), find_used_price(r2)


def scrape_page_async(ks, token, page_number='1'):
    r = (grequests.get(link.format(k, token, page_number), headers={"user-agent": MOZILLA}, session=s) for k in ks)
    results = grequests.map(r)
    urls = map(url, results)
    urls = map(lambda x: "http://www.chegg.com" + x, urls)
    r = (grequests.get(k, headers={"user-agent": MOZILLA}, session=s) for k in urls)
    pages_with_prices = grequests.map(r)
    result = []
    assert (len(ks) == len(pages_with_prices))
    for k, p in zip(ks, pages_with_prices):
        if p is None:
            result.append((k, 'NaN', 'NaN', 'NaN'))
        else:
            if is_out_of_stock(p):
                result.append((k, 'Out of stock', 'Out of stock', 'Out of stock'))
            else:
                result.append((k, rent_price(p), find_new_price(p), find_used_price(p)))
    return result


def scrape_eans(N, token, filename='1.csv'):
    res = []

    for i in range(1, N):
        r = s.get(link.format('1', token, i), headers={"user-agent": MOZILLA})
        res.extend(get_eans(r))
    f = file(filename, 'w')
    dw = csv.DictWriter(f, fieldnames=['ISBN'])
    headers = dict((n, n) for n in ['ISBN'])
    dw.writerow(headers)
    for i in res:
        dw.writerow({'ISBN': i})
    return res
