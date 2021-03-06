import os
import sys
import queue
import random
import threading
import progressbar


from faker import Faker
from change_file import change_int, change_dec, change_char, change_time, change_enum, handle_error


def run_thread(tilt, nb_insert, type_to_change, param, my_queue_lst):
    file_2 = generate_file(tilt, nb_insert, type_to_change, param, "")
    my_queue_lst.put(file_2)


def list_param(type_to_change, tilt):
    param = " ("
    for table in type_to_change:
        if tilt == 1:
            param += "`"
        param += table.name
        param += "`, " if tilt == 1 else ", "
    param = param[:-2] + ") VALUES\n"
    return param


def generate_file(tilt, nb_insert, type_to_change, param, new_file, pbar=None):
    func = {'char': change_char, 'int': change_int, 'dec': change_dec, 'date': change_time,
            'enum': change_enum, 'error': handle_error}
    fake = Faker('fr_FR')
    new_file += "\n\nINSERT INTO "
    new_file += "`" if tilt == 1 else ""
    new_file += param
    new_file += "`" if tilt == 1 else ""
    new_file += list_param(type_to_change, tilt)
    len_text = len(type_to_change)
    for i in range(nb_insert):
        for nu, table in enumerate(type_to_change):
            gender = random.randint(0, 1)
            tmp = func[table.group](nu, len_text, table, fake, gender)
            if table.unique_ok == 1:
                while tmp in table.unique:
                    tmp = func[table.group](nu, len_text, table, fake, gender)
                table.unique[tmp] = 0
            new_file += tmp
            new_file += "," if (nu + 1) < len(type_to_change) else ""
        new_file += "),\n" if i < nb_insert - 1 else ");\n"
        if pbar:
            pbar.update(i + 1)
    return new_file + "\n"


def generate_db(type_to_change, sql_file, nb_insert, create):
    wait = len(type_to_change) if len(type_to_change) > 1 else nb_insert + len(sql_file) + 2
    pbar = progressbar.ProgressBar(maxval=wait)
    pbar.start()
    pbar.update(0)
    new_file = ""
    for l in sql_file:
        new_file += str(l)
    m = create.search(new_file)
    st = new_file[m.start():].split('`', 1)
    tilt = 0
    if len(st) == 2:
        tilt = 1
    if len(type_to_change) > 1:
        my_thread = []
        my_queue_lst = []
        for i, param in enumerate(type_to_change):
            my_queue_lst.append(queue.Queue())
            my_thread.append(
                threading.Thread(run_thread(tilt, nb_insert, type_to_change[param], param, my_queue_lst[i])))
            my_thread[i].start()
            pbar.update(i + 1)
    else:
        for param in type_to_change.keys():
            new_file = generate_file(tilt, nb_insert, type_to_change[param], param, new_file, pbar)
    pbar.update(wait)
    path = os.path.realpath(sys.argv[1])[:-4] + "_generated.sql"
    with open(path, 'wb') as f:
        f.write(bytes(new_file, 'utf-8'))
        if len(type_to_change) > 1:
            for i in range(len(my_thread)):
                f.write(bytes(my_queue_lst[i].get(), 'utf-8'))
        f.close()
    return
