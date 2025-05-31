import csv

def create_record(filename, record):
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(record)

def read_records(filename):
    all_records = []
    with open(filename, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            all_records.append(row)
    return all_records

def update_record(filename, record_id, updated_record):
    rows = []
    with open(filename, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == record_id:
                rows.append(updated_record)
            else:
                rows.append(row)

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

def is_user_exists(filename, search_id, chat_id):
    with open(filename, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[4] == str(search_id) and row[5] == str(chat_id):
                return True
    return False

def return_user_record(filename, user_id, chat_id):
    if not is_user_exists(filename, user_id, chat_id): return None
    with open(filename, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[4] == str(user_id) and row[5] == str(chat_id):
                return row

def sort_records(filename, index):
    all_records = read_records(filename)
    all_records.sort(key=lambda x: int(x[index]), reverse=True)
    return all_records
