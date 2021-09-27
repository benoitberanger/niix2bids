import os    # for path management
import json  # json file loading

########################################################################################################################
class File:

    instances = []

    def __init__(self, path: str):
        self.path = path
        self.__class__.instances.append(self)


########################################################################################################################
class Nii(File):

    instances = []


########################################################################################################################
class Json(File):

    instances = []


########################################################################################################################
class Volume:

    instances = []

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, path: str):

        # separate name and extension
        name, ext = os.path.splitext(path)
        if ext != ".nii":
            raise  RuntimeError(f"not a .nii file : {path}")

        # instance filling
        self.nii = Nii(path)
        self.json = Json(name + ".json")
        self.param = dict

        # store a list of all instances
        self.__class__.instances.append(self)

    # ------------------------------------------------------------------------------------------------------------------
    def load_json(self):
        with open(self.json.path, "r") as file:
            self.param = json.load(file)
