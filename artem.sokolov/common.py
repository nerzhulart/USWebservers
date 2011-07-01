import sys
import subprocess 
import gzip

def safe_open_file(file_to_open, mode='r', buffer_size=-1, error_message='Unexpected Error. Terminated.'):
    try:
        if ".gz" in file_to_open:
            opened_file = gzip.open(file_to_open, mode, buffer_size)
        else:
            opened_file = open(file_to_open, mode, buffer_size)
        return opened_file
    except IOError:
        sys.exit(error_message)

def safe_close_file(object, file_name):
    if hasattr(object, file_name):
        if object.originalReadsFile:
            object.originalReadsFile.close()

def file_lines_count(file_name):
    p = subprocess.Popen(['wc', '-l', file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result, err = p.communicate()
    if p.returncode:
        raise IOError(err)
    return int(result.strip().split()[0]) 
