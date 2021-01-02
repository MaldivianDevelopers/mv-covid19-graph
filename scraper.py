#!/bin/env/python

import requests
from bs4 import BeautifulSoup 
from csv import DictWriter
import re
import json
from shutil import which 
from subprocess import call
import time
from datetime import datetime


def parse_last_update(page):
    try:
        soup = BeautifulSoup(page.text, features="html.parser")
        update_tag = soup.find(lambda tag:tag.name=="div" and tag.text.startswith("Last Updated Date"))
        return update_tag.text
    except Exception as e:
        print("unable to parse last updated")


def parse_edges(page):
    try:
        pattern = re.search(
                r"var edges = new vis\.DataSet\((.*?)\);", 
                page.text,
                re.MULTILINE | re.DOTALL
            )
        return json.loads(pattern.group(1))
    except Exception as e:
        print(e)
        return None

def convert_date(dt):

    if not dt:
        return None
    else:
        datetimeobject = datetime.strptime(dt,'%Y%m%d')
        return datetimeobject.strftime('%d %B %Y')

def parse_nodes(page):
    # soup = BeautifulSoup(page.text, features='html.parser')
    
    nodes = []
    # headers = ["ID", ] + [ x.text for x in soup.select_one(".covid_table_header").find_all("div") ]
    # for row in soup.select(".covid_table_row"):
    #     values = [row.get("data-id")] + [x.text for x in row.find_all("div") ]
    #     nodes.append(dict(zip(headers, values)))

    items = json.loads(page.text)
    
    for key, item in items.items():        

        node = {
            "ID": f"MAV{item['case_id']:05}",
            "Case": f"MAV{item['case_id']:05}",
            "Age": item["age"],
            "Gender": item["gender"],
            "Nationality": item["nationality"],
            "Condition": item["condition"],
            "Transmission": item["infection_source"],
            "Cluster": item["cluster"],
            "Confirmed On": convert_date(item["confirmed_date"]),
            "Recovered On": convert_date(item["recovered_date"]),
            "Discharged On": convert_date(item["discharged_date"]),
            "Deceased On": convert_date(item["deceased_date"]),
        }


        nodes.append(node)

    return nodes


def write_edges(edges):
    if edges:
        with open("edges_official.csv", "w") as f:
            writer = DictWriter(f, ['to', 'from', 'dashes'] )
            writer.writeheader()
            writer.writerows(edges)


def write_nodes(nodes):
    with open("nodes_official.csv", "w") as f:
        writer = DictWriter(f, nodes[0].keys())
        writer.writeheader()
        writer.writerows(nodes)

def fetch_document(url, title, parser):

    # retrieve the document
    print(f"fetching {url}")
    doc = requests.get(
           url, 
           headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
            }
        )

    if doc.status_code == 200:                  # note: requests doesn't necessary mean HTTP200 here
        updated_on = parse_last_update(doc)
        print(f"Fetched {title}: {updated_on}")
        return parser(doc)
    else:
        print(f"Error: Failed to fetch {title}") 
        return None


if __name__ == "__main__":
    
        
    # process nodes
    nodes = fetch_document(f"https://covid19.health.gov.mv/cases.json?t={int(time.time())}", "Nodes", parse_nodes)
    print(f"Writing {len(nodes)} Nodes to file")
    if nodes:
        write_nodes(nodes)

    # process edges
    # edges = fetch_document("https://covid19.health.gov.mv/dashboard/network/", "Edges", parse_edges)
    # if edges:
    #     print(f"Writing {len(edges)} Edges to file")
    #     write_edges(edges)

    # print git diff
    print("\n")   # sugar
    if which("git"):
        call([
            "git",
            "diff",
            "--stat",
            "nodes_official.csv",
            "edges_official.csv"
        ])

    else:
        print("Error: Response returned unsuccessful")