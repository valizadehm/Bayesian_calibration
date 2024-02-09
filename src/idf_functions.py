from abc import abstractmethod
from eppy.modeleditor import IDF

def equal(str1, str2):
    """
    param str1: string str1
    param str2: string str2
    return: check if string a equals string b ignoring character case
    """
    try:
        return str1.upper() == str2.upper()
    except AttributeError:
        return str1 == str2


class UtilityIdf():

    @abstractmethod
    def copy(self, idf):
        """
        parameter idf: idf file of EnergyPlus to be copied
        return: a copy of the idf file of EnergyPlus
        """
        pass


    @abstractmethod
    def idf_handle(self, idf, obj_id, obj_name, field, value):
        """
        handle and modify and *.idf file EnergyPlus in place
        parameter obj_id: object ID being used to identify EnergyPlus object
        parameter obj_name: name of an idf object
        parameter field: field to be modified
        parameter value: value of idf object to be modified
        """
        pass

    @abstractmethod
    def get_output(self):
        """
        return: model output of dtype=float that will be used for the sensivity analysis
        """
        pass



class EppyUtilityIdf(UtilityIdf):

    # Conceret definition of the abstract method copy()
    def copy(self, idf):
        idf_txt = idf.idfstr()
        try:
            idf_copy = IDF(epw=getattr(idf, 'epw'))
        except:
            idf_copy = IDF()
        idf_copy.initreadtxt(idf_txt)
        return idf_copy

    # Conceret definition of the abstract method idf_handle()
    def idf_handle(self, idf, obj_id, obj_name, field, value):
        
        # modification done in place
        obj_list = idf.idfobjects[obj_id.upper()]

        for obj in obj_list:
            if not obj_name:
                obj[field] = value
                break
            elif obj_name == obj.Name:
                obj[field] = value

    # Concret definition of abstract method get_output()
    def get_output(self, html_tables, arg_list):
        if not arg_list:
            return None
        elif len(arg_list) == 1:
            key = arg_list.pop(0)
            for table in html_tables:
                heading = table[0]
                if equal(heading, key):
                    return table[1:]
        else:
            key = arg_list.pop(0)
            for table in html_tables:
                heading = table[0]
                if equal(heading, key):
                    return self.get_output(table[1], arg_list)
        return None