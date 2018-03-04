import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import unicodedata
import argparse
import re


MAP_MONTHS = {"sty":"01", "lut":"02", "feb":"02", "mar":"03",
          "kwi":"04", "maj":"05", "cze":"06", "lip":"07",
          "sie":"08", "wrz":"09", "paź":"10", "lis":"11",
          "gru":"12"}


def map_months(text):
    for key, value in MAP_MONTHS.items():
        text = text.replace(key, value)
    return text


def normalize_token(token):
    token = re.sub("[!@#$%^&*\(\)\[\]<><>?:\'\";`.,?]", " ", token)
    token = re.sub(" [ ]+", " ", token)
    return token.strip()


def normalize(tokens):
    tokens = [normalize_token(token.lower()) for token in tokens if token]
    tokens = [token for token in tokens if len(token) > 1]
    return tokens


def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode("UTF-8")


def normalize_date(value):
    if value:
        raw=value
        value = value.split(',')[0]
        value = value.lower().strip()
        value = remove_accents(value)
        value = re.sub("[ /.]", "-", value)
        value = re.sub("([^a-z]|^)([a-z]{3})([a-z]*)([^a-z]|$)", r"\1\2\4", value)
        value = re.sub("[^a-z0-9\-]", "", value)
        value = [val for val in value.split("-")[:3]]
        
        if value[0].isalpha():
            temp = value[0]
            value[0] = value[1]
            value[1] = temp

        value[1] = map_months(value[1])
        value = [int(val) for val in value]

        if len(value) == 2:
            value.append(2018)
        if value[0] > 1000:
            value = value[::-1]
        if value[-1] < 1000:
            value[-1] = 2000 + value[-1]
        return datetime(*value[::-1])
    else:
        return pd.NaT


def read_data_from_tsv(file_path):
    data = []
    quality, clickbait, title = None, None, None
    group_id = -1
    for line in open(file_path).read().split('\n')[1:]:
        if not line.strip():
            continue
        new_quality, new_clickbait, new_title, url, json = line.split('\t')
        if new_quality:
            group_id += 1
            quality = int(new_quality)
            clickbait = int(new_clickbait)
            title = new_title
        json = eval(json)
        json["url"] = url
        json["clickbait_score"] = 5 - clickbait
        json["quality_score"] = quality
        json["group_id"] = group_id
        data.append(json)
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")
    parser.add_argument("output_path")
    args = parser.parse_args()

    data = read_data_from_tsv(args.input_path)
    df = pd.DataFrame(data)

    df = df.fillna("")
    df["tags"] = df["tags"].apply(normalize)
    df["timestamp"] = df["timestamp"].apply(normalize_date)

    with open(args.output_path, "w") as output:
        for value in df.T.to_dict().values():
            output.write("{}\n".format(value))


if __name__ == "__main__":
    main()
