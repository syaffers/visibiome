
import os

def static_file_func(module_file, file_dir, file_dict):
    mydir, myfile = os.path.split(module_file)

    file_dict = dict(((key, os.path.join(os.path.join(mydir, file_dir), value)) for key, value in file_dict.items()))

    for file_name in file_dict.itervalues():
        assert os.path.exists(file_name), "required data file does not exist: %s" % file_name

    def get_file(key):
        if key not in file_dict:
            raise Exception("Unknown static file key '%s'" % key)
        return file_dict[key]


    return get_file

        
