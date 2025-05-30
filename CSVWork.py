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

def is_user_exists(filename, search_id):
    with open(filename, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == search_id:
                return True
    return False

def return_user_record(filename, user):
    if not is_user_exists(filename, user): return None
    with open(filename, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == user:
                return row